"""Marxian Value Analysis and Pasinetti Vertical Integration via I-O tables.

Implements:
- Vertically integrated labor coefficients (Pasinetti 1981)
- Labor values / embodied labor (Marxian value theory)
- Rate of surplus value by sector
- Organic composition of capital by sector
- Price-value deviations

References:
- Pasinetti (1981) — Structural Change and Economic Growth
- Foley, Dumenil — Marxian Transformation Problem
- Shaikh — value theory and I-O applications
All from Wynne Knowledge Base.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def vertically_integrated_labor(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
) -> pd.Series:
    """Calculate vertically integrated labor coefficients (Pasinetti).

    v = l' × (I - A)^(-1)

    Each element vⱼ gives the total labor (direct + indirect) embodied
    per unit of sector j's final output.

    Args:
        A: Direct requirements matrix (n x n).
        labor_coefficients: Direct labor per unit output by sector (l = emp/x).

    Returns:
        Series of vertically integrated labor coefficients, indexed by sector.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)
    v = labor_coefficients.values @ L
    result = pd.Series(v, index=A.columns, name="vertically_integrated_labor")
    logger.info(f"Vertically integrated labor: mean={result.mean():.6f}")
    return result


def labor_values(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
) -> pd.Series:
    """Calculate Marxian labor values (embodied labor per unit output).

    λ = l' × (I - A)^(-1)

    Mathematically identical to vertically integrated labor.
    Interpretation differs: these are the total socially necessary
    labor time embodied in each commodity.

    Args:
        A: Direct requirements matrix.
        labor_coefficients: Direct labor input per unit output.

    Returns:
        Series of labor values by sector.
    """
    result = vertically_integrated_labor(A, labor_coefficients)
    result.name = "labor_value"
    return result


