"""Innovation propagation speed through I-O networks.

Measures how many Leontief power-series iterations (A, A^2, A^3, ...)
are needed for a productivity shock to reach 90% of its total effect.
Faster propagation = more tightly coupled economy.

Reference: Acemoglu et al. (2012); Miller & Blair Ch. 2.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def leontief_power_series_convergence(
    A: pd.DataFrame,
    n_terms: int = 50,
) -> pd.DataFrame:
    """Compute cumulative Leontief power series: L = I + A + A^2 + ...

    Args:
        A: Direct requirements matrix.
        n_terms: Number of power series terms to compute.

    Returns:
        DataFrame with term, cumulative_sum, pct_of_L_total per term.
    """
    n = A.shape[0]
    A_vals = A.values
    L = linalg.inv(np.eye(n) - A_vals)
    L_total = L.sum()

    cumsum = np.eye(n)
    power = np.eye(n)
    rows = [{"term": 0, "cumulative_sum": float(cumsum.sum()), "pct_of_L_total": float(cumsum.sum() / L_total * 100)}]

    for k in range(1, n_terms + 1):
        power = power @ A_vals
        cumsum = cumsum + power
        pct = cumsum.sum() / L_total * 100

        rows.append({
            "term": k,
            "cumulative_sum": float(cumsum.sum()),
            "pct_of_L_total": float(pct),
        })

        if pct > 99.99:
            break

    return pd.DataFrame(rows).set_index("term")


def propagation_depth_by_sector(
    A: pd.DataFrame,
    threshold_pct: float = 90.0,
) -> pd.Series:
    """Compute how many A-power iterations to reach threshold% of total effect.

    For sector j: find smallest k such that
    (I + A + ... + A^k)[:,j].sum() / L[:,j].sum() >= threshold_pct/100.

    Args:
        A: Direct requirements matrix.
        threshold_pct: Convergence threshold (default 90%).

    Returns:
        Series of propagation depths indexed by sector. Lower = faster propagation.
    """
    n = A.shape[0]
    A_vals = A.values
    L = linalg.inv(np.eye(n) - A_vals)
    L_col_sums = L.sum(axis=0)

    threshold = threshold_pct / 100.0
    depths = np.full(n, -1, dtype=int)

    cumsum = np.eye(n)
    power = np.eye(n)

    for k in range(1, n + 20):
        power = power @ A_vals
        cumsum = cumsum + power
        col_sums = cumsum.sum(axis=0)

        for j in range(n):
            if depths[j] == -1 and L_col_sums[j] > 0:
                if col_sums[j] / L_col_sums[j] >= threshold:
                    depths[j] = k

        if np.all(depths >= 0):
            break

    depths[depths == -1] = k
    result = pd.Series(depths, index=A.index, name="propagation_depth")

    logger.info(f"Propagation depth: mean={result.mean():.1f}, range=[{result.min()}, {result.max()}]")
    return result


def propagation_speed_matrix(
    A: pd.DataFrame,
    threshold_pct: float = 50.0,
    max_steps: int = 20,
) -> pd.DataFrame:
    """Compute pairwise propagation speed: steps for shock in i to reach j.

    Args:
        A: Direct requirements matrix.
        threshold_pct: Fraction of total effect to reach.
        max_steps: Maximum steps to track.

    Returns:
        n x n DataFrame of propagation steps (i -> j).
    """
    n = A.shape[0]
    A_vals = A.values
    L = linalg.inv(np.eye(n) - A_vals)

    threshold = threshold_pct / 100.0
    speed = np.full((n, n), max_steps, dtype=int)

    cumsum = np.eye(n)
    power = np.eye(n)

    for k in range(1, max_steps + 1):
        power = power @ A_vals
        cumsum = cumsum + power

        for i in range(n):
            for j in range(n):
                if speed[i, j] == max_steps and L[i, j] > 1e-10:
                    if cumsum[i, j] / L[i, j] >= threshold:
                        speed[i, j] = k

    return pd.DataFrame(speed, index=A.index, columns=A.columns)


def innovation_propagation_timeseries(
    data_by_year: Dict[int, dict],
    threshold_pct: float = 90.0,
) -> pd.DataFrame:
    """Track mean propagation depth across years.

    Args:
        data_by_year: Dict of year -> data dict.
        threshold_pct: Convergence threshold.

    Returns:
        DataFrame with year, mean_depth, std_depth, min_depth, max_depth.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        A = data_by_year[year].get("A_matrix")
        if A is None or A.empty:
            continue
        depths = propagation_depth_by_sector(A, threshold_pct)
        rows.append({
            "year": year,
            "mean_depth": float(depths.mean()),
            "std_depth": float(depths.std()),
            "min_depth": int(depths.min()),
            "max_depth": int(depths.max()),
            "median_depth": float(depths.median()),
        })

    return pd.DataFrame(rows).set_index("year")
