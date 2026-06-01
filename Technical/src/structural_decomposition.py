"""Structural Decomposition Analysis (SDA) for Input-Output tables.

Decomposes changes in output between two time periods into:
- Technology effect (changes in A matrix / Leontief inverse)
- Final demand effect (changes in demand composition)
- Interaction term (combined effect)

Reference: Miller & Blair (2009/2022), Ch. 13 — from Wynne KB.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def _leontief_inverse(A: np.ndarray) -> np.ndarray:
    """Calculate L = (I - A)^(-1)."""
    n = A.shape[0]
    return linalg.inv(np.eye(n) - A)


def structural_decomposition_3term(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    f_0: pd.Series,
    f_1: pd.Series,
) -> Dict[str, pd.Series]:
    """Three-term structural decomposition of output change.

    Δx = L¹·Δf + ΔL·f⁰ + ΔL·Δf

    Args:
        A_0: Direct requirements matrix, period 0.
        A_1: Direct requirements matrix, period 1.
        f_0: Final demand vector, period 0.
        f_1: Final demand vector, period 1.

    Returns:
        Dict with keys: total_change, demand_effect, technology_effect,
        interaction_effect, and component Series indexed by sector.
    """
    L_0 = _leontief_inverse(A_0.values)
    L_1 = _leontief_inverse(A_1.values)

    delta_f = f_1.values - f_0.values
    delta_L = L_1 - L_0

    demand_effect = L_1 @ delta_f
    technology_effect = delta_L @ f_0.values
    interaction_effect = delta_L @ delta_f
    total_change = demand_effect + technology_effect + interaction_effect

    idx = A_0.index

    result = {
        "total_change": pd.Series(total_change, index=idx, name="Total Change"),
        "demand_effect": pd.Series(demand_effect, index=idx, name="Final Demand Effect"),
        "technology_effect": pd.Series(technology_effect, index=idx, name="Technology Effect"),
        "interaction_effect": pd.Series(interaction_effect, index=idx, name="Interaction Effect"),
    }

    logger.info(
        f"SDA complete: demand={demand_effect.sum():.1f}, "
        f"tech={technology_effect.sum():.1f}, "
        f"interaction={interaction_effect.sum():.1f}"
    )
    return result


def structural_decomposition_polar(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    f_0: pd.Series,
    f_1: pd.Series,
) -> Dict[str, pd.Series]:
    """Two-polar average decomposition (eliminates interaction term).

    Δx = ½[L⁰·Δf + ΔL·f¹] + ½[L¹·Δf + ΔL·f⁰]

    This averages the two possible orderings of the decomposition,
    distributing the interaction term equally between demand and technology.

    Args:
        A_0: Direct requirements matrix, period 0.
        A_1: Direct requirements matrix, period 1.
        f_0: Final demand vector, period 0.
        f_1: Final demand vector, period 1.

    Returns:
        Dict with keys: total_change, demand_effect, technology_effect.
    """
    L_0 = _leontief_inverse(A_0.values)
    L_1 = _leontief_inverse(A_1.values)

    delta_f = f_1.values - f_0.values
    delta_L = L_1 - L_0

    # Polar decomposition 1: L⁰ for demand, f¹ for technology
    demand_1 = L_0 @ delta_f
    tech_1 = delta_L @ f_1.values

    # Polar decomposition 2: L¹ for demand, f⁰ for technology
    demand_2 = L_1 @ delta_f
    tech_2 = delta_L @ f_0.values

    # Average
    demand_effect = 0.5 * (demand_1 + demand_2)
    technology_effect = 0.5 * (tech_1 + tech_2)
    total_change = demand_effect + technology_effect

    idx = A_0.index

    return {
        "total_change": pd.Series(total_change, index=idx, name="Total Change"),
        "demand_effect": pd.Series(demand_effect, index=idx, name="Final Demand Effect"),
        "technology_effect": pd.Series(technology_effect, index=idx, name="Technology Effect"),
    }


def sda_summary(decomp: Dict[str, pd.Series]) -> pd.DataFrame:
    """Create a summary DataFrame from SDA results.

    Args:
        decomp: Output from structural_decomposition_3term or _polar.

    Returns:
        DataFrame with sectors as rows and effects as columns,
        plus percentage contribution columns.
    """
    df = pd.DataFrame(decomp)
    total = df["total_change"]

    # Add percentage contributions (avoid division by zero)
    for col in df.columns:
        if col != "total_change":
            pct_col = col.replace("_effect", "_pct")
            df[pct_col] = np.where(
                total != 0,
                (df[col] / total) * 100,
                0,
            )

    return df.sort_values("total_change", ascending=False)


def sda_4term(
    A_dom_0: pd.DataFrame,
    A_dom_1: pd.DataFrame,
    A_imp_0: pd.DataFrame,
    A_imp_1: pd.DataFrame,
    f_0: pd.Series,
    f_1: pd.Series,
) -> Dict[str, pd.Series]:
    """Four-term structural decomposition separating import substitution.

    Decomposes output change into:
    - Demand effect (change in final demand level and composition)
    - Domestic technology effect (change in domestic A matrix)
    - Import substitution effect (shift between domestic and imported inputs)
    - Interaction effect

    Uses the Dietzenbacher-Los (1998) polar average method.

    Args:
        A_dom_0/1: Domestic direct requirements matrix, periods 0 and 1.
        A_imp_0/1: Import direct requirements matrix, periods 0 and 1.
        f_0/f_1: Final demand vectors.

    Returns:
        Dict with demand_effect, technology_effect, import_substitution_effect,
        interaction_effect, total_change.
    """
    L_dom_0 = _leontief_inverse(A_dom_0.values)
    L_dom_1 = _leontief_inverse(A_dom_1.values)

    delta_f = f_1.values - f_0.values
    delta_L = L_dom_1 - L_dom_0

    # Import substitution: change in import coefficients
    delta_A_imp = A_imp_1.values - A_imp_0.values

    # Polar decomposition 1
    demand_1 = L_dom_1 @ delta_f
    tech_1 = delta_L @ f_0.values
    import_sub_1 = L_dom_1 @ delta_A_imp @ L_dom_0 @ f_0.values

    # Polar decomposition 2
    demand_2 = L_dom_0 @ delta_f
    tech_2 = delta_L @ f_1.values
    import_sub_2 = L_dom_0 @ delta_A_imp @ L_dom_1 @ f_1.values

    demand_effect = 0.5 * (demand_1 + demand_2)
    technology_effect = 0.5 * (tech_1 + tech_2)
    import_sub_effect = 0.5 * (import_sub_1 + import_sub_2)

    total_change = demand_effect + technology_effect + import_sub_effect
    interaction = (L_dom_1 @ f_1.values - L_dom_0 @ f_0.values) - total_change

    idx = A_dom_0.index

    return {
        "total_change": pd.Series(
            L_dom_1 @ f_1.values - L_dom_0 @ f_0.values, index=idx, name="Total Change"
        ),
        "demand_effect": pd.Series(demand_effect, index=idx, name="Demand Effect"),
        "technology_effect": pd.Series(technology_effect, index=idx, name="Technology Effect"),
        "import_substitution_effect": pd.Series(
            import_sub_effect, index=idx, name="Import Substitution Effect"
        ),
        "interaction_effect": pd.Series(interaction, index=idx, name="Interaction Effect"),
    }


def sda_average_all_orderings(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    f_0: pd.Series,
    f_1: pd.Series,
) -> Dict[str, pd.Series]:
    """Full Dietzenbacher-Los average over all decomposition orderings.

    For a 2-factor decomposition (L and f), there are 2! = 2 orderings.
    This averages both orderings exactly, which is equivalent to the
    polar decomposition but generalizable to more factors.

    This implementation provides the exact D&I formula for the 2-factor
    case and serves as the template for higher-order decompositions.

    Args:
        A_0/A_1: Direct requirements matrices.
        f_0/f_1: Final demand vectors.

    Returns:
        Dict with demand_effect, technology_effect (no interaction term).
    """
    L_0 = _leontief_inverse(A_0.values)
    L_1 = _leontief_inverse(A_1.values)

    delta_f = f_1.values - f_0.values
    delta_L = L_1 - L_0

    # All orderings for 2-factor decomposition:
    # Order 1: L changes first → demand at L1 weights, tech at f0 weights
    # Order 2: f changes first → demand at L0 weights, tech at f1 weights
    demand_effect = 0.5 * (L_0 @ delta_f + L_1 @ delta_f)
    technology_effect = 0.5 * (delta_L @ f_0.values + delta_L @ f_1.values)

    idx = A_0.index

    return {
        "total_change": pd.Series(
            L_1 @ f_1.values - L_0 @ f_0.values, index=idx, name="Total Change"
        ),
        "demand_effect": pd.Series(demand_effect, index=idx, name="Demand Effect"),
        "technology_effect": pd.Series(technology_effect, index=idx, name="Technology Effect"),
    }
