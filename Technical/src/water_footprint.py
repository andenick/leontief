"""Water footprint analysis via I-O satellite accounts.

Extends the Leontief inverse with water-use satellite vectors to compute
total (direct + indirect) water consumption per sector.

Reference: Miller & Blair (2009/2022), Ch. 10; Hoekstra et al. (2011).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def water_intensity_coefficients(
    water_by_sector: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Compute direct water use per unit output.

    Args:
        water_by_sector: Water withdrawals by sector (million gallons, m3, etc.).
        total_output: Total output by sector (millions of dollars).

    Returns:
        Series of water intensity coefficients.
    """
    common = water_by_sector.index.intersection(total_output.index)
    w = water_by_sector.reindex(common).fillna(0)
    x = total_output.reindex(common).fillna(0).replace(0, np.nan)
    result = (w / x).fillna(0)
    result.name = "water_intensity"
    return result


def embodied_water(
    A: pd.DataFrame,
    water_coeff: pd.Series,
) -> pd.Series:
    """Compute total embodied water per unit output.

    W = w' * (I - A)^(-1)

    Args:
        A: Direct requirements matrix.
        water_coeff: Direct water intensity per unit output.

    Returns:
        Series of total embodied water by sector.
    """
    n = A.shape[0]
    w = water_coeff.reindex(A.index).fillna(0).values
    L = linalg.inv(np.eye(n) - A.values)
    total = w @ L
    result = pd.Series(total, index=A.index, name="embodied_water")
    logger.info(f"Embodied water: mean={result.mean():.6f}")
    return result


def water_multipliers(
    L: pd.DataFrame,
    water_coeff: pd.Series,
) -> pd.Series:
    """Compute water multipliers (total water per unit final demand).

    Args:
        L: Leontief inverse matrix.
        water_coeff: Direct water intensity.

    Returns:
        Series of water multipliers by sector.
    """
    w = water_coeff.reindex(L.index).fillna(0).values
    mult = w @ L.values
    return pd.Series(mult, index=L.columns, name="water_multiplier")


def water_footprint_of_final_demand(
    L: pd.DataFrame,
    water_coeff: pd.Series,
    final_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Attribute water use to final demand categories.

    Args:
        L: Leontief inverse.
        water_coeff: Direct water intensity.
        final_demand: DataFrame with FD categories as columns.

    Returns:
        Sectors x FD categories matrix of attributed water use.
    """
    w = water_coeff.reindex(L.index).fillna(0).values
    w_embodied = w @ L.values

    results = {}
    for col in final_demand.columns:
        f_k = final_demand[col].reindex(L.columns).fillna(0).values
        results[col] = w_embodied * f_k

    result = pd.DataFrame(results, index=L.columns)
    result["total"] = result.sum(axis=1)
    return result


def water_risk_index(
    water_coeff: pd.Series,
    L: pd.DataFrame,
    water_stress: pd.Series,
) -> pd.Series:
    """Compute supply-chain water risk index.

    Weights embodied water by the water stress level of each
    supplying sector's region/basin.

    Args:
        water_coeff: Direct water intensity.
        L: Leontief inverse.
        water_stress: Water stress score (0-1) by sector.

    Returns:
        Series of water risk scores by sector.
    """
    w = water_coeff.reindex(L.index).fillna(0).values
    s = water_stress.reindex(L.index).fillna(0).values

    # Stress-weighted water intensity
    ws = w * s
    risk = ws @ L.values

    result = pd.Series(risk, index=L.columns, name="water_risk_index")
    return result.sort_values(ascending=False)


def virtual_water_trade(
    L: pd.DataFrame,
    water_coeff: pd.Series,
    exports: pd.Series,
    imports: pd.Series,
) -> pd.DataFrame:
    """Compute virtual water in trade flows.

    Virtual water exports = embodied water * export volume
    Virtual water imports = embodied water * import volume (approximate)

    Args:
        L: Leontief inverse.
        water_coeff: Direct water intensity.
        exports: Export values by sector.
        imports: Import values by sector.

    Returns:
        DataFrame with virtual_water_exports, virtual_water_imports, net_virtual_water.
    """
    w = water_coeff.reindex(L.index).fillna(0).values
    w_embodied = w @ L.values

    e = exports.reindex(L.columns).fillna(0).values
    m = imports.reindex(L.columns).fillna(0).values

    vw_exports = w_embodied * e
    vw_imports = w_embodied * m

    return pd.DataFrame({
        "embodied_water": w_embodied,
        "virtual_water_exports": vw_exports,
        "virtual_water_imports": vw_imports,
        "net_virtual_water": vw_exports - vw_imports,
    }, index=L.columns)
