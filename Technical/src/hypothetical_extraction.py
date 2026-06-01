"""Hypothetical Extraction Method (HEM) — standalone functional module.

Measures sector importance by removing it from the I-O system and
observing the resulting output loss. Supports full, partial, and
row-only/column-only extraction variants.

Reference: Miller & Blair (2009/2022), Ch. 12.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def hypothetical_extraction_single(
    A: pd.DataFrame,
    f: pd.Series,
    sector: str,
    extraction_type: str = "complete",
) -> Dict[str, float]:
    """Extract a single sector and measure economy-wide output loss.

    Args:
        A: Direct requirements matrix (n x n).
        f: Final demand vector.
        sector: Sector code to extract.
        extraction_type: "complete" (row+col), "backward" (col only),
                         "forward" (row only).

    Returns:
        Dict with baseline_output, extracted_output, output_loss,
        loss_pct, and per-sector losses.
    """
    if sector not in A.index:
        raise ValueError(f"Sector '{sector}' not in A matrix index")

    n = A.shape[0]
    k = A.index.get_loc(sector)
    A_mod = A.values.copy()

    if extraction_type == "complete":
        A_mod[k, :] = 0
        A_mod[:, k] = 0
    elif extraction_type == "backward":
        A_mod[:, k] = 0
    elif extraction_type == "forward":
        A_mod[k, :] = 0
    else:
        raise ValueError(f"Unknown extraction_type: {extraction_type}")

    L_baseline = linalg.inv(np.eye(n) - A.values)
    x_baseline = L_baseline @ f.values

    L_mod = linalg.inv(np.eye(n) - A_mod)
    x_mod = L_mod @ f.values

    losses = x_baseline - x_mod
    total_baseline = x_baseline.sum()
    total_loss = losses.sum()

    return {
        "sector": sector,
        "extraction_type": extraction_type,
        "baseline_output": float(total_baseline),
        "extracted_output": float(x_mod.sum()),
        "output_loss": float(total_loss),
        "loss_pct": float(total_loss / total_baseline * 100) if total_baseline != 0 else 0.0,
        "sector_losses": pd.Series(losses, index=A.index, name=f"loss_{sector}"),
    }


def hypothetical_extraction_all(
    A: pd.DataFrame,
    f: pd.Series,
    extraction_type: str = "complete",
) -> pd.DataFrame:
    """Run hypothetical extraction for every sector.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        extraction_type: "complete", "backward", or "forward".

    Returns:
        DataFrame indexed by sector with output_loss and loss_pct,
        sorted by loss_pct descending.
    """
    results = []
    for sector in A.index:
        try:
            r = hypothetical_extraction_single(A, f, sector, extraction_type)
            results.append({
                "sector": r["sector"],
                "output_loss": r["output_loss"],
                "loss_pct": r["loss_pct"],
            })
        except linalg.LinAlgError:
            results.append({
                "sector": sector,
                "output_loss": np.nan,
                "loss_pct": np.nan,
            })

    df = pd.DataFrame(results).set_index("sector")
    df = df.sort_values("loss_pct", ascending=False)
    logger.info(
        f"HEM ({extraction_type}): top sector = {df.index[0]} "
        f"({df['loss_pct'].iloc[0]:.1f}%)"
    )
    return df


def partial_extraction(
    A: pd.DataFrame,
    f: pd.Series,
    sector: str,
    extraction_fraction: float = 0.5,
) -> Dict[str, float]:
    """Partially extract a sector (reduce its coefficients by a fraction).

    Useful for simulating partial disruptions rather than complete removal.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        sector: Sector code.
        extraction_fraction: Fraction to remove (0.0 = no change, 1.0 = full extraction).

    Returns:
        Dict with baseline_output, extracted_output, output_loss, loss_pct.
    """
    if not 0.0 <= extraction_fraction <= 1.0:
        raise ValueError(f"extraction_fraction must be in [0, 1], got {extraction_fraction}")

    n = A.shape[0]
    k = A.index.get_loc(sector)
    A_mod = A.values.copy()
    A_mod[k, :] *= (1 - extraction_fraction)
    A_mod[:, k] *= (1 - extraction_fraction)

    L_baseline = linalg.inv(np.eye(n) - A.values)
    x_baseline = L_baseline @ f.values

    L_mod = linalg.inv(np.eye(n) - A_mod)
    x_mod = L_mod @ f.values

    total_baseline = x_baseline.sum()
    total_loss = x_baseline.sum() - x_mod.sum()

    return {
        "sector": sector,
        "extraction_fraction": extraction_fraction,
        "baseline_output": float(total_baseline),
        "extracted_output": float(x_mod.sum()),
        "output_loss": float(total_loss),
        "loss_pct": float(total_loss / total_baseline * 100) if total_baseline != 0 else 0.0,
    }


def extraction_decomposition(
    A: pd.DataFrame,
    f: pd.Series,
    sector: str,
) -> Dict[str, float]:
    """Decompose extraction impact into backward and forward components.

    Total = Complete extraction loss
    Backward = Column-only extraction loss (sector stops buying inputs)
    Forward = Row-only extraction loss (sector stops supplying outputs)
    Internal = Total - Backward - Forward (double-counted internal flow)

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        sector: Sector code.

    Returns:
        Dict with total, backward, forward, internal components.
    """
    complete = hypothetical_extraction_single(A, f, sector, "complete")
    backward = hypothetical_extraction_single(A, f, sector, "backward")
    forward = hypothetical_extraction_single(A, f, sector, "forward")

    internal = complete["output_loss"] - backward["output_loss"] - forward["output_loss"]

    return {
        "sector": sector,
        "total_loss": complete["output_loss"],
        "total_loss_pct": complete["loss_pct"],
        "backward_loss": backward["output_loss"],
        "backward_loss_pct": backward["loss_pct"],
        "forward_loss": forward["output_loss"],
        "forward_loss_pct": forward["loss_pct"],
        "internal_loss": float(internal),
    }
