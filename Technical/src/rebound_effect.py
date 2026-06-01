"""Rebound effect estimation via I-O analysis.

When a sector improves energy efficiency, the cost reduction stimulates
output growth through the I-O system, partially offsetting the savings.

Reference: Saunders (2000); Turner (2009).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def energy_efficiency_shock(
    A: pd.DataFrame,
    energy_sector: str,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    efficiency_gain_pct: float = 10.0,
) -> Dict:
    """Simulate an energy efficiency improvement and compute rebound.

    1. Reduce energy row in A by efficiency_gain_pct
    2. Cost-push price decrease (forward propagation)
    3. Output expansion from price decrease
    4. Additional energy from output expansion
    5. Rebound = additional_energy / direct_energy_saved

    Args:
        A: Direct requirements matrix.
        energy_sector: Sector code for the energy sector.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        efficiency_gain_pct: Efficiency improvement (%).

    Returns:
        Dict with direct_saved, induced_demand, rebound_fraction, net_savings.
    """
    if energy_sector not in A.index:
        return {"error": f"Sector {energy_sector} not found"}

    sectors = A.index
    n = len(sectors)
    k = sectors.get_loc(energy_sector)
    x = total_output.reindex(sectors).fillna(0).values

    # Baseline energy use: A[energy_sector, :] * x (energy inputs to all sectors)
    baseline_energy = A.values[k, :] * x
    total_baseline_energy = baseline_energy.sum()

    # Modified A: reduce energy row by efficiency gain
    A_mod = A.values.copy()
    A_mod[k, :] *= (1 - efficiency_gain_pct / 100)

    # Direct energy savings
    direct_saved = total_baseline_energy * efficiency_gain_pct / 100

    # New equilibrium output (price decrease -> output expansion)
    L_old = linalg.inv(np.eye(n) - A.values)
    L_new = linalg.inv(np.eye(n) - A_mod)

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va = value_added.reindex(sectors).fillna(0)

    va_coeff = (va / pd.Series(x, index=sectors).replace(0, np.nan)).fillna(0).values

    # Price effect: cost-push
    p_old = va_coeff @ L_old
    p_new = va_coeff @ L_new
    price_decrease = p_old - p_new

    # Output expansion (demand elasticity proxy: 1% price decrease -> 0.5% output increase)
    demand_elasticity = 0.5
    output_expansion = x * (price_decrease / np.where(p_old > 0, p_old, 1)) * demand_elasticity

    # Additional energy demand from expanded output
    induced_energy = A_mod[k, :] * output_expansion
    total_induced = induced_energy.sum()

    rebound = total_induced / max(direct_saved, 1e-10)

    return {
        "energy_sector": energy_sector,
        "efficiency_gain_pct": efficiency_gain_pct,
        "direct_energy_saved": float(direct_saved),
        "induced_energy_demand": float(total_induced),
        "net_energy_savings": float(direct_saved - total_induced),
        "rebound_fraction": float(rebound),
        "rebound_pct": float(rebound * 100),
        "mean_price_decrease_pct": float(price_decrease.mean() / max(p_old.mean(), 1e-10) * 100),
    }


def rebound_by_energy_sector(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    energy_sectors: List[str] = None,
    efficiency_gain_pct: float = 10.0,
) -> pd.DataFrame:
    """Compute rebound fraction for each energy-related sector.

    Args:
        A: Direct requirements matrix.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        energy_sectors: List of energy sector codes.
        efficiency_gain_pct: Efficiency gain to simulate.

    Returns:
        DataFrame with rebound metrics per energy sector.
    """
    if energy_sectors is None:
        energy_sectors = [s for s in A.index if any(
            str(s).startswith(p) for p in ["22", "211", "324", "486"]
        )]

    if not energy_sectors:
        energy_sectors = list(A.index[:3])
        logger.warning(f"No energy sectors found; using first 3 sectors as demo")

    rows = []
    for sector in energy_sectors:
        if sector not in A.index:
            continue
        result = energy_efficiency_shock(A, sector, value_added, total_output, efficiency_gain_pct)
        rows.append(result)

    return pd.DataFrame(rows)


def rebound_sensitivity(
    A: pd.DataFrame,
    energy_sector: str,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    gain_range: List[float] = None,
) -> pd.DataFrame:
    """Compute rebound at varying efficiency gains.

    Args:
        A: Direct requirements matrix.
        energy_sector: Energy sector code.
        value_added: VA DataFrame.
        total_output: Total output.
        gain_range: List of efficiency gain percentages to test.

    Returns:
        DataFrame with gain_pct, rebound_pct, net_savings.
    """
    if gain_range is None:
        gain_range = [1, 2, 5, 10, 15, 20, 30, 50]

    rows = []
    for gain in gain_range:
        result = energy_efficiency_shock(A, energy_sector, value_added, total_output, gain)
        rows.append({
            "efficiency_gain_pct": gain,
            "rebound_pct": result.get("rebound_pct", 0),
            "net_savings": result.get("net_energy_savings", 0),
            "direct_saved": result.get("direct_energy_saved", 0),
        })

    return pd.DataFrame(rows)
