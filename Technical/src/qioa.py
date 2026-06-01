"""Qualitative Input-Output Analysis (QIOA).

Studies the sign structure and qualitative properties of the Leontief
inverse to determine which inter-industry connections are robust to
quantitative changes in coefficients.

Reference: Steenge (1990); Miller & Blair (2009), Ch. 6.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def qualitative_matrix(
    A: pd.DataFrame,
    threshold: float = 1e-6,
) -> pd.DataFrame:
    """Convert A matrix to binary sign (qualitative) matrix.

    Args:
        A: Direct requirements matrix.
        threshold: Values below this are treated as zero.

    Returns:
        Binary DataFrame: 1 where A > threshold, 0 otherwise.
    """
    Q = (A.abs() > threshold).astype(int)
    n_nonzero = Q.values.sum()
    n_total = Q.shape[0] * Q.shape[1]
    logger.info(f"Qualitative matrix: {n_nonzero}/{n_total} nonzero ({n_nonzero/n_total*100:.1f}%)")
    return Q


def qualitative_leontief_inverse(Q: pd.DataFrame) -> pd.DataFrame:
    """Compute qualitative Leontief inverse via boolean transitive closure.

    Q_L = I + Q + Q^2 + Q^3 + ... (in boolean arithmetic)
    Converges when Q^k adds no new nonzero entries.

    Args:
        Q: Binary qualitative matrix.

    Returns:
        Binary DataFrame: 1 if sector i can reach sector j via any path.
    """
    n = Q.shape[0]
    R = np.eye(n, dtype=int) | Q.values.astype(int)
    prev = np.zeros_like(R)

    for k in range(n):
        if np.array_equal(R, prev):
            logger.info(f"Qualitative L converged at power {k}")
            break
        prev = R.copy()
        R = (R | (R @ Q.values.astype(int) > 0).astype(int))

    return pd.DataFrame(R, index=Q.index, columns=Q.columns)


def sign_determinacy_of_L(A: pd.DataFrame) -> pd.DataFrame:
    """Analyze which entries of L are sign-determinate.

    An entry L_ij is sign-determinate if it has the same sign for ALL
    coefficient matrices with the same qualitative (zero/nonzero) pattern
    as A. For productive I-O systems, all L_ij >= 0, but some are
    strictly positive regardless of magnitudes.

    Args:
        A: Direct requirements matrix.

    Returns:
        DataFrame with L_value, is_positive, qualitative_positive
        (guaranteed positive from sign structure alone).
    """
    n = A.shape[0]
    L = linalg.inv(np.eye(n) - A.values)

    Q = qualitative_matrix(A, threshold=1e-8)
    Q_L = qualitative_leontief_inverse(Q)

    return pd.DataFrame({
        "L_value": L.flatten(),
        "is_positive": (L > 0).flatten(),
        "qualitative_positive": Q_L.values.flatten().astype(bool),
        "row": np.repeat(A.index, n),
        "col": np.tile(A.columns, n),
    })


def structural_zeros_analysis(
    A_by_year: Dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Identify structural vs. accidental zeros across years.

    A cell is a structural zero if it's zero in every year observed.
    A cell that's sometimes zero and sometimes nonzero is accidental.

    Args:
        A_by_year: Dict of year -> A matrix.

    Returns:
        DataFrame with row, col, n_years_zero, n_years_nonzero,
        frequency_nonzero, is_structural_zero.
    """
    if not A_by_year:
        return pd.DataFrame()

    years = sorted(A_by_year.keys())
    first = A_by_year[years[0]]
    common_sectors = first.index.tolist()
    for y in years[1:]:
        common_sectors = [s for s in common_sectors if s in A_by_year[y].index]

    n = len(common_sectors)
    nonzero_count = np.zeros((n, n), dtype=int)
    zero_count = np.zeros((n, n), dtype=int)

    for year in years:
        A_y = A_by_year[year].loc[common_sectors, common_sectors].values
        nonzero_count += (np.abs(A_y) > 1e-8).astype(int)
        zero_count += (np.abs(A_y) <= 1e-8).astype(int)

    n_years = len(years)
    rows = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            nz = int(nonzero_count[i, j])
            z = int(zero_count[i, j])
            rows.append({
                "row": common_sectors[i],
                "col": common_sectors[j],
                "n_years_nonzero": nz,
                "n_years_zero": z,
                "frequency_nonzero": nz / n_years,
                "is_structural_zero": nz == 0,
            })

    df = pd.DataFrame(rows)
    n_structural = df["is_structural_zero"].sum()
    n_total = len(df)
    logger.info(f"Structural zeros: {n_structural}/{n_total} ({n_structural/max(n_total,1)*100:.1f}%)")
    return df


def sign_stable_sectors(
    A: pd.DataFrame,
    n_perturbations: int = 200,
    perturbation_pct: float = 0.20,
    seed: int = 42,
) -> pd.DataFrame:
    """Monte Carlo sign stability analysis.

    Perturb each A_ij by +/- perturbation_pct (keeping sign),
    recompute L, and count how often each L_ij keeps the same sign.

    Args:
        A: Direct requirements matrix.
        n_perturbations: Number of Monte Carlo draws.
        perturbation_pct: Maximum fractional perturbation (0.20 = +/-20%).
        seed: Random seed.

    Returns:
        DataFrame (n x n) of sign stability scores in [0, 1].
    """
    n = A.shape[0]
    A_vals = A.values.copy()
    rng = np.random.RandomState(seed)

    L_base = linalg.inv(np.eye(n) - A_vals)
    base_sign = np.sign(L_base)

    agreement = np.zeros((n, n))

    for _ in range(n_perturbations):
        perturbation = 1 + rng.uniform(-perturbation_pct, perturbation_pct, (n, n))
        A_pert = A_vals * perturbation
        A_pert = np.clip(A_pert, 0, None)

        col_sums = A_pert.sum(axis=0)
        if np.any(col_sums >= 1):
            scale = np.where(col_sums >= 1, 0.99 / col_sums, 1.0)
            A_pert *= scale[np.newaxis, :]

        try:
            L_pert = linalg.inv(np.eye(n) - A_pert)
            pert_sign = np.sign(L_pert)
            agreement += (pert_sign == base_sign).astype(float)
        except linalg.LinAlgError:
            agreement += 1.0

    stability = agreement / n_perturbations
    result = pd.DataFrame(stability, index=A.index, columns=A.columns)

    avg_stability = stability.mean()
    logger.info(f"Sign stability: avg={avg_stability:.4f} over {n_perturbations} perturbations")
    return result
