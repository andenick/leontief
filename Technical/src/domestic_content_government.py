"""Domestic content analysis for government procurement.

Applies DVA methodology to each government final demand column to measure
how much of public spending stays in the domestic economy.

Reference: Hummels et al. (2001); Johnson & Noguera (2012).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

DEFAULT_GOV_COLS = ["F06C00", "F06N00", "F07C00"]
GOV_LABELS = {
    "F06C00": "Federal Defense",
    "F06N00": "Federal Nondefense",
    "F07C00": "State & Local",
}


def _find_gov_columns(fd: pd.DataFrame, gov_codes: List[str]) -> List[str]:
    """Find government FD columns by prefix matching."""
    found = []
    for code in gov_codes:
        exact = [c for c in fd.columns if str(c) == code]
        if exact:
            found.extend(exact)
        else:
            prefix = [c for c in fd.columns if str(c).startswith(code[:3])]
            found.extend(prefix)
    return found


def dva_in_government_procurement(
    use_table: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    final_demand: pd.DataFrame,
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Compute domestic value added content for each government FD column.

    Args:
        use_table: Full Use table.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        final_demand: FD DataFrame with government columns.
        gov_col_codes: Government FD column codes.

    Returns:
        DataFrame with gov_category, dva_total, dva_share, import_content.
    """
    from import_analysis import split_use_table

    if gov_col_codes is None:
        gov_col_codes = DEFAULT_GOV_COLS

    Z_dom, Z_imp = split_use_table(use_table)

    sectors = Z_dom.index.intersection(Z_dom.columns)
    A_dom = Z_dom.loc[sectors, sectors].div(
        total_output.reindex(sectors).replace(0, np.nan), axis=1
    ).fillna(0)

    n = len(sectors)
    L_dom = linalg.inv(np.eye(n) - A_dom.values)

    if isinstance(value_added, pd.DataFrame):
        va_total = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va_total = value_added.reindex(sectors).fillna(0)

    x = total_output.reindex(sectors).fillna(0)
    va_coeff = (va_total / x.replace(0, np.nan)).fillna(0).values

    gov_cols = _find_gov_columns(final_demand, gov_col_codes)
    rows = []

    for col in gov_cols:
        f_gov = final_demand[col].reindex(sectors).fillna(0).values
        f_total = f_gov.sum()
        if f_total <= 0:
            continue

        dva = va_coeff @ L_dom @ f_gov
        label = GOV_LABELS.get(str(col), str(col))

        rows.append({
            "gov_category": label,
            "col_code": str(col),
            "total_spending": float(f_total),
            "dva_total": float(dva),
            "dva_share": float(dva / f_total),
            "import_content": float(f_total - dva),
            "import_share": float(1.0 - dva / f_total),
        })

    logger.info(f"Government DVA: {len(rows)} categories analyzed")
    return pd.DataFrame(rows)


def dva_sector_decomposition(
    use_table: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    gov_fd_col: pd.Series,
) -> pd.DataFrame:
    """Decompose DVA in government procurement by originating sector.

    Args:
        use_table: Full Use table.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        gov_fd_col: Government FD vector for one category.

    Returns:
        DataFrame with sector, dva_contribution, dva_share, sorted descending.
    """
    from import_analysis import split_use_table

    Z_dom, _ = split_use_table(use_table)
    sectors = Z_dom.index.intersection(Z_dom.columns)

    A_dom = Z_dom.loc[sectors, sectors].div(
        total_output.reindex(sectors).replace(0, np.nan), axis=1
    ).fillna(0)

    n = len(sectors)
    L_dom = linalg.inv(np.eye(n) - A_dom.values)

    if isinstance(value_added, pd.DataFrame):
        va_total = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va_total = value_added.reindex(sectors).fillna(0)

    x = total_output.reindex(sectors).fillna(0)
    va_coeff = (va_total / x.replace(0, np.nan)).fillna(0).values

    f = gov_fd_col.reindex(sectors).fillna(0).values

    # DVA contribution by sector: va_coeff_i * L_row_i * f
    output_triggered = L_dom @ f
    dva_by_sector = va_coeff * output_triggered

    total_dva = dva_by_sector.sum()
    result = pd.DataFrame({
        "dva_contribution": dva_by_sector,
        "dva_share": dva_by_sector / max(total_dva, 1e-10),
        "output_triggered": output_triggered,
    }, index=sectors)

    return result.sort_values("dva_contribution", ascending=False)


def dva_government_timeseries(
    data_by_year: Dict[int, dict],
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Track domestic content of government procurement over time.

    Args:
        data_by_year: Dict of year -> data dict.
        gov_col_codes: Government column codes.

    Returns:
        DataFrame with year, category, dva_share.
    """
    if gov_col_codes is None:
        gov_col_codes = DEFAULT_GOV_COLS

    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        use = d.get("use_table")
        va = d.get("value_added")
        x = d.get("total_output")
        fd = d.get("final_demand")

        if use is None or va is None or x is None or fd is None:
            continue
        if isinstance(fd, pd.Series):
            continue

        try:
            result = dva_in_government_procurement(use, va, x, fd, gov_col_codes)
            for _, row in result.iterrows():
                rows.append({
                    "year": year,
                    "gov_category": row["gov_category"],
                    "dva_share": row["dva_share"],
                    "total_spending": row["total_spending"],
                })
        except Exception:
            continue

    return pd.DataFrame(rows)
