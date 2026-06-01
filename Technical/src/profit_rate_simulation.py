"""Profit rate equalization and Sraffian price simulation.

Simulates classical competition: capital flows toward high-profit sectors,
driving profit rates toward equalization. Connects to the transformation
problem (labor values vs. production prices).

Reference: Sraffa (1960); Shaikh (2016); Miller & Blair Ch. 3.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def sectoral_profit_rates(
    A: pd.DataFrame,
    wages: pd.Series,
    total_output: pd.Series,
    value_added: pd.DataFrame,
) -> pd.Series:
    """Compute gross profit rate by sector.

    r_j = (VA_j - wages_j) / (intermediate_inputs_j)
    where intermediate_inputs_j = sum_i(A_ij * x_j)

    Args:
        A: Direct requirements matrix.
        wages: Wage bill by sector (compensation of employees).
        total_output: Total output by sector.
        value_added: Value added DataFrame (rows = VA components, cols = sectors).

    Returns:
        Series of gross profit rates by sector.
    """
    sectors = A.index
    w = wages.reindex(sectors).fillna(0)
    x = total_output.reindex(sectors).fillna(0)

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va = value_added.reindex(sectors).fillna(0)

    surplus = va - w
    intermediate = (A.values * x.values[np.newaxis, :]).sum(axis=0)
    intermediate_s = pd.Series(intermediate, index=sectors)

    rates = surplus / intermediate_s.replace(0, np.nan)
    rates = rates.fillna(0)
    rates.name = "profit_rate"

    logger.info(f"Profit rates: mean={rates.mean():.4f}, std={rates.std():.4f}")
    return rates


def sraffian_prices(
    A: pd.DataFrame,
    wages_share: pd.Series,
    profit_rate: float,
) -> pd.Series:
    """Compute Sraffian production prices at a uniform profit rate.

    p = w * (I - A*(1+r))^(-1)

    Args:
        A: Direct requirements matrix.
        wages_share: Wage cost per unit output by sector (w_j / x_j).
        profit_rate: Uniform profit rate r.

    Returns:
        Series of production prices by sector.
    """
    n = A.shape[0]
    w = wages_share.reindex(A.index).fillna(0).values
    M = np.eye(n) - A.values * (1 + profit_rate)

    try:
        prices = w @ linalg.inv(M)
    except linalg.LinAlgError:
        logger.warning(f"Sraffian price system singular at r={profit_rate:.4f}")
        prices = np.full(n, np.nan)

    result = pd.Series(prices, index=A.index, name="production_price")
    return result


def maximum_profit_rate(A: pd.DataFrame) -> float:
    """Compute the maximum feasible profit rate (Sraffa's R).

    R = 1/lambda_max(A) - 1, where lambda_max is the dominant eigenvalue.
    Above R, the price system has no positive solution.

    Args:
        A: Direct requirements matrix.

    Returns:
        Maximum profit rate R.
    """
    eigenvalues = linalg.eigvals(A.values)
    lambda_max = np.max(np.abs(eigenvalues))
    if lambda_max <= 0 or lambda_max >= 1:
        return 0.0
    return float(1.0 / lambda_max - 1.0)


def equalize_profit_rates(
    A: pd.DataFrame,
    wages: pd.Series,
    total_output: pd.Series,
    value_added: pd.DataFrame,
    max_iter: int = 500,
    tol: float = 1e-6,
) -> Dict:
    """Simulate profit rate equalization via capital flow.

    Iteratively:
    1. Compute sectoral profit rates
    2. Shift output weights toward high-profit sectors
    3. Recompute A via proportional scaling
    4. Repeat until profit rate variance < tol

    Args:
        A: Direct requirements matrix.
        wages: Wage bill by sector.
        total_output: Total output by sector.
        value_added: VA DataFrame.
        max_iter: Maximum iterations.
        tol: Convergence tolerance (variance of profit rates).

    Returns:
        Dict with convergence_path, final_rates, final_output_weights.
    """
    sectors = A.index
    x = total_output.reindex(sectors).fillna(0).values.astype(float)
    x_total = x.sum()

    log_rows = []

    for iteration in range(max_iter):
        x_series = pd.Series(x, index=sectors)
        rates = sectoral_profit_rates(A, wages, x_series, value_added)
        r_vals = rates.values
        r_mean = np.mean(r_vals)
        r_var = np.var(r_vals)

        log_rows.append({
            "iteration": iteration,
            "mean_rate": float(r_mean),
            "variance": float(r_var),
            "max_rate": float(np.max(r_vals)),
            "min_rate": float(np.min(r_vals)),
        })

        if r_var < tol:
            logger.info(f"Profit rates equalized in {iteration} iterations (var={r_var:.2e})")
            break

        # Shift output toward high-profit sectors
        adjustment = 1 + 0.1 * (r_vals - r_mean) / max(np.std(r_vals), 1e-10)
        adjustment = np.clip(adjustment, 0.9, 1.1)
        x = x * adjustment
        x = x * (x_total / x.sum())
    else:
        logger.warning(f"Profit equalization did not converge after {max_iter} iterations")

    return {
        "convergence_path": pd.DataFrame(log_rows),
        "final_rates": pd.Series(r_vals, index=sectors, name="equalized_rate"),
        "final_output_weights": pd.Series(x / x.sum(), index=sectors, name="output_weight"),
        "converged": r_var < tol,
        "iterations": len(log_rows),
    }


def transformation_problem_prices(
    A: pd.DataFrame,
    labor_coeff: pd.Series,
    uniform_rate: float,
) -> pd.DataFrame:
    """Compare labor values with production prices at a uniform profit rate.

    Args:
        A: Direct requirements matrix.
        labor_coeff: Direct labor per unit output.
        uniform_rate: Uniform profit rate for Sraffian prices.

    Returns:
        DataFrame with labor_value, production_price, deviation_pct.
    """
    n = A.shape[0]
    l = labor_coeff.reindex(A.index).fillna(0).values

    L = linalg.inv(np.eye(n) - A.values)
    labor_values = l @ L

    wages_share = labor_coeff.reindex(A.index).fillna(0)
    prod_prices = sraffian_prices(A, wages_share, uniform_rate)

    lv_norm = labor_values / max(np.mean(labor_values), 1e-15)
    pp_norm = prod_prices.values / max(np.mean(prod_prices.values), 1e-15)

    deviation = np.where(
        lv_norm > 1e-10,
        (pp_norm - lv_norm) / lv_norm * 100,
        0,
    )

    result = pd.DataFrame({
        "labor_value": labor_values,
        "production_price": prod_prices.values,
        "labor_value_normalized": lv_norm,
        "production_price_normalized": pp_norm,
        "deviation_pct": deviation,
    }, index=A.index)

    logger.info(f"Transformation: mean abs deviation = {np.abs(deviation).mean():.1f}%")
    return result


def wage_profit_frontier(
    A: pd.DataFrame,
    labor_coeff: pd.Series,
    n_points: int = 50,
) -> pd.DataFrame:
    """Trace the wage-profit frontier (Sraffa's w-r curve).

    For each profit rate from 0 to R_max, compute the maximum
    real wage consistent with non-negative prices.

    Args:
        A: Direct requirements matrix.
        labor_coeff: Direct labor per unit output.
        n_points: Number of points along the frontier.

    Returns:
        DataFrame with profit_rate, max_real_wage columns.
    """
    R_max = maximum_profit_rate(A)
    if R_max <= 0:
        return pd.DataFrame(columns=["profit_rate", "max_real_wage"])

    rates = np.linspace(0, R_max * 0.99, n_points)
    wages = []

    for r in rates:
        prices = sraffian_prices(A, labor_coeff, r)
        if np.any(np.isnan(prices.values)) or np.any(prices.values < 0):
            wages.append(0.0)
        else:
            wages.append(float(1.0 / max(prices.mean(), 1e-15)))

    return pd.DataFrame({
        "profit_rate": rates,
        "max_real_wage": wages,
    })
