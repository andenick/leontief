"""Structural change indices for tracking economic transformation over time.

Implements:
- Lilien turbulence index (dispersion of sectoral growth)
- Cosine similarity of A matrices
- Sector concentration (HHI of multipliers)
- Absolute structural change metric

Reference: Pasinetti (1981) — from Wynne KB.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def lilien_index(output_0: pd.Series, output_1: pd.Series) -> float:
    """Lilien (1982) structural turbulence index.

    σ = √[Σ sᵢ (Δlog(xᵢ) - Δlog(X))²]

    Where sᵢ = share of sector i in total output.
    Higher values indicate more sectoral reallocation.
    """
    common = output_0.index.intersection(output_1.index)
    x0 = output_0.reindex(common).replace(0, np.nan)
    x1 = output_1.reindex(common).replace(0, np.nan)

    growth = np.log(x1 / x0).dropna()
    shares = (x0 / x0.sum()).reindex(growth.index)
    agg_growth = (shares * growth).sum()

    sigma = np.sqrt((shares * (growth - agg_growth) ** 2).sum())
    return float(sigma)


def cosine_similarity(A_0: pd.DataFrame, A_1: pd.DataFrame) -> float:
    """Cosine similarity between two A matrices (flattened).

    Returns value between 0 (completely different) and 1 (identical).
    """
    common_rows = A_0.index.intersection(A_1.index)
    common_cols = A_0.columns.intersection(A_1.columns)
    v0 = A_0.loc[common_rows, common_cols].values.flatten()
    v1 = A_1.loc[common_rows, common_cols].values.flatten()

    dot = np.dot(v0, v1)
    norm0 = np.linalg.norm(v0)
    norm1 = np.linalg.norm(v1)
    if norm0 == 0 or norm1 == 0:
        return 0.0
    return float(dot / (norm0 * norm1))


def absolute_structural_change(A_0: pd.DataFrame, A_1: pd.DataFrame) -> float:
    """Mean absolute change in A matrix coefficients.

    Δ = (1/n²) × Σᵢⱼ |a¹ᵢⱼ - a⁰ᵢⱼ|
    """
    common_rows = A_0.index.intersection(A_1.index)
    common_cols = A_0.columns.intersection(A_1.columns)
    diff = (A_1.loc[common_rows, common_cols] - A_0.loc[common_rows, common_cols]).abs()
    return float(diff.values.mean())


def multiplier_concentration(multipliers: pd.Series) -> float:
    """HHI of output multipliers — measures concentration of economic linkages.

    HHI = Σ (mᵢ / Σmⱼ)²

    Higher HHI = more concentrated (few dominant sectors drive the economy).
    """
    shares = multipliers / multipliers.sum()
    return float((shares ** 2).sum())


def sector_classification_evolution(
    linkage_data: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Track how sectors' linkage classifications change over time.

    Args:
        linkage_data: dict of year -> DataFrame with 'sector_type' column
            (from enhanced_linkages.enhanced_linkage_indices).

    Returns:
        DataFrame with sector × year, showing classification at each point.
    """
    years = sorted(linkage_data.keys())
    all_sectors = set()
    for df in linkage_data.values():
        all_sectors.update(df.index.tolist())

    rows = []
    for sector in sorted(all_sectors):
        row = {"sector": sector}
        for year in years:
            df = linkage_data[year]
            if sector in df.index:
                row[year] = df.loc[sector, "sector_type"]
            else:
                row[year] = "Not available"
        rows.append(row)

    return pd.DataFrame(rows).set_index("sector")
