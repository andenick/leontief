"""Carbon Border Adjustment Mechanism (CBAM) simulator.

Computes embodied carbon in trade flows and simulates the competitive
effects of equalizing domestic and imported carbon prices.

Reference: EU CBAM Regulation (2023); Böhringer et al. (2022).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def _estimate_carbon_proxy(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
) -> pd.Series:
    """Estimate carbon intensity proxy from energy-sector linkages.

    Uses the sum of A-matrix coefficients from energy-like sectors
    as a proxy for carbon intensity when satellite data is unavailable.
    """
    sectors = A.index
    energy_prefixes = ["211", "22", "324", "486"]
    energy_sectors = [s for s in sectors if any(str(s).startswith(p) for p in energy_prefixes)]

    if not energy_sectors:
        return pd.Series(0.01, index=sectors, name="carbon_proxy")

    carbon_proxy = A.loc[energy_sectors].sum(axis=0).reindex(sectors).fillna(0)
    carbon_proxy.name = "carbon_proxy"
    return carbon_proxy


def embodied_carbon_in_imports(
    A_domestic: pd.DataFrame,
    A_import: pd.DataFrame,
    carbon_coeff: Optional[pd.Series] = None,
    value_added: Optional[pd.DataFrame] = None,
    total_output: Optional[pd.Series] = None,
) -> pd.Series:
    """Estimate embodied carbon in imports by sector.

    Uses domestic carbon intensities applied to import structure
    (assumes similar technology — conservative upper bound).

    Args:
        A_domestic: Domestic A matrix.
        A_import: Import A matrix.
        carbon_coeff: Carbon intensity (if available from satellite).
        value_added: VA DataFrame (for proxy if no carbon_coeff).
        total_output: Total output (for proxy).

    Returns:
        Series of embodied carbon in imports per unit output.
    """
    sectors = A_domestic.index
    n = len(sectors)

    if carbon_coeff is None:
        carbon_coeff = _estimate_carbon_proxy(A_domestic, value_added, total_output)

    c = carbon_coeff.reindex(sectors).fillna(0).values
    A_imp = A_import.loc[sectors, sectors].fillna(0).values

    L_dom = linalg.inv(np.eye(n) - A_domestic.loc[sectors, sectors].values)
    import_carbon = c @ L_dom @ A_imp

    return pd.Series(import_carbon, index=sectors, name="embodied_carbon_imports")


def cbam_price_adjustment(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
    carbon_coeff: Optional[pd.Series] = None,
    carbon_price_per_unit: float = 50.0,
) -> pd.DataFrame:
    """Simulate domestic carbon pricing at CBAM rate.

    Adds carbon cost to VA coefficients and computes cost-push price impact.

    Args:
        A: Direct requirements matrix.
        value_added: VA DataFrame.
        total_output: Total output.
        carbon_coeff: Carbon intensity by sector.
        carbon_price_per_unit: Carbon price ($/unit of carbon proxy).

    Returns:
        DataFrame with baseline_price, carbon_price, increase_pct.
    """
    sectors = A.index
    n = len(sectors)

    if carbon_coeff is None:
        carbon_coeff = _estimate_carbon_proxy(A, value_added, total_output)

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0)
    else:
        va = value_added.reindex(sectors).fillna(0)

    x = total_output.reindex(sectors).fillna(0)
    va_coeff = (va / x.replace(0, np.nan)).fillna(0).values
    c = carbon_coeff.reindex(sectors).fillna(0).values

    L = linalg.inv(np.eye(n) - A.values)
    p_baseline = va_coeff @ L

    va_coeff_carbon = va_coeff + c * carbon_price_per_unit
    p_carbon = va_coeff_carbon @ L

    increase = p_carbon - p_baseline
    increase_pct = np.where(p_baseline > 1e-10, increase / p_baseline * 100, 0)

    return pd.DataFrame({
        "baseline_price": p_baseline,
        "carbon_adjusted_price": p_carbon,
        "price_increase": increase,
        "price_increase_pct": increase_pct,
        "direct_carbon_intensity": c,
    }, index=sectors).sort_values("price_increase_pct", ascending=False)


def cbam_winners_losers(
    use_table: pd.DataFrame,
    total_output: pd.Series,
    value_added: pd.DataFrame,
    carbon_coeff: Optional[pd.Series] = None,
    carbon_price: float = 50.0,
) -> pd.DataFrame:
    """Identify sectors gaining/losing competitiveness under CBAM.

    Sectors where import carbon > domestic carbon gain (imports penalized more).

    Args:
        use_table: Full Use table.
        total_output: Total output.
        value_added: VA DataFrame.
        carbon_coeff: Carbon intensity.
        carbon_price: Carbon price per unit.

    Returns:
        DataFrame with domestic_carbon, import_carbon, competitive_effect.
    """
    from import_analysis import split_use_table

    Z_dom, Z_imp = split_use_table(use_table)
    sectors = Z_dom.index.intersection(Z_dom.columns)

    x = total_output.reindex(sectors).replace(0, np.nan)
    A_dom = Z_dom.loc[sectors, sectors].div(x, axis=1).fillna(0)
    A_imp = Z_imp.loc[sectors, sectors].div(x, axis=1).fillna(0)

    if carbon_coeff is None:
        carbon_coeff = _estimate_carbon_proxy(A_dom, value_added, total_output)

    n = len(sectors)
    c = carbon_coeff.reindex(sectors).fillna(0).values
    L_dom = linalg.inv(np.eye(n) - A_dom.values)

    domestic_embodied = c @ L_dom
    import_embodied = c @ L_dom @ A_imp.values

    net_effect = import_embodied - domestic_embodied

    return pd.DataFrame({
        "domestic_carbon": domestic_embodied,
        "import_carbon": import_embodied,
        "net_competitive_effect": net_effect,
        "cbam_benefit": net_effect > 0,
        "domestic_cost_increase": domestic_embodied * carbon_price,
        "import_cost_increase": import_embodied * carbon_price,
    }, index=sectors).sort_values("net_competitive_effect", ascending=False)
