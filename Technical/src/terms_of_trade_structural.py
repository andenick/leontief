"""Terms of trade structural change decomposition.

Decomposes sectoral terms-of-trade changes into technology-driven
(A matrix changes) vs. distribution-driven (VA share changes).

Reference: Miller & Blair Ch. 3; Dutt (1990).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def sectoral_terms_of_trade(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
) -> pd.Series:
    """Compute implicit terms-of-trade index for each sector.

    ToT_j = p_j / p_mean where p = v' * L (cost-push prices).

    Args:
        A: Direct requirements matrix.
        value_added: VA DataFrame.
        total_output: Total output by sector.

    Returns:
        Series of ToT indices normalized to mean = 1.
    """
    sectors = A.index
    n = len(sectors)

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va = value_added.reindex(sectors).fillna(0)

    x = total_output.reindex(sectors).fillna(0)
    va_coeff = (va / x.replace(0, np.nan)).fillna(0).values

    L = linalg.inv(np.eye(n) - A.values)
    prices = va_coeff @ L

    mean_price = prices.mean()
    tot = prices / max(mean_price, 1e-10)

    return pd.Series(tot, index=sectors, name="terms_of_trade")


def tot_structural_decomposition(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    va_0: pd.DataFrame,
    va_1: pd.DataFrame,
    x_0: pd.Series,
    x_1: pd.Series,
) -> pd.DataFrame:
    """Decompose ToT change into technology vs. distribution components.

    p = v' * L
    delta_p = delta_v' * L_1 + v_0' * delta_L  (polar average)
    Technology: v_0' * delta_L (from A change)
    Distribution: delta_v' * L_1 (from VA share change)

    Args:
        A_0/1: Direct requirements matrices.
        va_0/1: VA DataFrames.
        x_0/1: Total output vectors.

    Returns:
        DataFrame with tot_change, tech_component, distrib_component per sector.
    """
    common = A_0.index.intersection(A_1.index)
    n = len(common)

    A0 = A_0.loc[common, common].values
    A1 = A_1.loc[common, common].values

    if isinstance(va_0, pd.DataFrame):
        v0 = va_0.sum(axis=0).reindex(common).fillna(0).values
    else:
        v0 = va_0.reindex(common).fillna(0).values

    if isinstance(va_1, pd.DataFrame):
        v1 = va_1.sum(axis=0).reindex(common).fillna(0).values
    else:
        v1 = va_1.reindex(common).fillna(0).values

    xv0 = x_0.reindex(common).fillna(0).values
    xv1 = x_1.reindex(common).fillna(0).values

    vc0 = v0 / np.where(xv0 > 0, xv0, np.nan)
    vc1 = v1 / np.where(xv1 > 0, xv1, np.nan)
    vc0 = np.nan_to_num(vc0)
    vc1 = np.nan_to_num(vc1)

    L0 = linalg.inv(np.eye(n) - A0)
    L1 = linalg.inv(np.eye(n) - A1)

    p0 = vc0 @ L0
    p1 = vc1 @ L1

    # Polar decomposition
    tech_1 = vc0 @ (L1 - L0)
    dist_1 = (vc1 - vc0) @ L1

    tech_2 = vc1 @ (L1 - L0)
    dist_2 = (vc1 - vc0) @ L0

    tech = 0.5 * (tech_1 + tech_2)
    dist = 0.5 * (dist_1 + dist_2)
    total = p1 - p0

    p0_safe = np.where(np.abs(p0) > 1e-10, p0, np.nan)

    return pd.DataFrame({
        "price_0": p0,
        "price_1": p1,
        "tot_change": total,
        "tot_change_pct": np.nan_to_num(total / p0_safe * 100),
        "technology_component": tech,
        "distribution_component": dist,
        "tech_share": np.nan_to_num(tech / np.where(np.abs(total) > 1e-10, total, np.nan)),
    }, index=common).fillna(0)


def tot_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Track aggregate terms-of-trade metrics across years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year, tot_dispersion, tech_share_mean.
    """
    years = sorted(data_by_year.keys())
    rows = []

    for i in range(1, len(years)):
        y0, y1 = years[i - 1], years[i]
        d0, d1 = data_by_year[y0], data_by_year[y1]

        A0, A1 = d0.get("A_matrix"), d1.get("A_matrix")
        va0, va1 = d0.get("value_added"), d1.get("value_added")
        x0, x1 = d0.get("total_output"), d1.get("total_output")

        if any(v is None for v in [A0, A1, va0, va1, x0, x1]):
            continue

        try:
            decomp = tot_structural_decomposition(A0, A1, va0, va1, x0, x1)
            rows.append({
                "year": y1,
                "mean_tot_change_pct": float(decomp["tot_change_pct"].mean()),
                "tech_share_mean": float(decomp["tech_share"].mean()),
                "tot_dispersion": float(decomp["tot_change"].std()),
            })
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year")
