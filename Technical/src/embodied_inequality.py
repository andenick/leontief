"""Embodied wage inequality analysis via I-O satellite accounts.

Combines the Leontief inverse with BLS wage percentile data to compute
the Gini coefficient of labor income embodied in each final demand category.

Reference: Alsamawi et al. (2014); Timmer et al. (2014).

REQUIRES SATELLITE DATA: BLS OES wage percentiles by industry.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

SATELLITE_DIR = Path(__file__).parent.parent / "data" / "processed" / "satellite"


def load_oes_wage_percentiles(
    filepath: Optional[Path] = None,
) -> Optional[pd.DataFrame]:
    """Load BLS OES wage percentile data crosswalked to I-O sectors.

    Expected format: DataFrame with index=sector_code, columns include
    p10, p25, p50, p75, p90, employment.

    Args:
        filepath: Path to processed OES data. Defaults to satellite dir.

    Returns:
        DataFrame or None if file not found.
    """
    if filepath is None:
        filepath = SATELLITE_DIR / "oes_wages.pkl"

    if not filepath.exists():
        logger.warning(
            f"OES wage data not found at {filepath}. "
            f"Run download_satellite_*.py to acquire BLS OES data."
        )
        return None

    import pickle
    with open(filepath, "rb") as f:
        data = pickle.load(f)

    if isinstance(data, pd.DataFrame):
        return data
    return None


def _gini_from_percentiles(percentiles: np.ndarray) -> float:
    """Approximate Gini coefficient from percentile wages (p10-p90)."""
    if len(percentiles) < 2 or np.all(percentiles == 0):
        return 0.0

    sorted_p = np.sort(percentiles)
    n = len(sorted_p)
    total = sorted_p.sum()
    if total <= 0:
        return 0.0

    cumulative = np.cumsum(sorted_p)
    gini = 1 - 2 * cumulative.sum() / (n * total) + 1 / n
    return max(float(gini), 0.0)


def embodied_wage_distribution(
    L: pd.DataFrame,
    wage_percentiles: pd.DataFrame,
    final_demand_col: pd.Series,
) -> pd.DataFrame:
    """Compute wage distribution embodied in a final demand vector.

    For each percentile: embodied_pXX = pXX_wages × L × f

    Args:
        L: Leontief inverse matrix.
        wage_percentiles: BLS wage percentiles by sector.
        final_demand_col: FD vector for one category.

    Returns:
        DataFrame with percentile-level embodied wages.
    """
    sectors = L.index
    f = final_demand_col.reindex(sectors).fillna(0).values
    f_total = f.sum()
    if f_total <= 0:
        return pd.DataFrame()

    f_unit = f / f_total

    pct_cols = [c for c in wage_percentiles.columns if c.startswith("p")]
    results = {}

    for col in pct_cols:
        w_pct = wage_percentiles[col].reindex(sectors).fillna(0).values
        w_coeff = w_pct / 1e6
        embodied = w_coeff @ L.values @ f_unit
        results[col] = float(embodied)

    return pd.DataFrame([results])


def gini_of_embodied_wages(
    L: pd.DataFrame,
    wage_percentiles: pd.DataFrame,
    final_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Compute Gini of embodied wage income by FD category.

    Args:
        L: Leontief inverse.
        wage_percentiles: BLS wage data by sector.
        final_demand: FD DataFrame with category columns.

    Returns:
        DataFrame with fd_category, gini, mean_wage, p90_p10_ratio.
    """
    rows = []
    for col in final_demand.columns:
        fd_col = final_demand[col]
        dist = embodied_wage_distribution(L, wage_percentiles, fd_col)
        if dist.empty:
            continue

        pct_values = dist.iloc[0].values
        gini = _gini_from_percentiles(pct_values)

        p10 = dist.iloc[0].get("p10", 0)
        p90 = dist.iloc[0].get("p90", 0)

        rows.append({
            "fd_category": str(col),
            "gini_embodied": gini,
            "mean_embodied_wage": float(np.mean(pct_values)),
            "p90_p10_ratio": float(p90 / max(p10, 1e-10)),
        })

    return pd.DataFrame(rows)
