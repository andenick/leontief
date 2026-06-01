"""Cascade failure simulation for I-O production networks.

Simulates contagion: when a sector's output falls below a threshold,
it can no longer supply downstream customers, triggering further failures.
Iterative hypothetical extraction with endogenous propagation.

Reference: Acemoglu et al. (2012); Hallegatte (2008).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def cascade_step(
    A: pd.DataFrame,
    f: pd.Series,
    x_baseline: pd.Series,
    failed_sectors: Set[str],
    threshold_pct: float = 50.0,
) -> Tuple[pd.Series, Set[str]]:
    """Execute one step of cascade propagation.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        x_baseline: Original (pre-shock) output vector.
        failed_sectors: Set of sectors that have already failed.
        threshold_pct: Sectors with output loss > this % of baseline fail.

    Returns:
        Tuple of (new output vector, updated set of failed sectors).
    """
    n = A.shape[0]
    A_mod = A.values.copy()

    for sector in failed_sectors:
        if sector in A.index:
            k = A.index.get_loc(sector)
            A_mod[k, :] = 0
            A_mod[:, k] = 0

    try:
        L_mod = linalg.inv(np.eye(n) - A_mod)
        x_new = L_mod @ f.values
    except linalg.LinAlgError:
        x_new = np.zeros(n)

    x_new_series = pd.Series(x_new, index=A.index)

    new_failures = set(failed_sectors)
    for sector in A.index:
        if sector in failed_sectors:
            continue
        baseline = x_baseline.get(sector, 0)
        if baseline <= 0:
            continue
        loss_pct = (baseline - x_new_series.get(sector, 0)) / baseline * 100
        if loss_pct >= threshold_pct:
            new_failures.add(sector)

    return x_new_series, new_failures


def run_cascade(
    A: pd.DataFrame,
    f: pd.Series,
    initial_shock: Dict[str, float],
    threshold_pct: float = 50.0,
    max_steps: int = 50,
) -> pd.DataFrame:
    """Run a full cascade simulation from an initial shock.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        initial_shock: Dict of {sector_code: fraction_of_output_lost}.
            Values in [0, 1] where 1.0 = complete failure.
        threshold_pct: Output loss threshold for cascade propagation.
        max_steps: Maximum cascade steps.

    Returns:
        DataFrame with step, n_failed, total_output, output_loss_pct,
        new_failures_this_step.
    """
    n = A.shape[0]
    L_base = linalg.inv(np.eye(n) - A.values)
    x_baseline = pd.Series(L_base @ f.values, index=A.index)
    total_baseline = x_baseline.sum()

    failed = set()
    for sector, fraction in initial_shock.items():
        if fraction >= 0.99 and sector in A.index:
            failed.add(sector)

    log_rows = [{
        "step": 0,
        "n_failed": len(failed),
        "total_output": float(total_baseline),
        "output_loss_pct": 0.0,
        "new_failures": ", ".join(sorted(failed)),
    }]

    for step in range(1, max_steps + 1):
        prev_failed = set(failed)
        x_current, failed = cascade_step(A, f, x_baseline, failed, threshold_pct)

        new_this_step = failed - prev_failed
        total_current = max(x_current.sum(), 0)
        loss_pct = (total_baseline - total_current) / max(total_baseline, 1e-10) * 100

        log_rows.append({
            "step": step,
            "n_failed": len(failed),
            "total_output": float(total_current),
            "output_loss_pct": float(loss_pct),
            "new_failures": ", ".join(sorted(new_this_step)),
        })

        if not new_this_step:
            logger.info(f"Cascade stabilized at step {step}: {len(failed)} failed sectors")
            break

    return pd.DataFrame(log_rows)


def cascade_vulnerability_map(
    A: pd.DataFrame,
    f: pd.Series,
    threshold_pct: float = 50.0,
    max_sectors: Optional[int] = None,
) -> pd.DataFrame:
    """Run cascade for each sector as the initial shock.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        threshold_pct: Cascade failure threshold.
        max_sectors: Limit to top-N sectors by output (for large matrices).

    Returns:
        DataFrame with initial_sector, cascade_size, total_output_loss_pct,
        steps_to_stabilize, sorted by cascade_size descending.
    """
    n = A.shape[0]
    L_base = linalg.inv(np.eye(n) - A.values)
    x_baseline = pd.Series(L_base @ f.values, index=A.index)

    sectors = list(A.index)
    if max_sectors and len(sectors) > max_sectors:
        top = x_baseline.nlargest(max_sectors).index.tolist()
        sectors = top

    results = []
    for sector in sectors:
        cascade = run_cascade(A, f, {sector: 1.0}, threshold_pct)
        final = cascade.iloc[-1]

        results.append({
            "initial_sector": sector,
            "cascade_size": int(final["n_failed"]),
            "total_output_loss_pct": float(final["output_loss_pct"]),
            "steps_to_stabilize": int(final["step"]),
            "baseline_output_share": float(x_baseline[sector] / max(x_baseline.sum(), 1e-10) * 100),
        })

    df = pd.DataFrame(results).set_index("initial_sector")
    df = df.sort_values("cascade_size", ascending=False)

    logger.info(f"Vulnerability map: max cascade = {df['cascade_size'].max()} sectors")
    return df


def systemic_risk_index(
    vulnerability_map: pd.DataFrame,
) -> pd.Series:
    """Compute systemic risk score for each sector.

    Weighted average cascade size when sector k fails,
    weighted by sector k's output share.

    Args:
        vulnerability_map: Output from cascade_vulnerability_map.

    Returns:
        Series of systemic risk scores, higher = more systemically important.
    """
    weight = vulnerability_map["baseline_output_share"] / 100
    cascade = vulnerability_map["cascade_size"]
    loss = vulnerability_map["total_output_loss_pct"]

    score = (cascade * weight + loss * weight) / 2
    score.name = "systemic_risk_index"
    return score.sort_values(ascending=False)


def targeted_vs_random_attack(
    A: pd.DataFrame,
    f: pd.Series,
    n_removals: int = 10,
    threshold_pct: float = 50.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Compare targeted (highest-output) vs. random sector removal.

    Tests network robustness: scale-free networks are robust to random
    failure but fragile to targeted attacks.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        n_removals: Number of sectors to remove sequentially.
        threshold_pct: Cascade threshold.
        seed: Random seed for random removal order.

    Returns:
        DataFrame with n_removed, targeted_loss_pct, random_loss_pct.
    """
    n = A.shape[0]
    L_base = linalg.inv(np.eye(n) - A.values)
    x_baseline = pd.Series(L_base @ f.values, index=A.index)
    total_baseline = x_baseline.sum()

    targeted_order = x_baseline.nlargest(n_removals).index.tolist()

    rng = np.random.RandomState(seed)
    random_order = list(A.index)
    rng.shuffle(random_order)
    random_order = random_order[:n_removals]

    results = []
    for k in range(1, n_removals + 1):
        targeted_shock = {s: 1.0 for s in targeted_order[:k]}
        targeted_cascade = run_cascade(A, f, targeted_shock, threshold_pct)
        targeted_loss = float(targeted_cascade.iloc[-1]["output_loss_pct"])

        random_shock = {s: 1.0 for s in random_order[:k]}
        random_cascade = run_cascade(A, f, random_shock, threshold_pct)
        random_loss = float(random_cascade.iloc[-1]["output_loss_pct"])

        results.append({
            "n_removed": k,
            "targeted_loss_pct": targeted_loss,
            "random_loss_pct": random_loss,
            "fragility_ratio": targeted_loss / max(random_loss, 1e-10),
        })

    return pd.DataFrame(results).set_index("n_removed")
