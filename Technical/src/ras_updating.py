"""RAS biproportional balancing and Cross-Entropy updating for I-O tables.

Updates an old A matrix to match new row and column totals using
iterative scaling (RAS) or information-theoretic (CE) methods.

Reference: Miller & Blair (2009/2022), Ch. 7; Stone (1961).
"""

import numpy as np
import pandas as pd
from scipy import linalg, optimize
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def ras_biproportional(
    A_0: pd.DataFrame,
    target_row_sums: pd.Series,
    target_col_sums: pd.Series,
    max_iter: int = 1000,
    tol: float = 1e-8,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """RAS biproportional balancing.

    Iteratively scales rows and columns of A_0 to match target marginals.
    Each iteration: scale rows to match target_row_sums, then scale columns
    to match target_col_sums. Converges when both constraints are satisfied.

    Args:
        A_0: Baseline coefficient matrix (n x n).
        target_row_sums: Desired row sums for the updated matrix.
        target_col_sums: Desired column sums for the updated matrix.
        max_iter: Maximum iterations.
        tol: Convergence tolerance (max absolute deviation from target).

    Returns:
        Tuple of (balanced A matrix, convergence log DataFrame).
    """
    common = A_0.index.intersection(target_row_sums.index).intersection(target_col_sums.index)
    A = A_0.loc[common, common].values.astype(float).copy()
    u = target_row_sums.reindex(common).values.astype(float)
    v = target_col_sums.reindex(common).values.astype(float)

    log_rows = []

    for iteration in range(max_iter):
        row_sums = A.sum(axis=1)
        row_factors = np.where(row_sums > 0, u / row_sums, 0)
        A = A * row_factors[:, np.newaxis]

        col_sums = A.sum(axis=0)
        col_factors = np.where(col_sums > 0, v / col_sums, 0)
        A = A * col_factors[np.newaxis, :]

        row_err = np.max(np.abs(A.sum(axis=1) - u))
        col_err = np.max(np.abs(A.sum(axis=0) - v))
        max_err = max(row_err, col_err)

        log_rows.append({
            "iteration": iteration + 1,
            "row_error": row_err,
            "col_error": col_err,
            "max_error": max_err,
        })

        if max_err < tol:
            logger.info(f"RAS converged in {iteration + 1} iterations (err={max_err:.2e})")
            break
    else:
        logger.warning(f"RAS did not converge after {max_iter} iterations (err={max_err:.2e})")

    result = pd.DataFrame(A, index=common, columns=common)
    convergence = pd.DataFrame(log_rows)
    return result, convergence


def cross_entropy_updating(
    A_0: pd.DataFrame,
    target_row_sums: pd.Series,
    target_col_sums: pd.Series,
) -> pd.DataFrame:
    """Cross-entropy minimization for I-O table updating.

    Minimizes: sum_ij a_ij * log(a_ij / a_0_ij)
    Subject to: row sums = u, col sums = v, a_ij >= 0

    Slower than RAS but handles zero cells and additional constraints.

    Args:
        A_0: Baseline coefficient matrix.
        target_row_sums: Desired row sums.
        target_col_sums: Desired column sums.

    Returns:
        Updated A matrix minimizing cross-entropy distance from A_0.
    """
    common = A_0.index.intersection(target_row_sums.index).intersection(target_col_sums.index)
    A0 = A_0.loc[common, common].values.astype(float)
    u = target_row_sums.reindex(common).values.astype(float)
    v = target_col_sums.reindex(common).values.astype(float)
    n = len(common)

    A0_flat = A0.flatten()
    mask = A0_flat > 0

    def objective(x):
        result = 0.0
        for i in range(len(x)):
            if mask[i] and x[i] > 1e-15:
                result += x[i] * np.log(x[i] / A0_flat[i])
        return result

    def row_constraint(x, i):
        return x.reshape(n, n)[i, :].sum() - u[i]

    def col_constraint(x, j):
        return x.reshape(n, n)[:, j].sum() - v[j]

    constraints = []
    for i in range(n):
        constraints.append({"type": "eq", "fun": row_constraint, "args": (i,)})
    for j in range(n):
        constraints.append({"type": "eq", "fun": col_constraint, "args": (j,)})

    bounds = [(0, None)] * (n * n)

    # Use RAS solution as initial guess for faster convergence
    ras_result, _ = ras_biproportional(
        pd.DataFrame(A0, index=common, columns=common),
        pd.Series(u, index=common),
        pd.Series(v, index=common),
        max_iter=100,
    )
    x0 = ras_result.values.flatten()

    result = optimize.minimize(
        objective, x0, method="SLSQP",
        bounds=bounds, constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-10},
    )

    if not result.success:
        logger.warning(f"CE optimization did not converge: {result.message}")

    A_new = result.x.reshape(n, n)
    return pd.DataFrame(A_new, index=common, columns=common)


