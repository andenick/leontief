"""Embodied energy and carbon intensity analysis via I-O satellite accounts.

Extends the Leontief inverse with energy/emissions satellite vectors to
compute total (direct + indirect) environmental footprints per sector.

Reference: Miller & Blair (2009/2022), Ch. 10; Leontief (1970).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def energy_intensity_coefficients(
    energy_by_sector: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Compute direct energy intensity per unit output.

    Args:
        energy_by_sector: Energy use by sector (TBtu, TJ, or any unit).
        total_output: Total output by sector (millions of dollars).

    Returns:
        Series of energy intensity coefficients (energy/dollar).
    """
    common = energy_by_sector.index.intersection(total_output.index)
    e = energy_by_sector.reindex(common).fillna(0)
    x = total_output.reindex(common).fillna(0).replace(0, np.nan)
    result = (e / x).fillna(0)
    result.name = "energy_intensity"
    return result


def embodied_energy(
    A: pd.DataFrame,
    energy_coeff: pd.Series,
) -> pd.Series:
    """Compute total embodied energy per unit output.

    E = e' * L = e' * (I - A)^(-1)

    Args:
        A: Direct requirements matrix.
        energy_coeff: Direct energy intensity per unit output.

    Returns:
        Series of total (direct + indirect) energy per unit output.
    """
    n = A.shape[0]
    e = energy_coeff.reindex(A.index).fillna(0).values
    L = linalg.inv(np.eye(n) - A.values)
    total = e @ L
    result = pd.Series(total, index=A.index, name="embodied_energy")
    logger.info(f"Embodied energy: mean={result.mean():.6f}")
    return result


def energy_multipliers(
    L: pd.DataFrame,
    energy_coeff: pd.Series,
) -> pd.Series:
    """Compute energy multipliers (total energy per unit final demand).

    Args:
        L: Leontief inverse matrix.
        energy_coeff: Direct energy intensity per unit output.

    Returns:
        Series of energy multipliers by sector.
    """
    e = energy_coeff.reindex(L.index).fillna(0).values
    mult = e @ L.values
    result = pd.Series(mult, index=L.columns, name="energy_multiplier")
    return result


def carbon_intensity_coefficients(
    emissions_by_sector: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Compute direct carbon intensity per unit output.

    Args:
        emissions_by_sector: GHG emissions by sector (tCO2e or MtCO2e).
        total_output: Total output by sector.

    Returns:
        Series of carbon intensity coefficients.
    """
    common = emissions_by_sector.index.intersection(total_output.index)
    c = emissions_by_sector.reindex(common).fillna(0)
    x = total_output.reindex(common).fillna(0).replace(0, np.nan)
    result = (c / x).fillna(0)
    result.name = "carbon_intensity"
    return result


def embodied_carbon(
    A: pd.DataFrame,
    carbon_coeff: pd.Series,
) -> pd.Series:
    """Compute total embodied carbon per unit output.

    Args:
        A: Direct requirements matrix.
        carbon_coeff: Direct carbon intensity per unit output.

    Returns:
        Series of total embodied carbon by sector.
    """
    n = A.shape[0]
    c = carbon_coeff.reindex(A.index).fillna(0).values
    L = linalg.inv(np.eye(n) - A.values)
    total = c @ L
    result = pd.Series(total, index=A.index, name="embodied_carbon")
    logger.info(f"Embodied carbon: mean={result.mean():.6f}")
    return result


def carbon_footprint_of_final_demand(
    L: pd.DataFrame,
    carbon_coeff: pd.Series,
    final_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Attribute carbon emissions to final demand categories.

    For each FD category (consumption, investment, exports, government):
    emissions_k = c' * L * f_k

    Args:
        L: Leontief inverse.
        carbon_coeff: Direct carbon intensity.
        final_demand: DataFrame with FD categories as columns.

    Returns:
        DataFrame: sectors x FD categories, values = attributed emissions.
    """
    c = carbon_coeff.reindex(L.index).fillna(0).values
    c_embodied = c @ L.values

    results = {}
    for col in final_demand.columns:
        f_k = final_demand[col].reindex(L.columns).fillna(0).values
        results[col] = c_embodied * f_k

    result = pd.DataFrame(results, index=L.columns)
    result["total"] = result.sum(axis=1)
    return result


def decarbonization_attribution(
    carbon_coeff_0: pd.Series,
    carbon_coeff_1: pd.Series,
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    f_0: pd.Series,
    f_1: pd.Series,
) -> Dict[str, pd.Series]:
    """Decompose carbon emissions change into technology, demand, and emission coefficient effects.

    Uses polar SDA approach:
    delta_E = effect_of(delta_c) + effect_of(delta_A) + effect_of(delta_f)

    Args:
        carbon_coeff_0/1: Carbon intensity in periods 0 and 1.
        A_0/A_1: Direct requirements matrices.
        f_0/f_1: Final demand vectors.

    Returns:
        Dict with emission_coefficient_effect, technology_effect, demand_effect.
    """
    n = A_0.shape[0]
    sectors = A_0.index

    c0 = carbon_coeff_0.reindex(sectors).fillna(0).values
    c1 = carbon_coeff_1.reindex(sectors).fillna(0).values
    L0 = linalg.inv(np.eye(n) - A_0.values)
    L1 = linalg.inv(np.eye(n) - A_1.values)
    fv0 = f_0.reindex(sectors).fillna(0).values
    fv1 = f_1.reindex(sectors).fillna(0).values

    # Polar decomposition (average of two orderings)
    dc = c1 - c0
    dL = L1 - L0
    df = fv1 - fv0

    # Ordering 1: c changes first, then L, then f
    emission_1 = dc @ L0 @ fv0
    tech_1 = c1 @ dL @ fv0
    demand_1 = c1 @ L1 @ df

    # Ordering 2: f changes first, then L, then c
    demand_2 = c0 @ L0 @ df
    tech_2 = c0 @ dL @ fv1
    emission_2 = dc @ L1 @ fv1

    emission_effect = 0.5 * (emission_1 + emission_2)
    tech_effect = 0.5 * (tech_1 + tech_2)
    demand_effect = 0.5 * (demand_1 + demand_2)

    return {
        "emission_coefficient_effect": float(emission_effect),
        "technology_effect": float(tech_effect),
        "demand_effect": float(demand_effect),
        "total_change": float(emission_effect + tech_effect + demand_effect),
    }


def environmental_multiplier_summary(
    A: pd.DataFrame,
    energy_coeff: Optional[pd.Series] = None,
    carbon_coeff: Optional[pd.Series] = None,
    total_output: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Summary table of all environmental multipliers.

    Args:
        A: Direct requirements matrix.
        energy_coeff: Direct energy intensity (optional).
        carbon_coeff: Direct carbon intensity (optional).
        total_output: Total output for weighting (optional).

    Returns:
        DataFrame with direct and embodied intensities by sector.
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)

    result = pd.DataFrame(index=A.index)

    if energy_coeff is not None:
        e = energy_coeff.reindex(A.index).fillna(0)
        result["direct_energy"] = e
        result["embodied_energy"] = e.values @ L
        if total_output is not None:
            x = total_output.reindex(A.index).fillna(0)
            result["total_energy_use"] = result["embodied_energy"] * x

    if carbon_coeff is not None:
        c = carbon_coeff.reindex(A.index).fillna(0)
        result["direct_carbon"] = c
        result["embodied_carbon"] = c.values @ L
        if total_output is not None:
            x = total_output.reindex(A.index).fillna(0)
            result["total_carbon_emissions"] = result["embodied_carbon"] * x

    return result.sort_values(result.columns[-1], ascending=False)
