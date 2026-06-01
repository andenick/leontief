"""Enhanced linkage analysis with coefficient of variation weighting.

Extends the basic Rasmussen indices with:
- Coefficient of variation (CV) weighting for identifying truly key sectors
- Hirschman classification with spread metrics
- Hypothetical extraction-based linkage measures

Reference: Miller & Blair (2009), Ch. 12 — from Wynne KB.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def enhanced_linkage_indices(L: pd.DataFrame) -> pd.DataFrame:
    """Calculate Rasmussen indices with coefficient of variation.

    Standard Rasmussen indices identify sectors with above-average linkages,
    but don't distinguish between sectors with concentrated effects (one big
    supplier) vs diffuse effects (many small suppliers). The CV captures this.

    Args:
        L: Leontief inverse matrix (n x n).

    Returns:
        DataFrame with columns: backward_linkage, forward_linkage,
        backward_index, forward_index, backward_cv, forward_cv,
        sector_type.
    """
    n = L.shape[0]
    L_vals = L.values
    grand_mean = L_vals.sum() / (n * n)

    # Backward linkages (column-based)
    col_means = L_vals.mean(axis=0)
    backward_index = col_means / grand_mean

    # Forward linkages (row-based)
    row_means = L_vals.mean(axis=1)
    forward_index = row_means / grand_mean

    # Coefficient of variation (spread of effects)
    backward_cv = np.zeros(n)
    forward_cv = np.zeros(n)
    for j in range(n):
        col = L_vals[:, j]
        backward_cv[j] = col.std() / col.mean() if col.mean() > 0 else 0

        row = L_vals[j, :]
        forward_cv[j] = row.std() / row.mean() if row.mean() > 0 else 0

    # Classify sectors
    sector_types = []
    for i in range(n):
        bi = backward_index[i]
        fi = forward_index[i]
        if bi > 1 and fi > 1:
            sector_types.append("Key sector")
        elif bi > 1:
            sector_types.append("Backward-oriented")
        elif fi > 1:
            sector_types.append("Forward-oriented")
        else:
            sector_types.append("Weak linkage")

    result = pd.DataFrame({
        "backward_linkage": L_vals.sum(axis=0),
        "forward_linkage": L_vals.sum(axis=1),
        "backward_index": backward_index,
        "forward_index": forward_index,
        "backward_cv": backward_cv,
        "forward_cv": forward_cv,
        "sector_type": sector_types,
    }, index=L.index)

    counts = result["sector_type"].value_counts()
    logger.info(f"Sector classification: {counts.to_dict()}")
    return result


def power_of_dispersion(L: pd.DataFrame) -> pd.Series:
    """Rasmussen's power of dispersion (normalized backward linkage).

    U_j = (1/n) × Σᵢ lᵢⱼ / (1/n²) × ΣᵢΣⱼ lᵢⱼ

    A value > 1 means sector j draws more heavily on the economy
    than an average sector.
    """
    n = L.shape[0]
    col_sums = L.values.sum(axis=0)
    grand_sum = L.values.sum()
    return pd.Series(
        n * col_sums / grand_sum,
        index=L.columns,
        name="power_of_dispersion",
    )


def sensitivity_of_dispersion(L: pd.DataFrame) -> pd.Series:
    """Rasmussen's sensitivity of dispersion (normalized forward linkage).

    U_i = (1/n) × Σⱼ lᵢⱼ / (1/n²) × ΣᵢΣⱼ lᵢⱼ

    A value > 1 means sector i is drawn upon more heavily by
    the rest of the economy than average.
    """
    n = L.shape[0]
    row_sums = L.values.sum(axis=1)
    grand_sum = L.values.sum()
    return pd.Series(
        n * row_sums / grand_sum,
        index=L.index,
        name="sensitivity_of_dispersion",
    )


def extraction_based_linkages(
    A: pd.DataFrame,
    x: pd.Series,
    f: pd.Series,
) -> pd.DataFrame:
    """Calculate total linkage via hypothetical extraction for all sectors.

    For each sector k, extract it (zero out row k and column k in A),
    re-solve the system, and measure total output loss.

    Args:
        A: Direct requirements matrix.
        x: Total output vector.
        f: Final demand vector.

    Returns:
        DataFrame with absolute and relative extraction impacts.
    """
    n = A.shape[0]
    total_output = x.sum()
    results = []

    for k in range(n):
        A_mod = A.values.copy()
        A_mod[k, :] = 0
        A_mod[:, k] = 0

        try:
            L_mod = linalg.inv(np.eye(n) - A_mod)
            x_mod = L_mod @ f.values
            output_loss = x.values.sum() - x_mod.sum()
            loss_pct = (output_loss / total_output) * 100
        except linalg.LinAlgError:
            output_loss = np.nan
            loss_pct = np.nan

        results.append({
            "sector": A.index[k],
            "output_loss": output_loss,
            "loss_pct": loss_pct,
        })

    df = pd.DataFrame(results).set_index("sector")
    df = df.sort_values("loss_pct", ascending=False)

    logger.info(f"Extraction linkages: top sector = {df.index[0]} ({df['loss_pct'].iloc[0]:.1f}%)")
    return df
