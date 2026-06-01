"""Keynesian/Sraffian supermultiplier analysis.

Extends the standard Leontief multiplier by endogenizing investment
(accelerator) and government spending response to capacity utilization.

Reference: Serrano (1995); Freitas & Serrano (2015).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def capacity_utilization_proxy(
    total_output: pd.Series,
    total_output_trend: pd.Series,
) -> pd.Series:
    """Compute capacity utilization as output / trend-output ratio.

    Args:
        total_output: Actual output by sector.
        total_output_trend: Trend output (HP-filtered or linear).

    Returns:
        Series of utilization rates.
    """
    trend_safe = total_output_trend.replace(0, np.nan)
    util = (total_output / trend_safe).fillna(1.0)
    util.name = "capacity_utilization"
    return util


def _linear_trend(series_by_year: Dict[int, float]) -> Dict[int, float]:
    """Compute linear trend from year->value dict."""
    years = sorted(series_by_year.keys())
    vals = [series_by_year[y] for y in years]
    if len(years) < 2:
        return series_by_year

    coeffs = np.polyfit(years, vals, 1)
    return {y: np.polyval(coeffs, y) for y in years}


def keynesian_supermultiplier(
    A: pd.DataFrame,
    final_demand: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    autonomous_col_prefixes: List[str] = None,
    investment_col_prefix: str = "F03",
    induced_investment_elasticity: float = 0.3,
) -> Dict[str, float]:
    """Compute the Sraffian supermultiplier.

    SM = 1 / (1 - c*(1-t) - h)
    where c = marginal propensity to consume from wages
          t = effective tax rate
          h = induced investment propensity

    Args:
        A: Direct requirements matrix.
        final_demand: FD DataFrame.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        autonomous_col_prefixes: Prefixes for autonomous demand (gov spending).
        investment_col_prefix: Prefix for investment columns.
        induced_investment_elasticity: h parameter.

    Returns:
        Dict with supermultiplier, standard_multiplier, ratio, components.
    """
    if autonomous_col_prefixes is None:
        autonomous_col_prefixes = ["F06", "F07"]

    sectors = A.index
    n = len(sectors)

    # Standard multiplier
    L = linalg.inv(np.eye(n) - A.values)
    standard_mult = L.sum() / n

    # Components
    if isinstance(value_added, pd.DataFrame):
        comp_rows = [r for r in value_added.index if "V001" in str(r)]
        tax_rows = [r for r in value_added.index if "V002" in str(r)]
        va_total = value_added.sum(axis=0).reindex(sectors).fillna(0)

        wages = value_added.loc[comp_rows[0]].reindex(sectors).fillna(0) if comp_rows else va_total * 0.5
        taxes = value_added.loc[tax_rows[0]].reindex(sectors).fillna(0) if tax_rows else va_total * 0.1
    else:
        wages = value_added.reindex(sectors).fillna(0) * 0.5
        taxes = value_added.reindex(sectors).fillna(0) * 0.1

    x = total_output.reindex(sectors).fillna(0)
    x_total = x.sum()

    # c = aggregate wage-to-consumption ratio
    wage_total = wages.sum()
    pce_cols = [c for c in final_demand.columns if str(c).startswith("F01")]
    if pce_cols:
        pce_total = final_demand[pce_cols].sum().sum()
    else:
        pce_total = wage_total * 0.9

    c = pce_total / max(wage_total, 1e-10)
    c = min(c, 0.95)

    # t = effective tax rate
    t = taxes.sum() / max(x_total, 1e-10)
    t = min(t, 0.5)

    # h = induced investment elasticity
    h = induced_investment_elasticity

    # Supermultiplier
    denom = 1 - c * (1 - t) - h
    if denom <= 0.01:
        denom = 0.01
        logger.warning("Supermultiplier denominator near zero; capping")

    supermult = 1.0 / denom

    return {
        "supermultiplier": float(supermult),
        "standard_multiplier": float(standard_mult),
        "ratio_sm_to_standard": float(supermult / max(standard_mult, 1e-10)),
        "propensity_to_consume": float(c),
        "effective_tax_rate": float(t),
        "induced_investment_elasticity": float(h),
        "denominator": float(denom),
    }


def supermultiplier_timeseries(
    data_by_year: Dict[int, dict],
    induced_investment_elasticity: float = 0.3,
) -> pd.DataFrame:
    """Track supermultiplier and components across years.

    Args:
        data_by_year: Dict of year -> data dict.
        induced_investment_elasticity: h parameter.

    Returns:
        DataFrame with year, supermultiplier, standard_multiplier, components.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        fd = d.get("final_demand")
        va = d.get("value_added")
        x = d.get("total_output")

        if A is None or fd is None or va is None or x is None:
            continue
        if isinstance(fd, pd.Series):
            continue

        try:
            result = keynesian_supermultiplier(
                A, fd, va, x,
                induced_investment_elasticity=induced_investment_elasticity,
            )
            result["year"] = year
            rows.append(result)
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year")
