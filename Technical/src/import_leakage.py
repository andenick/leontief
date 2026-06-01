"""Import leakage multiplier analysis.

Measures how much of each stimulus dollar leaks abroad through
intermediate import channels. High-leakage sectors are poor targets
for domestic fiscal stimulus.

Reference: Miller & Blair Ch. 3; Hummels et al. (2001).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def domestic_retention_rate(
    A_domestic: pd.DataFrame,
    A_import: pd.DataFrame,
    f: pd.Series,
) -> pd.Series:
    """Compute domestic retention rate per unit of final demand.

    DRR_j = (L_d * e_j).sum() / (L_total * e_j).sum()
    where L_d = (I - A_d)^(-1), L_total = (I - A_d - A_m)^(-1)

    Args:
        A_domestic: Domestic direct requirements matrix.
        A_import: Import direct requirements matrix.
        f: Final demand vector.

    Returns:
        Series of retention rates in [0, 1] by sector.
    """
    common = A_domestic.index.intersection(A_import.index).intersection(f.index)
    A_d = A_domestic.loc[common, common].values
    A_m = A_import.loc[common, common].values
    n = len(common)

    L_d = linalg.inv(np.eye(n) - A_d)
    A_total = A_d + A_m
    col_sums = A_total.sum(axis=0)
    if np.any(col_sums >= 1):
        scale = np.where(col_sums >= 0.99, 0.98 / col_sums, 1.0)
        A_total *= scale[np.newaxis, :]

    L_total = linalg.inv(np.eye(n) - A_total)

    f_vals = f.reindex(common).fillna(0).values

    drr = np.zeros(n)
    for j in range(n):
        e_j = np.zeros(n)
        e_j[j] = 1.0
        domestic_effect = (L_d @ e_j).sum()
        total_effect = (L_total @ e_j).sum()
        drr[j] = domestic_effect / max(total_effect, 1e-10)

    result = pd.Series(drr, index=common, name="domestic_retention_rate")
    return result.clip(0, 1)


def import_leakage_multiplier(
    A_domestic: pd.DataFrame,
    A_import: pd.DataFrame,
) -> pd.DataFrame:
    """Compute import leakage as gap between total and domestic multipliers.

    Args:
        A_domestic: Domestic direct requirements matrix.
        A_import: Import direct requirements matrix.

    Returns:
        DataFrame with standard_multiplier, domestic_multiplier,
        leakage_fraction per sector.
    """
    common = A_domestic.index.intersection(A_import.index)
    A_d = A_domestic.loc[common, common].values
    A_m = A_import.loc[common, common].values
    n = len(common)

    L_d = linalg.inv(np.eye(n) - A_d)
    domestic_mult = L_d.sum(axis=0)

    A_total = A_d + A_m
    col_sums = A_total.sum(axis=0)
    if np.any(col_sums >= 1):
        scale = np.where(col_sums >= 0.99, 0.98 / col_sums, 1.0)
        A_total *= scale[np.newaxis, :]

    L_total = linalg.inv(np.eye(n) - A_total)
    total_mult = L_total.sum(axis=0)

    leakage = (total_mult - domestic_mult) / np.where(total_mult > 0, total_mult, 1)

    return pd.DataFrame({
        "standard_multiplier": total_mult,
        "domestic_multiplier": domestic_mult,
        "leakage_fraction": leakage,
        "import_intensity": A_m.sum(axis=0),
    }, index=common).sort_values("leakage_fraction", ascending=False)


def leakage_by_fd_category(
    use_table: pd.DataFrame,
    total_output: pd.Series,
    final_demand: pd.DataFrame,
    gov_col_codes: List[str] = None,
) -> pd.DataFrame:
    """Compute import leakage for each government FD category.

    Args:
        use_table: Full Use table.
        total_output: Total output by sector.
        final_demand: FD DataFrame with government columns.
        gov_col_codes: Government column codes.

    Returns:
        DataFrame with fd_category, domestic_multiplier, import_leakage.
    """
    from import_analysis import split_use_table

    if gov_col_codes is None:
        gov_col_codes = ["F06C00", "F06N00", "F07C00"]

    Z_dom, Z_imp = split_use_table(use_table)
    sectors = Z_dom.index.intersection(Z_dom.columns)

    x = total_output.reindex(sectors).replace(0, np.nan)
    A_d = Z_dom.loc[sectors, sectors].div(x, axis=1).fillna(0)
    A_m = Z_imp.loc[sectors, sectors].div(x, axis=1).fillna(0)

    n = len(sectors)
    L_d = linalg.inv(np.eye(n) - A_d.values)

    gov_labels = {"F06C00": "Federal Defense", "F06N00": "Federal Nondefense", "F07C00": "State & Local"}
    rows = []

    for code in gov_col_codes:
        cols = [c for c in final_demand.columns if str(c).startswith(code[:3])]
        if not cols:
            continue

        f_gov = final_demand[cols].sum(axis=1).reindex(sectors).fillna(0).values
        f_total = f_gov.sum()
        if f_total <= 0:
            continue

        domestic_output = (L_d @ f_gov).sum()
        domestic_mult = domestic_output / f_total

        rows.append({
            "fd_category": gov_labels.get(code, code),
            "total_spending": float(f_total),
            "domestic_output": float(domestic_output),
            "domestic_multiplier": float(domestic_mult),
            "import_leakage": float(1.0 - domestic_output / max(domestic_output + f_total * 0.1, 1e-10)),
        })

    return pd.DataFrame(rows)
