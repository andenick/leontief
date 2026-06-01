"""Fiscal multiplier analysis by government spending category.

Computes output and employment multipliers for each type of government
spending (defense, nondefense, state/local) and ranks by jobs-per-dollar.

Reference: Ramey (2011); Auerbach & Gorodnichenko (2012).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

GOV_LABELS = {
    "F06C00": "Federal Defense",
    "F06N00": "Federal Nondefense",
    "F07C00": "State & Local",
}


def government_fd_columns(
    final_demand: pd.DataFrame,
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Extract government FD columns from the final demand DataFrame.

    Args:
        final_demand: Full FD DataFrame.
        gov_col_codes: Column codes to extract.

    Returns:
        DataFrame with only government columns found.
    """
    if gov_col_codes is None:
        gov_col_codes = list(GOV_LABELS.keys())

    found = []
    for code in gov_col_codes:
        matches = [c for c in final_demand.columns if str(c).startswith(code[:4])]
        found.extend(matches)

    if not found:
        found = [c for c in final_demand.columns if str(c).startswith("F06") or str(c).startswith("F07")]

    return final_demand[found] if found else pd.DataFrame()


def output_multiplier_by_fd_category(
    L: pd.DataFrame,
    fd_col: pd.Series,
) -> Dict[str, float]:
    """Compute output multiplier for a specific FD category.

    Uses the composition-weighted multiplier: total output generated
    per dollar of this FD category, weighted by the spending pattern.

    Args:
        L: Leontief inverse matrix.
        fd_col: FD vector for one spending category.

    Returns:
        Dict with multiplier, total_output_impact, spending_total.
    """
    sectors = L.index
    f = fd_col.reindex(sectors).fillna(0).values
    f_total = f.sum()

    if f_total <= 0:
        return {"multiplier": 0, "total_output_impact": 0, "spending_total": 0}

    f_unit = f / f_total
    output_impact = L.values @ f_unit

    return {
        "multiplier": float(output_impact.sum()),
        "total_output_impact": float((L.values @ f).sum()),
        "spending_total": float(f_total),
    }


def employment_multiplier_by_fd_category(
    L: pd.DataFrame,
    fd_col: pd.Series,
    compensation_coeff: pd.Series,
) -> Dict[str, float]:
    """Compute employment multiplier for a specific FD category.

    Jobs-per-dollar = compensation' * L * f_unit

    Args:
        L: Leontief inverse.
        fd_col: FD vector for one spending category.
        compensation_coeff: Compensation per unit output by sector.

    Returns:
        Dict with employment_multiplier, compensation_per_dollar.
    """
    sectors = L.index
    f = fd_col.reindex(sectors).fillna(0).values
    f_total = f.sum()
    comp = compensation_coeff.reindex(sectors).fillna(0).values

    if f_total <= 0:
        return {"employment_multiplier": 0, "compensation_per_dollar": 0}

    f_unit = f / f_total
    comp_impact = comp @ L.values @ f_unit

    return {
        "employment_multiplier": float(comp_impact),
        "compensation_per_dollar": float(comp_impact),
    }


def fiscal_multiplier_table(
    A: pd.DataFrame,
    L: pd.DataFrame,
    final_demand: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Full fiscal multiplier table across all government spending categories.

    Args:
        A: Direct requirements matrix.
        L: Leontief inverse.
        final_demand: FD DataFrame.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        gov_col_codes: Government column codes.

    Returns:
        DataFrame indexed by FD category with output and employment multipliers.
    """
    if gov_col_codes is None:
        gov_col_codes = list(GOV_LABELS.keys())

    sectors = A.index
    x = total_output.reindex(sectors).fillna(0)

    if isinstance(value_added, pd.DataFrame):
        comp_rows = [r for r in value_added.index if "V001" in str(r)]
        if comp_rows:
            comp = value_added.loc[comp_rows[0]].reindex(sectors).fillna(0)
        else:
            comp = value_added.iloc[0].reindex(sectors).fillna(0)
    else:
        comp = value_added.reindex(sectors).fillna(0)

    comp_coeff = (comp / x.replace(0, np.nan)).fillna(0)

    gov_fd = government_fd_columns(final_demand, gov_col_codes)
    rows = []

    for col in gov_fd.columns:
        fd_col = gov_fd[col]
        out_mult = output_multiplier_by_fd_category(L, fd_col)
        emp_mult = employment_multiplier_by_fd_category(L, fd_col, comp_coeff)

        # Find top sector beneficiary
        f = fd_col.reindex(sectors).fillna(0).values
        output_by_sector = L.values @ f
        top_sector_idx = np.argmax(output_by_sector)
        top_sector = sectors[top_sector_idx]

        label = GOV_LABELS.get(str(col), str(col))
        rows.append({
            "fd_category": label,
            "col_code": str(col),
            "output_multiplier": out_mult["multiplier"],
            "employment_multiplier": emp_mult["employment_multiplier"],
            "total_spending": out_mult["spending_total"],
            "total_output_impact": out_mult["total_output_impact"],
            "top_beneficiary_sector": top_sector,
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("output_multiplier", ascending=False)
    return result


def fiscal_multiplier_timeseries(
    data_by_year: Dict[int, dict],
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Track fiscal multipliers across years.

    Args:
        data_by_year: Dict of year -> data dict.
        gov_col_codes: Government column codes.

    Returns:
        DataFrame with year, category, output_multiplier.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        L = d.get("L_matrix")
        fd = d.get("final_demand")
        va = d.get("value_added")
        x = d.get("total_output")

        if A is None or L is None or fd is None or va is None or x is None:
            continue
        if isinstance(fd, pd.Series):
            continue

        try:
            table = fiscal_multiplier_table(A, L, fd, va, x, gov_col_codes)
            for _, row in table.iterrows():
                rows.append({
                    "year": year,
                    "fd_category": row["fd_category"],
                    "output_multiplier": row["output_multiplier"],
                })
        except Exception:
            continue

    return pd.DataFrame(rows)
