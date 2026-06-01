"""Functional income distribution counterfactual analysis.

Simulates: if sector X had maintained its 1997 wage share, what would
prices look like today? Isolates distributional vs. technology effects.

Reference: Kalecki (1954); Shaikh (2016) Ch. 9.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def counterfactual_wage_share(
    value_added_actual: pd.DataFrame,
    value_added_anchor: pd.DataFrame,
    total_output_actual: pd.Series,
    total_output_anchor: pd.Series,
    counterfactual_sector: str,
    sectors: pd.Index,
) -> pd.Series:
    """Construct counterfactual VA coefficients holding one sector at anchor wage share.

    Args:
        value_added_actual: Current VA DataFrame.
        value_added_anchor: Anchor-year VA DataFrame (e.g., 1997).
        total_output_actual: Current total output.
        total_output_anchor: Anchor total output.
        counterfactual_sector: Sector to hold at anchor wage share.
        sectors: Sector index for alignment.

    Returns:
        Counterfactual VA coefficient vector.
    """
    if isinstance(value_added_actual, pd.DataFrame):
        va_actual = value_added_actual.sum(axis=0).reindex(sectors).fillna(0)
        comp_rows = [r for r in value_added_actual.index if "V001" in str(r)]
        if comp_rows:
            wages_actual = value_added_actual.loc[comp_rows[0]].reindex(sectors).fillna(0)
        else:
            wages_actual = va_actual * 0.5
    else:
        va_actual = value_added_actual.reindex(sectors).fillna(0)
        wages_actual = va_actual * 0.5

    if isinstance(value_added_anchor, pd.DataFrame):
        va_anchor = value_added_anchor.sum(axis=0).reindex(sectors).fillna(0)
        comp_rows = [r for r in value_added_anchor.index if "V001" in str(r)]
        if comp_rows:
            wages_anchor = value_added_anchor.loc[comp_rows[0]].reindex(sectors).fillna(0)
        else:
            wages_anchor = va_anchor * 0.5
    else:
        va_anchor = value_added_anchor.reindex(sectors).fillna(0)
        wages_anchor = va_anchor * 0.5

    x_actual = total_output_actual.reindex(sectors).fillna(0)
    x_anchor = total_output_anchor.reindex(sectors).fillna(0)

    va_coeff = (va_actual / x_actual.replace(0, np.nan)).fillna(0)

    if counterfactual_sector in sectors:
        anchor_ws = wages_anchor.get(counterfactual_sector, 0) / max(
            x_anchor.get(counterfactual_sector, 1), 1e-10
        )
        actual_ws = wages_actual.get(counterfactual_sector, 0) / max(
            x_actual.get(counterfactual_sector, 1), 1e-10
        )
        adjustment = anchor_ws - actual_ws
        va_coeff_cf = va_coeff.copy()
        va_coeff_cf[counterfactual_sector] += adjustment
    else:
        va_coeff_cf = va_coeff.copy()

    return va_coeff_cf


def price_impact_of_wage_counterfactual(
    A: pd.DataFrame,
    va_coeff_actual: pd.Series,
    va_coeff_counterfactual: pd.Series,
) -> pd.DataFrame:
    """Compute price impact of restoring a sector's wage share.

    Args:
        A: Direct requirements matrix.
        va_coeff_actual: Actual VA coefficients.
        va_coeff_counterfactual: Counterfactual VA coefficients.

    Returns:
        DataFrame with actual_price, counterfactual_price, deviation_pct.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)

    p_actual = va_coeff_actual.reindex(A.index).fillna(0).values @ L
    p_cf = va_coeff_counterfactual.reindex(A.index).fillna(0).values @ L

    deviation = np.where(p_actual > 1e-10, (p_cf - p_actual) / p_actual * 100, 0)

    return pd.DataFrame({
        "actual_price": p_actual,
        "counterfactual_price": p_cf,
        "deviation_pct": deviation,
    }, index=A.index)


def all_sector_wage_counterfactuals(
    A: pd.DataFrame,
    value_added_latest: pd.DataFrame,
    value_added_anchor: pd.DataFrame,
    total_output_latest: pd.Series,
    total_output_anchor: pd.Series,
) -> pd.DataFrame:
    """Run counterfactual for each sector restoring its anchor wage share.

    Args:
        A: Current direct requirements matrix.
        value_added_latest: Current VA.
        value_added_anchor: Anchor-year VA (e.g., 1997).
        total_output_latest: Current output.
        total_output_anchor: Anchor output.

    Returns:
        DataFrame with counterfactual_sector, mean_price_impact_pct,
        max_downstream_impact_pct, wage_share_change_pp.
    """
    sectors = A.index
    n = len(sectors)
    L = linalg.inv(np.eye(n) - A.values)

    if isinstance(value_added_latest, pd.DataFrame):
        va_actual = value_added_latest.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va_actual = value_added_latest.reindex(sectors).fillna(0)

    x_actual = total_output_latest.reindex(sectors).fillna(0)
    va_coeff_actual = (va_actual / x_actual.replace(0, np.nan)).fillna(0)
    p_actual = va_coeff_actual.values @ L

    rows = []
    for sector in sectors:
        va_cf = counterfactual_wage_share(
            value_added_latest, value_added_anchor,
            total_output_latest, total_output_anchor,
            sector, sectors,
        )
        p_cf = va_cf.values @ L
        deviation = np.where(p_actual > 1e-10, (p_cf - p_actual) / p_actual * 100, 0)

        rows.append({
            "counterfactual_sector": sector,
            "mean_price_impact_pct": float(np.mean(deviation)),
            "max_price_impact_pct": float(np.max(np.abs(deviation))),
            "own_price_impact_pct": float(deviation[sectors.get_loc(sector)]),
        })

    return pd.DataFrame(rows).set_index("counterfactual_sector").sort_values(
        "mean_price_impact_pct", key=abs, ascending=False
    )