def rate_of_surplus_value(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
    wages: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Calculate rate of surplus value (s/v) by sector.

    s/v = (λⱼ·xⱼ - wⱼ) / wⱼ

    Where:
    - λⱼ = labor value of sector j's output
    - xⱼ = total output of sector j
    - wⱼ = total wage bill in sector j

    Args:
        A: Direct requirements matrix.
        labor_coefficients: Direct labor per unit output.
        wages: Total wage bill by sector.
        total_output: Total output by sector.

    Returns:
        Series of surplus value rates by sector.
    """
    lv = labor_values(A, labor_coefficients)
    total_labor_value = lv * total_output
    surplus = total_labor_value - wages
    rate = surplus / wages.replace(0, np.nan)
    rate = rate.fillna(0)
    rate.name = "rate_of_surplus_value"

    logger.info(f"Rate of surplus value: mean={rate.mean():.3f}")
    return rate


def organic_composition(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
    wages: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Calculate organic composition of capital (c/v) by sector.

    c/v = (constant capital) / (variable capital)
        = (Σᵢ aᵢⱼ·λᵢ·xⱼ) / wⱼ

    Where constant capital is the labor value of material inputs.

    Args:
        A: Direct requirements matrix.
        labor_coefficients: Direct labor per unit output.
        wages: Total wage bill by sector.
        total_output: Total output by sector.

    Returns:
        Series of organic composition by sector.
    """
    lv = labor_values(A, labor_coefficients)

    # Constant capital per unit output: sum of (aᵢⱼ × λᵢ) for each j
    # This is: lv' × A (labor value of intermediate inputs)
    constant_capital_coeff = lv.values @ A.values
    constant_capital = constant_capital_coeff * total_output.values

    oc = constant_capital / wages.replace(0, np.nan).values
    oc = np.nan_to_num(oc, nan=0.0)
    result = pd.Series(oc, index=A.columns, name="organic_composition")

    logger.info(f"Organic composition: mean={result.mean():.3f}")
    return result


def price_value_deviation(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
    market_prices: pd.Series,
) -> pd.DataFrame:
    """Calculate deviation of market prices from labor values.

    Measures: (pⱼ - λⱼ) / λⱼ × 100

    The transformation problem: market prices deviate from labor values
    due to equalization of profit rates across sectors with different
    organic compositions.

    Args:
        A: Direct requirements matrix.
        labor_coefficients: Direct labor per unit output.
        market_prices: Market prices per unit output by sector.

    Returns:
        DataFrame with labor_value, market_price, deviation_pct.
    """
    lv = labor_values(A, labor_coefficients)

    # Normalize both to same scale
    lv_norm = lv / lv.mean()
    mp_norm = market_prices / market_prices.mean()

    deviation = ((mp_norm - lv_norm) / lv_norm.replace(0, np.nan)) * 100

    result = pd.DataFrame({
        "labor_value": lv,
        "labor_value_normalized": lv_norm,
        "market_price_normalized": mp_norm,
        "deviation_pct": deviation.fillna(0),
    })

    logger.info(f"Price-value deviation: mean abs = {result['deviation_pct'].abs().mean():.1f}%")
    return result


def value_analysis_summary(
    A: pd.DataFrame,
    labor_coefficients: pd.Series,
    wages: pd.Series,
    total_output: pd.Series,
    market_prices: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Run complete Marxian value analysis and return summary DataFrame.

    Args:
        A: Direct requirements matrix.
        labor_coefficients: Direct labor per unit output.
        wages: Total wage bill by sector.
        total_output: Total output by sector.
        market_prices: Optional market prices for price-value deviation.

    Returns:
        DataFrame with all value metrics by sector.
    """
    lv = labor_values(A, labor_coefficients)
    sv = rate_of_surplus_value(A, labor_coefficients, wages, total_output)
    oc = organic_composition(A, labor_coefficients, wages, total_output)

    result = pd.DataFrame({
        "labor_value": lv,
        "rate_of_surplus_value": sv,
        "organic_composition": oc,
        "total_output": total_output,
        "wages": wages,
    })

    if market_prices is not None:
        pvd = price_value_deviation(A, labor_coefficients, market_prices)
        result["price_value_deviation_pct"] = pvd["deviation_pct"]

    return result.sort_values("labor_value", ascending=False)


def pasinetti_subsystem(
    L: np.ndarray,
    f: pd.Series,
    total_output: pd.Series,
    labor_coefficients: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Compute Pasinetti's vertically integrated subsystems.

    For each final good j, the subsystem is the column j of L scaled by
    final demand f_j, giving the complete vertically integrated sector
    that "belongs" to producing good j.

    Args:
        L: Leontief inverse matrix (numpy array, from scipy.linalg.inv).
        f: Final demand vector.
        total_output: Total output by sector.
        labor_coefficients: Optional direct labor per unit output.

    Returns:
        DataFrame with subsystem_output, f_share, subsystem_output_share
        per sector j, plus subsystem_labor if labor_coefficients provided.
    """
    if isinstance(L, pd.DataFrame):
        L_vals = L.values
        sectors = L.index
    else:
        sectors = f.index
        L_vals = L

    f_vals = f.reindex(sectors).fillna(0).values
    x_vals = total_output.reindex(sectors).fillna(0).values

    # Subsystem output for good j: column j of L * f_j
    subsystem_output = np.zeros(len(sectors))
    for j in range(len(sectors)):
        subsystem_output[j] = L_vals[:, j].sum() * f_vals[j]

    f_total = f_vals.sum()
    x_total = x_vals.sum()

    result = pd.DataFrame({
        "final_demand": f_vals,
        "f_share": f_vals / max(f_total, 1e-10),
        "subsystem_output": subsystem_output,
        "subsystem_output_share": subsystem_output / max(x_total, 1e-10),
    }, index=sectors)

    if labor_coefficients is not None:
        l = labor_coefficients.reindex(sectors).fillna(0).values
        subsystem_labor = np.zeros(len(sectors))
        for j in range(len(sectors)):
            subsystem_labor[j] = (l * L_vals[:, j]).sum() * f_vals[j]
        result["subsystem_labor"] = subsystem_labor

    return result


def productivity_growth_decomposition(
    sub_0: pd.DataFrame,
    sub_1: pd.DataFrame,
) -> pd.DataFrame:
    """Decompose aggregate labor productivity growth into within vs. between.

    Within-sector: productivity gains within each Pasinetti subsystem.
    Between-sector (structural): reallocation of output across subsystems.

    Args:
        sub_0: Pasinetti subsystem DataFrame for period 0.
        sub_1: Pasinetti subsystem DataFrame for period 1.

    Returns:
        DataFrame with within_effect, between_effect, total_effect per sector.
    """
    common = sub_0.index.intersection(sub_1.index)
    s0 = sub_0.loc[common]
    s1 = sub_1.loc[common]

    if "subsystem_labor" not in s0.columns or "subsystem_labor" not in s1.columns:
        raise ValueError("subsystem_labor column required; pass labor_coefficients to pasinetti_subsystem")

    # Labor productivity = output / labor in each subsystem
    prod_0 = s0["subsystem_output"] / s0["subsystem_labor"].replace(0, np.nan)
    prod_1 = s1["subsystem_output"] / s1["subsystem_labor"].replace(0, np.nan)

    share_0 = s0["subsystem_labor"] / max(s0["subsystem_labor"].sum(), 1e-10)
    share_1 = s1["subsystem_labor"] / max(s1["subsystem_labor"].sum(), 1e-10)

    # Shift-share decomposition
    within = (prod_1 - prod_0).fillna(0) * share_0
    between = prod_0.fillna(0) * (share_1 - share_0)
    interaction = (prod_1 - prod_0).fillna(0) * (share_1 - share_0)

    return pd.DataFrame({
        "within_effect": within,
        "between_effect": between,
        "interaction_effect": interaction,
        "total_effect": within + between + interaction,
        "productivity_0": prod_0,
        "productivity_1": prod_1,
        "labor_share_0": share_0,
        "labor_share_1": share_1,
    }).fillna(0)