def ras_convergence_diagnostics(convergence_log: pd.DataFrame) -> Dict[str, float]:
    """Summarize RAS convergence behavior.

    Args:
        convergence_log: Output from ras_biproportional.

    Returns:
        Dict with iterations, final_error, converged flag, decay_rate.
    """
    final = convergence_log.iloc[-1]
    n_iter = int(final["iteration"])
    final_err = float(final["max_error"])

    decay_rate = np.nan
    if len(convergence_log) > 1:
        errors = convergence_log["max_error"].values
        positive = errors[errors > 0]
        if len(positive) > 1:
            log_errors = np.log(positive)
            decay_rate = float(np.polyfit(range(len(log_errors)), log_errors, 1)[0])

    return {
        "iterations": n_iter,
        "final_max_error": final_err,
        "converged": final_err < 1e-6,
        "log_decay_rate": decay_rate,
    }


def project_io_table(
    A_base: pd.DataFrame,
    x_target: pd.Series,
    f_target: pd.Series,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Project an I-O table to a new year using RAS.

    Infers target row and column sums from total output and final demand,
    then applies RAS to update the base A matrix.

    Args:
        A_base: Baseline direct requirements matrix.
        x_target: Target-year total output by sector.
        f_target: Target-year final demand by sector.

    Returns:
        Tuple of (projected A matrix, convergence log).
    """
    common = A_base.index.intersection(x_target.index).intersection(f_target.index)
    x = x_target.reindex(common).fillna(0)
    f = f_target.reindex(common).fillna(0)

    # Z = A * x_hat => row sum of Z = intermediate demand from sector i
    # col sum of Z = intermediate inputs to sector j = x_j - VA_j
    # Approximate: intermediate inputs = x - f (very rough)
    target_col_sums = (x - f).clip(lower=0)
    # Row sums: intermediate sales from each sector
    # Use base A row proportions scaled to new output
    A_base_common = A_base.loc[common, common]
    base_row_sums = (A_base_common.values * x.values[np.newaxis, :]).sum(axis=1)
    scale = x.sum() / max(base_row_sums.sum(), 1e-10)
    target_row_sums = pd.Series(base_row_sums * scale, index=common)

    return ras_biproportional(A_base_common, target_row_sums, target_col_sums)


def ras_accuracy_report(
    A_projected: pd.DataFrame,
    A_actual: pd.DataFrame,
) -> Dict[str, float]:
    """Compare a RAS-projected A matrix against the actual observed matrix.

    Args:
        A_projected: A matrix produced by RAS projection.
        A_actual: Actually observed A matrix for the target year.

    Returns:
        Dict with MAPE, RMSE, max_absolute_error, correlation.
    """
    common = A_projected.index.intersection(A_actual.index)
    proj = A_projected.loc[common, common].values
    actual = A_actual.loc[common, common].values

    nonzero = actual != 0
    if nonzero.any():
        mape = float(np.mean(np.abs(proj[nonzero] - actual[nonzero]) / np.abs(actual[nonzero])) * 100)
    else:
        mape = np.nan

    rmse = float(np.sqrt(np.mean((proj - actual) ** 2)))
    max_err = float(np.max(np.abs(proj - actual)))
    corr = float(np.corrcoef(proj.flatten(), actual.flatten())[0, 1])

    return {
        "mape_pct": mape,
        "rmse": rmse,
        "max_absolute_error": max_err,
        "correlation": corr,
        "n_sectors": len(common),
    }
