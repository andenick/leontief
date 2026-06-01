"""Miyazawa interrelational multiplier decomposition.

Partitions output into autonomous (final demand driven) and induced
(household income recycling) components using Miyazawa's extended
Leontief framework.

Reference: Miyazawa (1976); Miller & Blair Ch. 6.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def miyazawa_partition(
    A: pd.DataFrame,
    use_table: pd.DataFrame,
    value_added: pd.DataFrame,
    final_demand: pd.DataFrame,
    total_output: pd.Series,
) -> Dict:
    """Compute the Miyazawa multiplier decomposition.

    M = L * (I + K * B_hh * L)
    where K = household consumption pattern (how wages are spent)
          B_hh = household income coefficient (wages / output)

    Args:
        A: Direct requirements matrix.
        use_table: Full Use table.
        value_added: VA DataFrame.
        final_demand: FD DataFrame.
        total_output: Total output by sector.

    Returns:
        Dict with L (standard), M (Miyazawa), K_vector, B_vector,
        induced_output_share.
    """
    sectors = A.index
    n = len(sectors)

    L = linalg.inv(np.eye(n) - A.values)

    # B_hh: household income coefficient = compensation / output
    if isinstance(value_added, pd.DataFrame):
        comp_rows = [r for r in value_added.index if "V001" in str(r) or "comp" in str(r).lower()]
        if comp_rows:
            wages = value_added.loc[comp_rows[0]].reindex(sectors).fillna(0)
        else:
            wages = value_added.iloc[0].reindex(sectors).fillna(0)
    else:
        wages = value_added.reindex(sectors).fillna(0)

    x = total_output.reindex(sectors).fillna(0)
    B_hh = (wages / x.replace(0, np.nan)).fillna(0).values

    # K: household consumption pattern (how a dollar of wage income is spent)
    pce_cols = [c for c in final_demand.columns if str(c).startswith("F01") or "F010" in str(c)]
    if pce_cols:
        pce = final_demand[pce_cols].sum(axis=1).reindex(sectors).fillna(0)
    else:
        pce = final_demand.sum(axis=1).reindex(sectors).fillna(0)

    pce_total = pce.sum()
    K = (pce / max(pce_total, 1e-10)).values

    # Miyazawa multiplier: M = L * (I + K * B_hh' * L / (1 - B_hh' * L * K))
    # Simplified: propagation matrix P = K (outer) B_hh
    P = np.outer(K, B_hh)

    # M = (I - A - P)^{-1}  (augmented system)
    A_augmented = A.values + P
    col_sums = A_augmented.sum(axis=0)
    if np.any(col_sums >= 1):
        scale = np.where(col_sums >= 0.99, 0.98 / col_sums, 1.0)
        A_augmented *= scale[np.newaxis, :]

    M = linalg.inv(np.eye(n) - A_augmented)

    # Induced share: (M - L) * f / (M * f)
    if isinstance(final_demand, pd.DataFrame):
        f = final_demand.sum(axis=1).reindex(sectors).fillna(0).values
    else:
        f = final_demand.reindex(sectors).fillna(0).values

    total_output_m = (M @ f).sum()
    autonomous_output = (L @ f).sum()
    induced_output = total_output_m - autonomous_output
    induced_share = induced_output / max(total_output_m, 1e-10)

    logger.info(f"Miyazawa: induced share = {induced_share:.1%}")

    return {
        "L": pd.DataFrame(L, index=sectors, columns=sectors),
        "M": pd.DataFrame(M, index=sectors, columns=sectors),
        "K_vector": pd.Series(K, index=sectors, name="consumption_pattern"),
        "B_vector": pd.Series(B_hh, index=sectors, name="income_coefficient"),
        "induced_output_share": float(induced_share),
        "autonomous_output": float(autonomous_output),
        "induced_output": float(induced_output),
    }


def autonomous_vs_induced_output(
    M: pd.DataFrame,
    L: pd.DataFrame,
    final_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Decompose sectoral output into autonomous and induced components.

    Args:
        M: Miyazawa multiplier matrix.
        L: Standard Leontief inverse.
        final_demand: FD DataFrame or Series.

    Returns:
        DataFrame with autonomous_output, induced_output, induced_share per sector.
    """
    sectors = L.index
    if isinstance(final_demand, pd.DataFrame):
        f = final_demand.sum(axis=1).reindex(sectors).fillna(0).values
    else:
        f = final_demand.reindex(sectors).fillna(0).values

    x_autonomous = L.values @ f
    x_total = M.values @ f
    x_induced = x_total - x_autonomous

    return pd.DataFrame({
        "autonomous_output": x_autonomous,
        "induced_output": x_induced,
        "total_output": x_total,
        "induced_share": x_induced / np.where(x_total > 0, x_total, np.nan),
    }, index=sectors).fillna(0).sort_values("induced_share", ascending=False)


def miyazawa_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Track induced share of total output across years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year, induced_share, autonomous_output, induced_output.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        use = d.get("use_table")
        va = d.get("value_added")
        fd = d.get("final_demand")
        x = d.get("total_output")

        if A is None or use is None or va is None or fd is None or x is None:
            continue
        if isinstance(fd, pd.Series):
            continue

        try:
            result = miyazawa_partition(A, use, va, fd, x)
            rows.append({
                "year": year,
                "induced_share": result["induced_output_share"],
                "autonomous_output": result["autonomous_output"],
                "induced_output": result["induced_output"],
            })
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year")
