"""Stranded asset propagation through I-O supply chains.

Models a forced write-down of fossil fuel sector capital and traces
the economic loss through forward (Ghosh) and backward (Leontief)
propagation channels.

Reference: Mercure et al. (2018); Battiston et al. (2017).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

DEFAULT_FOSSIL = ["211", "324", "486"]


def stranded_asset_shock(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    fossil_sectors: List[str] = None,
    write_down_fraction: float = 0.30,
) -> pd.DataFrame:
    """Simulate a forced asset write-down in fossil fuel sectors.

    Combines forward (supply constraint) and backward (demand loss)
    propagation channels.

    Args:
        A: Direct requirements matrix.
        value_added: VA DataFrame.
        total_output: Total output by sector.
        fossil_sectors: Fossil fuel sector codes.
        write_down_fraction: Fraction of VA written down (0-1).

    Returns:
        DataFrame with sector-level impact assessment.
    """
    if fossil_sectors is None:
        fossil_sectors = [s for s in DEFAULT_FOSSIL if s in A.index]

    sectors = A.index
    n = len(sectors)
    x = total_output.reindex(sectors).fillna(0).values

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0).values
    else:
        va = value_added.reindex(sectors).fillna(0).values

    # Baseline
    L = linalg.inv(np.eye(n) - A.values)
    x_baseline = x.copy()

    # VA shock in fossil sectors
    va_shock = np.zeros(n)
    for s in fossil_sectors:
        if s in sectors:
            k = sectors.get_loc(s)
            va_shock[k] = -va[k] * write_down_fraction

    # Forward propagation: supply constraint via Ghosh
    x_inv = np.where(x > 0, 1.0 / x, 0)
    B = A.values * x[np.newaxis, :] * x_inv[:, np.newaxis]
    try:
        G = linalg.inv(np.eye(n) - B)
        forward_impact = va_shock @ G
    except linalg.LinAlgError:
        forward_impact = np.zeros(n)

    # Backward propagation: demand loss
    va_coeff = np.where(x > 0, va / x, 0)
    demand_loss = va_shock * va_coeff
    backward_impact = L @ demand_loss

    total_impact = forward_impact + backward_impact

    total_baseline = x_baseline.sum()

    return pd.DataFrame({
        "va_shock": va_shock,
        "forward_impact": forward_impact,
        "backward_impact": backward_impact,
        "total_impact": total_impact,
        "impact_pct_of_output": total_impact / np.where(x > 0, x, np.nan) * 100,
    }, index=sectors).fillna(0).sort_values("total_impact")


def stranded_cascade_path(
    A: pd.DataFrame,
    f: pd.Series,
    fossil_sectors: List[str] = None,
    cascade_threshold_pct: float = 20.0,
) -> pd.DataFrame:
    """Run cascade failure starting from fossil sector extraction.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        fossil_sectors: Sectors to extract.
        cascade_threshold_pct: Cascade propagation threshold.

    Returns:
        Cascade log DataFrame from cascade_failure.run_cascade.
    """
    from cascade_failure import run_cascade

    if fossil_sectors is None:
        fossil_sectors = [s for s in DEFAULT_FOSSIL if s in A.index]

    shock = {s: 1.0 for s in fossil_sectors}
    return run_cascade(A, f, shock, cascade_threshold_pct)


def transition_investment_needs(
    A: pd.DataFrame,
    total_output: pd.Series,
    fossil_sectors: List[str] = None,
    renewable_sectors: List[str] = None,
    replacement_ratio: float = 0.5,
) -> Dict[str, float]:
    """Estimate investment needed to replace fossil output with renewables.

    Args:
        A: Direct requirements matrix.
        total_output: Total output by sector.
        fossil_sectors: Sectors being phased out.
        renewable_sectors: Sectors replacing them.
        replacement_ratio: Fraction of fossil output replaced by renewables.

    Returns:
        Dict with fossil_output_lost, replacement_investment, net_output_impact.
    """
    if fossil_sectors is None:
        fossil_sectors = [s for s in DEFAULT_FOSSIL if s in A.index]
    if renewable_sectors is None:
        renewable_sectors = [s for s in A.index if str(s).startswith("22")]

    x = total_output.reindex(A.index).fillna(0)

    fossil_output = sum(x.get(s, 0) for s in fossil_sectors)
    renewable_output = sum(x.get(s, 0) for s in renewable_sectors)

    replacement_needed = fossil_output * replacement_ratio
    # Capital intensity proxy: intermediate inputs / output
    A_vals = A.values
    cap_intensity = A_vals.sum(axis=0).mean()
    investment_needed = replacement_needed * (1 + cap_intensity)

    return {
        "fossil_output_lost": float(fossil_output),
        "replacement_output_needed": float(replacement_needed),
        "estimated_investment": float(investment_needed),
        "current_renewable_output": float(renewable_output),
        "expansion_ratio": float(replacement_needed / max(renewable_output, 1e-10)),
    }
