"""Temporal Single System Interpretation (TSSI) valuation.

Implements sequential (non-simultaneous) price determination where
period-0 prices feed into period-1 costs, breaking the simultaneity
of the standard transformation problem.

Reference: Kliman & McGlone (1999); Freeman & Carchedi (1996).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def melt_monetary_expression(
    total_output: pd.Series,
    labor_coefficients: pd.Series,
) -> float:
    """Compute the Monetary Expression of Labor Time (MELT).

    MELT = sum(p_j * x_j) / sum(l_j * x_j)
    = total monetary output / total labor hours

    Args:
        total_output: Total output by sector (monetary).
        labor_coefficients: Direct labor per unit output.

    Returns:
        MELT in $/labor-hour.
    """
    common = total_output.index.intersection(labor_coefficients.index)
    x = total_output.reindex(common).fillna(0)
    l = labor_coefficients.reindex(common).fillna(0)

    total_money = x.sum()
    total_labor = (l * x).sum()

    if total_labor <= 0:
        return 1.0

    melt = total_money / total_labor
    logger.info(f"MELT: {melt:.2f} $/labor-hour")
    return float(melt)


def tssi_prices_period1(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    wages_coeff_1: pd.Series,
    labor_coeff_0: pd.Series,
    total_output_0: pd.Series,
) -> pd.Series:
    """Compute TSSI period-1 prices using period-0 prices as input costs.

    p1_j = (1 + r) * [sum_i(a1_ij * p0_i) + w1_j]
    where p0 = MELT_0 * lambda_0 (labor values at period-0 monetary expression)

    Iterates to find r that equalizes profits across sectors.

    Args:
        A_0: Period-0 A matrix.
        A_1: Period-1 A matrix.
        wages_coeff_1: Period-1 wage cost per unit output.
        labor_coeff_0: Period-0 labor coefficients.
        total_output_0: Period-0 total output.

    Returns:
        Series of TSSI period-1 prices.
    """
    common = A_0.index.intersection(A_1.index)
    n = len(common)

    A0 = A_0.loc[common, common].values
    A1 = A_1.loc[common, common].values
    l0 = labor_coeff_0.reindex(common).fillna(0).values
    w1 = wages_coeff_1.reindex(common).fillna(0).values
    x0 = total_output_0.reindex(common).fillna(0).values

    # Period-0 prices from labor values
    L0 = linalg.inv(np.eye(n) - A0)
    lambda_0 = l0 @ L0
    melt_0 = melt_monetary_expression(
        pd.Series(x0, index=common),
        pd.Series(l0, index=common),
    )
    p0 = melt_0 * lambda_0

    # Material cost at period-0 prices
    material_cost = A1.T @ p0

    # Find uniform r that satisfies: p1 = (1+r)(material_cost + w1)
    # Total surplus = total output value - total cost
    # Try: r = total_surplus / total_cost
    total_cost = (material_cost + w1).sum()
    if total_cost <= 0:
        return pd.Series(p0, index=common, name="tssi_price")

    # Initial estimate of r from aggregate surplus
    p1_estimate = material_cost + w1
    total_value = p1_estimate.sum()
    r_estimate = max((total_value - total_cost) / total_cost, 0)

    # Iterate for convergence
    for iteration in range(100):
        p1 = (1 + r_estimate) * (material_cost + w1)
        surplus = p1.sum() - (material_cost + w1).sum()
        cost_base = (material_cost + w1).sum()

        r_new = surplus / max(cost_base, 1e-10)
        if abs(r_new - r_estimate) < 1e-8:
            break
        r_estimate = 0.5 * r_estimate + 0.5 * r_new

    p1_final = (1 + r_estimate) * (material_cost + w1)
    result = pd.Series(p1_final, index=common, name="tssi_price")

    logger.info(f"TSSI prices: r={r_estimate:.4f}, mean_price={result.mean():.4f}")
    return result


def tssi_vs_static_comparison(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    wages_coeff_0: pd.Series,
    wages_coeff_1: pd.Series,
    labor_coeff_0: pd.Series,
    labor_coeff_1: pd.Series,
    total_output_0: pd.Series,
) -> pd.DataFrame:
    """Compare TSSI sequential prices with static Sraffian prices.

    Args:
        A_0/1: A matrices for two periods.
        wages_coeff_0/1: Wage coefficients.
        labor_coeff_0/1: Labor coefficients.
        total_output_0: Period-0 output.

    Returns:
        DataFrame with sraffian_price, tssi_price, deviation_pct.
    """
    from profit_rate_simulation import sraffian_prices, maximum_profit_rate

    common = A_0.index.intersection(A_1.index)

    # Static Sraffian for period 1
    A1 = A_1.loc[common, common]
    r_max = maximum_profit_rate(A1)
    r_uniform = r_max * 0.5
    w1 = wages_coeff_1.reindex(common).fillna(0)
    p_sraffa = sraffian_prices(A1, w1, r_uniform)

    # TSSI sequential
    p_tssi = tssi_prices_period1(A_0, A_1, wages_coeff_1, labor_coeff_0, total_output_0)

    p_sraffa_aligned = p_sraffa.reindex(common).fillna(0)
    p_tssi_aligned = p_tssi.reindex(common).fillna(0)

    # Normalize both to mean = 1
    ps_norm = p_sraffa_aligned / max(p_sraffa_aligned.mean(), 1e-10)
    pt_norm = p_tssi_aligned / max(p_tssi_aligned.mean(), 1e-10)

    deviation = np.where(
        ps_norm.values > 1e-10,
        (pt_norm.values - ps_norm.values) / ps_norm.values * 100,
        0,
    )

    return pd.DataFrame({
        "sraffian_price": ps_norm,
        "tssi_price": pt_norm,
        "deviation_pct": deviation,
    }, index=common)


def tssi_melt_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Track MELT across years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year, melt, total_monetary, total_labor.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        x = d.get("total_output")
        va = d.get("value_added")

        if x is None or va is None:
            continue

        sectors = x.index
        if isinstance(va, pd.DataFrame):
            comp_rows = [r for r in va.index if "V001" in str(r)]
            if comp_rows:
                wages = va.loc[comp_rows[0]].reindex(sectors).fillna(0)
            else:
                wages = va.iloc[0].reindex(sectors).fillna(0)
        else:
            wages = va.reindex(sectors).fillna(0) * 0.5

        labor_coeff = (wages / x.replace(0, np.nan)).fillna(0)
        melt = melt_monetary_expression(x, labor_coeff)

        rows.append({
            "year": year,
            "melt": melt,
            "total_monetary": float(x.sum()),
            "total_labor": float((labor_coeff * x).sum()),
        })

    return pd.DataFrame(rows).set_index("year")
