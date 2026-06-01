"""Spectral gap and mixing time analysis of the I-O matrix.

The spectral gap (lambda_1 - |lambda_2|) determines how quickly shocks
dissipate through the production network. A large gap means one dominant
mode and fast equilibration; a small gap means persistent, concentrated effects.

Reference: Acemoglu et al. (2012); Carvalho (2014).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def spectral_gap(A: pd.DataFrame) -> Dict[str, float]:
    """Compute eigenvalue spectrum and spectral gap of the A matrix.

    Args:
        A: Direct requirements matrix.

    Returns:
        Dict with lambda_1 (Perron root), lambda_2, spectral_gap,
        mixing_time_bound, spectral_ratio, all eigenvalues.
    """
    eigenvalues = linalg.eigvals(A.values)
    magnitudes = np.abs(eigenvalues)
    sorted_idx = np.argsort(-magnitudes)
    sorted_mags = magnitudes[sorted_idx]

    lambda_1 = float(sorted_mags[0])
    lambda_2 = float(sorted_mags[1]) if len(sorted_mags) > 1 else 0.0
    gap = lambda_1 - lambda_2

    mixing_bound = np.log(A.shape[0]) / gap if gap > 1e-10 else float("inf")
    spectral_ratio = lambda_2 / lambda_1 if lambda_1 > 1e-10 else 0.0

    logger.info(f"Spectral gap: {gap:.6f} (lambda_1={lambda_1:.6f}, lambda_2={lambda_2:.6f})")

    return {
        "lambda_1": lambda_1,
        "lambda_2": lambda_2,
        "spectral_gap": float(gap),
        "spectral_ratio": float(spectral_ratio),
        "mixing_time_bound": float(mixing_bound),
        "n_sectors": A.shape[0],
        "r_max": float(1.0 / lambda_1 - 1.0) if lambda_1 > 1e-10 else float("inf"),
    }


def mixing_time_estimation(
    A: pd.DataFrame,
    epsilon: float = 0.01,
) -> Dict[str, float]:
    """Estimate mixing time: steps for shocks to decay to epsilon of original.

    t_mix ~ log(1/epsilon) / spectral_gap

    Args:
        A: Direct requirements matrix.
        epsilon: Decay threshold.

    Returns:
        Dict with spectral_gap, mixing_time, n_steps_to_epsilon.
    """
    sg = spectral_gap(A)
    gap = sg["spectral_gap"]

    if gap > 1e-10:
        t_mix = np.log(1.0 / epsilon) / gap
    else:
        t_mix = float("inf")

    return {
        "spectral_gap": gap,
        "epsilon": epsilon,
        "mixing_time": float(t_mix),
        "n_steps_to_epsilon": int(np.ceil(t_mix)) if np.isfinite(t_mix) else -1,
    }


def eigenvector_centrality_from_spectrum(A: pd.DataFrame) -> pd.DataFrame:
    """Compute left and right Perron eigenvectors.

    Right eigenvector: proportional sector sizes at balanced growth.
    Left eigenvector: vertically integrated labor values (Marxian interpretation).

    Args:
        A: Direct requirements matrix.

    Returns:
        DataFrame with right_eigenvector, left_eigenvector per sector.
    """
    eigenvalues, right_vecs = linalg.eig(A.values)
    left_eigenvalues, left_vecs = linalg.eig(A.values.T)

    idx = np.argmax(np.abs(eigenvalues))
    right = np.abs(right_vecs[:, idx].real)
    right = right / right.sum()

    left_idx = np.argmax(np.abs(left_eigenvalues))
    left = np.abs(left_vecs[:, left_idx].real)
    left = left / left.sum()

    return pd.DataFrame({
        "right_eigenvector": right,
        "left_eigenvector": left,
    }, index=A.index)


def spectral_gap_timeseries(data_by_year: Dict[int, dict]) -> pd.DataFrame:
    """Track spectral gap and mixing time across years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year, lambda_1, lambda_2, spectral_gap, mixing_time, r_max.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        A = data_by_year[year].get("A_matrix")
        if A is None or A.empty:
            continue
        sg = spectral_gap(A)
        sg["year"] = year
        rows.append(sg)

    return pd.DataFrame(rows).set_index("year")
