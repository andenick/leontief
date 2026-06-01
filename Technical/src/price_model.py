"""Cost-push price model from Input-Output analysis.

Implements the dual (price) side of the Leontief system:
    p' = v'c × (I - A)^(-1) = v'c × L

Where p is the vector of prices and v_c is value-added coefficients.

Reference: Miller & Blair (2009), Ch. 3 — from Wynne KB.
"""

import numpy as np
import pandas as pd
from scipy import linalg
import logging

logger = logging.getLogger(__name__)


def cost_push_prices(
    A: pd.DataFrame,
    value_added_coefficients: pd.Series,
) -> pd.Series:
    """Calculate cost-push equilibrium prices.

    p' = v'c × (I - A)^(-1)

    Given value-added (cost) coefficients per unit output, this
    calculates the prices that clear all markets.

    Args:
        A: Direct requirements matrix.
        value_added_coefficients: Value-added per unit output by sector.

    Returns:
        Series of equilibrium prices by sector.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)
    prices = value_added_coefficients.values @ L

    result = pd.Series(prices, index=A.columns, name="equilibrium_price")
    logger.info(f"Cost-push prices: mean={result.mean():.4f}")
    return result


def price_impact(
    A: pd.DataFrame,
    value_added_coefficients: pd.Series,
    cost_shock: pd.Series,
) -> pd.DataFrame:
    """Calculate price impacts of a cost shock.

    Δp = L' × Δv_c

    Shows how a change in value-added costs propagates through
    the inter-industry structure to affect all prices.

    Args:
        A: Direct requirements matrix.
        value_added_coefficients: Baseline value-added coefficients.
        cost_shock: Change in value-added coefficients (Δv_c).

    Returns:
        DataFrame with baseline price, shocked price, and change.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)

    baseline = value_added_coefficients.values @ L
    delta_p = cost_shock.values @ L
    shocked = baseline + delta_p

    result = pd.DataFrame({
        "baseline_price": baseline,
        "price_change": delta_p,
        "shocked_price": shocked,
        "change_pct": np.where(baseline != 0, (delta_p / baseline) * 100, 0),
    }, index=A.columns)

    logger.info(f"Price impact: mean change = {result['change_pct'].mean():.2f}%")
    return result


def price_decomposition(
    A: pd.DataFrame,
    value_added_components: pd.DataFrame,
) -> pd.DataFrame:
    """Decompose prices into contributions from each value-added component.

    For each VA component (wages, profits, taxes, imports):
        contribution_k = v_k' × L

    Args:
        A: Direct requirements matrix.
        value_added_components: DataFrame where each row is a VA component
            (e.g., compensation, taxes, gross operating surplus)
            and columns are sectors.

    Returns:
        DataFrame with price contributions from each VA component.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)

    contributions = {}
    for component in value_added_components.index:
        v_k = value_added_components.loc[component].values
        contrib = v_k @ L
        contributions[component] = contrib

    result = pd.DataFrame(contributions, index=A.columns)
    result["total_price"] = result.sum(axis=1)

    logger.info(f"Price decomposition: {len(value_added_components)} components")
    return result


def markup_pricing(
    A: pd.DataFrame,
    wages_per_unit: pd.Series,
    markup_rates: pd.Series,
) -> pd.Series:
    """Kalecki/post-Keynesian markup pricing model.

    p_j = (1 + m_j) * (w_j + sum_i a_ij * p_i)

    Solves iteratively: p = (I + M) * (w + A' * p)
    Rearranged: p = (I - (I + M) * A')^(-1) * (I + M) * w

    Args:
        A: Direct requirements matrix.
        wages_per_unit: Direct wage cost per unit output by sector.
        markup_rates: Gross markup rates m_j by sector (e.g., 0.2 = 20% markup).

    Returns:
        Series of markup-based prices by sector.
    """
    n = A.shape[0]
    w = wages_per_unit.reindex(A.index).fillna(0).values
    m = markup_rates.reindex(A.index).fillna(0).values

    M = np.diag(1 + m)
    # p = (I - M @ A')^(-1) @ M @ w
    system = np.eye(n) - M @ A.values.T
    rhs = M @ w

    try:
        prices = linalg.solve(system, rhs)
    except linalg.LinAlgError:
        logger.warning("Markup pricing system singular")
        prices = np.full(n, np.nan)

    result = pd.Series(prices, index=A.index, name="markup_price")
    logger.info(f"Markup prices: mean={np.nanmean(prices):.4f}")
    return result
