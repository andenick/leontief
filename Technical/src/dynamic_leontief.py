"""Dynamic Leontief model with capital coefficients.

Extends the static I-O model with capital stock requirements to study
investment needs, balanced growth, and dynamic adjustment paths.

Reference: Leontief (1970); Duchin & Szyld (1985); Miller & Blair Ch. 6.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def capital_output_ratios(
    capital_stock: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Compute capital-output ratio by sector.

    Args:
        capital_stock: Net fixed assets by sector.
        total_output: Total output by sector.

    Returns:
        Series of capital-output ratios (K/x).
    """
    common = capital_stock.index.intersection(total_output.index)
    k = capital_stock.reindex(common).fillna(0)
    x = total_output.reindex(common).fillna(0).replace(0, np.nan)
    result = (k / x).fillna(0)
    result.name = "capital_output_ratio"
    return result


def investment_requirements(
    B: pd.Series,
    delta_x: pd.Series,
) -> pd.Series:
    """Compute investment needed to support output growth.

    I = B * delta_x (for diagonal B)

    Args:
        B: Capital-output ratios by sector (diagonal of B matrix).
        delta_x: Change in output by sector.

    Returns:
        Series of required investment by sector.
    """
    common = B.index.intersection(delta_x.index)
    b = B.reindex(common).fillna(0)
    dx = delta_x.reindex(common).fillna(0)
    result = b * dx
    result.name = "investment_required"
    return result


def dynamic_leontief_system(
    A: pd.DataFrame,
    B: pd.Series,
    x_0: pd.Series,
    growth_rate: float = 0.03,
    T: int = 5,
) -> pd.DataFrame:
    """Solve the dynamic Leontief system for a given growth rate.

    x(t) = A*x(t) + B*(x(t+1) - x(t)) + f(t)
    Simplified: given uniform growth g, x(t) = (1+g)^t * x(0)

    Computes the investment requirements and consumption residual
    at each time step.

    Args:
        A: Direct requirements matrix.
        B: Capital-output ratios (diagonal).
        x_0: Initial output vector.
        growth_rate: Annual growth rate.
        T: Number of time periods.

    Returns:
        DataFrame with time periods as rows showing output, investment,
        intermediate inputs, and consumption residual.
    """
    sectors = A.index
    b = B.reindex(sectors).fillna(0).values
    x = x_0.reindex(sectors).fillna(0).values.astype(float)

    rows = []
    for t in range(T + 1):
        x_t = x * (1 + growth_rate) ** t
        x_next = x * (1 + growth_rate) ** (t + 1)

        intermediate = A.values @ x_t
        investment = b * (x_next - x_t)
        consumption = x_t - intermediate - investment

        rows.append({
            "period": t,
            "total_output": float(x_t.sum()),
            "intermediate_inputs": float(intermediate.sum()),
            "investment": float(investment.sum()),
            "consumption_residual": float(consumption.sum()),
            "investment_share": float(investment.sum() / max(x_t.sum(), 1e-10)),
        })

    return pd.DataFrame(rows).set_index("period")


def dynamic_multiplier(
    A: pd.DataFrame,
    B: pd.Series,
    shock_sector: str,
    time_horizon: int = 10,
) -> pd.DataFrame:
    """Compute time-path of output response to a unit demand shock.

    Shows how a one-time increase in final demand propagates through
    time via investment (accelerator) effects.

    Args:
        A: Direct requirements matrix.
        B: Capital-output ratios.
        shock_sector: Sector receiving the demand shock.
        time_horizon: Number of periods to trace.

    Returns:
        DataFrame with periods as rows, sectors as columns.
    """
    n = A.shape[0]
    sectors = A.index
    b = B.reindex(sectors).fillna(0).values
    L = linalg.inv(np.eye(n) - A.values)

    shock_idx = sectors.get_loc(shock_sector)
    f_shock = np.zeros(n)
    f_shock[shock_idx] = 1.0

    # Period 0: static Leontief multiplier
    x_prev = L @ f_shock
    results = {0: pd.Series(x_prev, index=sectors)}

    for t in range(1, time_horizon + 1):
        # Investment demand from output change
        dx = results[t - 1].values - (results[t - 2].values if t > 1 else np.zeros(n))
        investment_demand = b * dx

        # New output = static response to (original shock + investment demand)
        total_demand = f_shock + np.clip(investment_demand, 0, None)
        x_t = L @ total_demand
        results[t] = pd.Series(x_t, index=sectors)

    df = pd.DataFrame(results).T
    df.index.name = "period"
    return df


