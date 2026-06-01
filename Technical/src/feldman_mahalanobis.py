"""Feldman-Mahalanobis two-sector growth model via I-O tables.

Partitions the economy into Department I (capital/investment goods)
and Department II (consumption goods) using final demand composition.

Reference: Feldman (1928); Mahalanobis (1953); Dobb (1960).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def classify_departments(
    final_demand: pd.DataFrame,
    investment_col_prefixes: List[str] = None,
    consumption_col_prefixes: List[str] = None,
) -> pd.Series:
    """Classify sectors into Dept I (capital) or Dept II (consumption).

    A sector belongs to Dept I if its sales to investment FD exceed
    its sales to consumption FD; otherwise Dept II.

    Args:
        final_demand: FD DataFrame with typed columns.
        investment_col_prefixes: Prefixes for investment columns (default F03).
        consumption_col_prefixes: Prefixes for consumption columns (default F01).

    Returns:
        Series with values "I" or "II" indexed by sector.
    """
    if investment_col_prefixes is None:
        investment_col_prefixes = ["F03"]
    if consumption_col_prefixes is None:
        consumption_col_prefixes = ["F01"]

    inv_cols = [c for c in final_demand.columns
                if any(str(c).startswith(p) for p in investment_col_prefixes)]
    con_cols = [c for c in final_demand.columns
                if any(str(c).startswith(p) for p in consumption_col_prefixes)]

    inv_share = final_demand[inv_cols].sum(axis=1) if inv_cols else pd.Series(0, index=final_demand.index)
    con_share = final_demand[con_cols].sum(axis=1) if con_cols else pd.Series(0, index=final_demand.index)

    dept = pd.Series("II", index=final_demand.index, name="department")
    dept[inv_share > con_share] = "I"

    n_I = (dept == "I").sum()
    n_II = (dept == "II").sum()
    logger.info(f"Department classification: {n_I} Dept I, {n_II} Dept II")
    return dept


def feldman_investment_ratio(
    A: pd.DataFrame,
    final_demand: pd.DataFrame,
    dept_assignment: pd.Series,
    total_output: pd.Series = None,
) -> Dict[str, float]:
    """Compute Feldman's alpha = share of Dept I output reinvested in Dept I.

    Args:
        A: Direct requirements matrix.
        final_demand: FD DataFrame.
        dept_assignment: Series with "I" or "II" values.
        total_output: Total output (optional, for weighting).

    Returns:
        Dict with alpha, dept_I_output, dept_II_output, dept_I_share.
    """
    sectors = A.index
    dept = dept_assignment.reindex(sectors).fillna("II")

    dept_I = [s for s in sectors if dept[s] == "I"]
    dept_II = [s for s in sectors if dept[s] == "II"]

    n = len(sectors)
    L = linalg.inv(np.eye(n) - A.values)

    if isinstance(final_demand, pd.DataFrame):
        f = final_demand.sum(axis=1).reindex(sectors).fillna(0).values
    else:
        f = final_demand.reindex(sectors).fillna(0).values

    output = L @ f

    dept_I_idx = [sectors.get_loc(s) for s in dept_I if s in sectors]
    dept_II_idx = [sectors.get_loc(s) for s in dept_II if s in sectors]

    dept_I_output = output[dept_I_idx].sum() if dept_I_idx else 0
    dept_II_output = output[dept_II_idx].sum() if dept_II_idx else 0
    total = dept_I_output + dept_II_output

    # Alpha: fraction of Dept I inputs that come from Dept I itself
    A_vals = A.values
    if dept_I_idx:
        I_to_I = sum(A_vals[i, j] for i in dept_I_idx for j in dept_I_idx)
        I_total = sum(A_vals[i, j] for i in range(n) for j in dept_I_idx)
        alpha = I_to_I / max(I_total, 1e-10)
    else:
        alpha = 0

    return {
        "alpha": float(alpha),
        "dept_I_output": float(dept_I_output),
        "dept_II_output": float(dept_II_output),
        "dept_I_share": float(dept_I_output / max(total, 1e-10)),
        "n_dept_I_sectors": len(dept_I),
        "n_dept_II_sectors": len(dept_II),
        "growth_ceiling_proxy": float(alpha * dept_I_output / max(total, 1e-10)),
    }


def feldman_growth_dynamics(
    data_by_year: Dict[int, dict],
    dept_assignment: pd.Series,
) -> pd.DataFrame:
    """Trace alpha and growth dynamics 1997-2024.

    Args:
        data_by_year: Dict of year -> data dict.
        dept_assignment: Department classification.

    Returns:
        DataFrame with year, alpha, dept_I_share, growth_ceiling.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        fd = d.get("final_demand")
        x = d.get("total_output")
        if A is None or fd is None:
            continue
        if isinstance(fd, pd.Series):
            continue

        try:
            result = feldman_investment_ratio(A, fd, dept_assignment, x)
            result["year"] = year
            rows.append(result)
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year")
