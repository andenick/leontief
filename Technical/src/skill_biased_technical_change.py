"""Skill-Biased Technical Change (SBTC) analysis via I-O tables.

Splits labor into high-skill and low-skill components using BLS
occupation data, then tracks the vertically integrated skill ratio.

Reference: Autor et al. (2003); Acemoglu & Autor (2011).

REQUIRES SATELLITE DATA: BLS occupation-by-industry employment data.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

SATELLITE_DIR = Path(__file__).parent.parent / "data" / "processed" / "satellite"

HIGH_SKILL_SOC_PREFIXES = ["11", "13", "15", "17", "19", "23", "25"]


def load_skill_split(
    filepath: Optional[Path] = None,
) -> Optional[Tuple[pd.Series, pd.Series]]:
    """Load BLS skill split data crosswalked to I-O sectors.

    Expected format: pickle with dict containing 'high_skill' and
    'low_skill' Series indexed by sector code.

    Args:
        filepath: Path to processed skill split data.

    Returns:
        Tuple of (high_skill_coeff, low_skill_coeff) or None.
    """
    if filepath is None:
        filepath = SATELLITE_DIR / "bls_skill_split.pkl"

    if not filepath.exists():
        logger.warning(
            f"BLS skill split data not found at {filepath}. "
            f"Download BLS OES by occupation and industry."
        )
        return None

    import pickle
    with open(filepath, "rb") as f:
        data = pickle.load(f)

    if isinstance(data, dict) and "high_skill" in data and "low_skill" in data:
        return data["high_skill"], data["low_skill"]
    return None


def vertically_integrated_skill_ratio(
    A: pd.DataFrame,
    high_skill_coeff: pd.Series,
    low_skill_coeff: pd.Series,
) -> pd.Series:
    """Compute vertically integrated high-skill / total labor ratio.

    v_high = h × L, v_low = l × L
    skill_ratio_j = v_high_j / (v_high_j + v_low_j)

    Args:
        A: Direct requirements matrix.
        high_skill_coeff: High-skill labor per unit output.
        low_skill_coeff: Low-skill labor per unit output.

    Returns:
        Series of skill ratios in [0, 1].
    """
    sectors = A.index
    n = len(sectors)

    h = high_skill_coeff.reindex(sectors).fillna(0).values
    l = low_skill_coeff.reindex(sectors).fillna(0).values

    L = linalg.inv(np.eye(n) - A.values)

    v_high = h @ L
    v_low = l @ L
    v_total = v_high + v_low

    ratio = np.where(v_total > 1e-10, v_high / v_total, 0)
    result = pd.Series(ratio, index=sectors, name="skill_ratio")

    logger.info(f"Skill ratio: mean={result.mean():.3f}, range=[{result.min():.3f}, {result.max():.3f}]")
    return result


def sbtc_decomposition(
    skill_ratio_0: pd.Series,
    skill_ratio_1: pd.Series,
    output_0: pd.Series,
    output_1: pd.Series,
) -> Dict[str, float]:
    """Decompose aggregate skill intensity change into within vs. between.

    Within: sectors became more skill-intensive (technology effect).
    Between: output shifted toward skill-intensive sectors (structural).

    Args:
        skill_ratio_0/1: Skill ratios in periods 0 and 1.
        output_0/1: Output shares in periods 0 and 1.

    Returns:
        Dict with within_effect, between_effect, interaction, total.
    """
    common = skill_ratio_0.index.intersection(skill_ratio_1.index)
    sr0 = skill_ratio_0.reindex(common).fillna(0)
    sr1 = skill_ratio_1.reindex(common).fillna(0)

    x0 = output_0.reindex(common).fillna(0)
    x1 = output_1.reindex(common).fillna(0)

    share_0 = x0 / max(x0.sum(), 1e-10)
    share_1 = x1 / max(x1.sum(), 1e-10)

    within = ((sr1 - sr0) * share_0).sum()
    between = (sr0 * (share_1 - share_0)).sum()
    interaction = ((sr1 - sr0) * (share_1 - share_0)).sum()

    return {
        "within_effect": float(within),
        "between_effect": float(between),
        "interaction_effect": float(interaction),
        "total_change": float(within + between + interaction),
        "within_share": float(within / max(abs(within + between + interaction), 1e-10)),
    }


def skill_ratio_timeseries(
    data_by_year: Dict[int, dict],
    high_skill_coeff: pd.Series,
    low_skill_coeff: pd.Series,
) -> pd.DataFrame:
    """Track mean skill ratio across years.

    Args:
        data_by_year: Dict of year -> data dict.
        high_skill_coeff: High-skill labor coefficients.
        low_skill_coeff: Low-skill labor coefficients.

    Returns:
        DataFrame with year, mean_ratio, std_ratio.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        A = data_by_year[year].get("A_matrix")
        if A is None or A.empty:
            continue

        ratio = vertically_integrated_skill_ratio(A, high_skill_coeff, low_skill_coeff)
        rows.append({
            "year": year,
            "mean_skill_ratio": float(ratio.mean()),
            "std_skill_ratio": float(ratio.std()),
            "max_skill_ratio": float(ratio.max()),
            "min_skill_ratio": float(ratio.min()),
        })

    return pd.DataFrame(rows).set_index("year")