def balanced_growth_path(
    A: pd.DataFrame,
    B: pd.Series,
) -> Tuple[float, pd.Series]:
    """Compute the balanced (von Neumann) growth rate and proportions.

    Solves: B^(-1) * (I - A) * x = (1 + g) * x
    The dominant eigenvalue gives (1 + g_max).

    Args:
        A: Direct requirements matrix.
        B: Capital-output ratios by sector.

    Returns:
        Tuple of (balanced_growth_rate, proportional_output_vector).
    """
    sectors = A.index
    b = B.reindex(sectors).fillna(0).values
    n = len(sectors)

    # Only sectors with positive capital requirements participate
    valid = b > 0
    if not valid.any():
        logger.warning("No sectors with positive capital requirements")
        return 0.0, pd.Series(0, index=sectors)

    A_valid = A.values[np.ix_(valid, valid)]
    b_valid = b[valid]
    n_valid = valid.sum()

    B_inv = np.diag(1.0 / b_valid)
    M = B_inv @ (np.eye(n_valid) - A_valid)

    eigenvalues, eigenvectors = linalg.eig(M)
    real_positive = [(ev, eigenvectors[:, i]) for i, ev in enumerate(eigenvalues)
                     if np.isreal(ev) and ev.real > 0]

    if not real_positive:
        logger.warning("No positive real eigenvalue found")
        return 0.0, pd.Series(0, index=sectors)

    real_positive.sort(key=lambda x: -x[0].real)
    lambda_max = float(real_positive[0][0].real)
    proportions = np.abs(real_positive[0][1].real)
    proportions = proportions / proportions.sum()

    growth_rate = lambda_max - 1.0

    full_proportions = np.zeros(n)
    full_proportions[valid] = proportions
    result = pd.Series(full_proportions, index=sectors, name="balanced_proportions")

    logger.info(f"Balanced growth rate: {growth_rate:.4f} ({growth_rate*100:.2f}%)")
    return float(growth_rate), result


def turnpike_analysis(
    A: pd.DataFrame,
    B: pd.Series,
    x_0: pd.Series,
    x_T: pd.Series,
    T: int = 10,
) -> pd.DataFrame:
    """Analyze how close an economy's growth path is to the turnpike.

    The turnpike theorem: optimal growth paths spend most of their time
    near the balanced growth path regardless of initial/terminal conditions.

    Args:
        A: Direct requirements matrix.
        B: Capital-output ratios.
        x_0: Initial output vector.
        x_T: Terminal output vector.
        T: Number of periods.

    Returns:
        DataFrame with deviation from balanced proportions at each period.
    """
    g_star, balanced = balanced_growth_path(A, B)
    if g_star <= 0:
        return pd.DataFrame()

    sectors = A.index
    x0 = x_0.reindex(sectors).fillna(0).values
    xT = x_T.reindex(sectors).fillna(0).values
    bp = balanced.values

    rows = []
    for t in range(T + 1):
        alpha = t / T
        x_t = (1 - alpha) * x0 + alpha * xT
        x_norm = x_t / max(x_t.sum(), 1e-10)

        deviation = np.sqrt(np.sum((x_norm - bp) ** 2))
        cosine_sim = np.dot(x_norm, bp) / (np.linalg.norm(x_norm) * np.linalg.norm(bp) + 1e-15)

        rows.append({
            "period": t,
            "deviation_from_balanced": float(deviation),
            "cosine_similarity": float(cosine_sim),
            "total_output": float(x_t.sum()),
        })

    return pd.DataFrame(rows).set_index("period")
