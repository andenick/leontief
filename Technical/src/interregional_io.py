"""Interregional Input-Output analysis via Location Quotient regionalization.

Constructs approximate regional I-O tables from the national table using
Location Quotient (LQ) methods, then builds interregional models to trace
cross-region supply chain effects.

Reference: Miller & Blair (2009/2022), Ch. 3, 8; Flegg et al. (1995).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def location_quotients(
    regional_output: pd.DataFrame,
    national_output: pd.Series,
) -> pd.DataFrame:
    """Compute simple Location Quotients for all regions.

    LQ_is = (x_is / x_s) / (x_i / x)
    Where x_is = output of sector i in region s.

    Args:
        regional_output: DataFrame with sectors as rows, regions as columns.
        national_output: National output by sector.

    Returns:
        DataFrame of LQ values (sectors x regions).
    """
    sectors = regional_output.index.intersection(national_output.index)
    reg = regional_output.loc[sectors]
    nat = national_output.reindex(sectors).fillna(0)

    national_total = nat.sum()
    if national_total == 0:
        return pd.DataFrame(0, index=sectors, columns=reg.columns)

    national_share = nat / national_total

    lq = pd.DataFrame(index=sectors, columns=reg.columns, dtype=float)
    for region in reg.columns:
        region_total = reg[region].sum()
        if region_total == 0:
            lq[region] = 0
        else:
            region_share = reg[region] / region_total
            lq[region] = region_share / national_share.replace(0, np.nan)

    return lq.fillna(0)


def flegg_lq(
    simple_lq: pd.DataFrame,
    regional_output: pd.DataFrame,
    national_total: float,
    lambda_param: float = 0.3,
) -> pd.DataFrame:
    """Compute Flegg Location Quotients (FLQ).

    FLQ_is = CILQ_is * lambda_s
    where lambda_s = [log2(1 + x_s/x)]^delta

    Better than simple LQ for small regions (adjusts for region size).

    Args:
        simple_lq: Simple LQ DataFrame (from location_quotients).
        regional_output: Regional output by sector and region.
        national_total: National total output.
        lambda_param: Adjustment parameter delta (typically 0.1-0.5).

    Returns:
        DataFrame of FLQ values.
    """
    flq = simple_lq.copy()

    for region in flq.columns:
        region_total = regional_output[region].sum()
        size_adj = np.log2(1 + region_total / max(national_total, 1e-10)) ** lambda_param
        flq[region] = simple_lq[region] * size_adj

    return flq


def regionalize_a_matrix(
    A_national: pd.DataFrame,
    lq: pd.Series,
) -> pd.DataFrame:
    """Construct a regional A matrix using Location Quotients.

    A_regional_ij = A_national_ij * min(LQ_i, 1)
    Cells where LQ < 1 are scaled down (region imports that input).

    Args:
        A_national: National direct requirements matrix.
        lq: Location quotients for one region (indexed by sector).

    Returns:
        Regional A matrix.
    """
    sectors = A_national.index.intersection(lq.index)
    A_nat = A_national.loc[sectors, sectors]
    lq_aligned = lq.reindex(sectors).fillna(0)

    adjustment = lq_aligned.clip(upper=1.0)
    A_regional = A_nat.multiply(adjustment, axis=0)
    return A_regional


def build_interregional_table(
    regional_A: Dict[str, pd.DataFrame],
    trade_coefficients: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build an interregional I-O table from regional A matrices.

    Creates block structure: diagonal = within-region, off-diagonal = trade.

    Args:
        regional_A: Dict of region_name -> regional A matrix.
        trade_coefficients: Optional matrix of inter-regional trade shares.
            If None, estimates from LQ-based import propensities.

    Returns:
        Interregional A matrix (n*R x n*R).
    """
    regions = sorted(regional_A.keys())
    first_A = regional_A[regions[0]]
    sectors = first_A.index.tolist()
    n = len(sectors)
    R = len(regions)

    # Multi-index: (region, sector)
    mi = pd.MultiIndex.from_product([regions, sectors], names=["region", "sector"])
    A_inter = pd.DataFrame(0.0, index=mi, columns=mi)

    for reg in regions:
        A_r = regional_A[reg].loc[sectors, sectors]
        for i, si in enumerate(sectors):
            for j, sj in enumerate(sectors):
                A_inter.loc[(reg, si), (reg, sj)] = A_r.loc[si, sj]

    if trade_coefficients is not None and not trade_coefficients.empty:
        for r_from in regions:
            for r_to in regions:
                if r_from == r_to:
                    continue
                trade_share = trade_coefficients.get((r_from, r_to), 0.05)
                A_nat = regional_A[r_from].loc[sectors, sectors]
                for i, si in enumerate(sectors):
                    for j, sj in enumerate(sectors):
                        A_inter.loc[(r_from, si), (r_to, sj)] = A_nat.loc[si, sj] * trade_share

    logger.info(f"Interregional table: {R} regions, {n} sectors, {R*n}x{R*n} matrix")
    return A_inter


def regional_multipliers(
    A_interregional: pd.DataFrame,
) -> pd.DataFrame:
    """Compute output multipliers from the interregional Leontief inverse.

    Args:
        A_interregional: Interregional A matrix.

    Returns:
        DataFrame with region, sector, multiplier columns.
    """
    n = A_interregional.shape[0]
    L = linalg.inv(np.eye(n) - A_interregional.values)
    L_df = pd.DataFrame(L, index=A_interregional.index, columns=A_interregional.columns)

    multipliers = L_df.sum(axis=0)
    multipliers.name = "output_multiplier"

    result = multipliers.reset_index()
    result.columns = ["region", "sector", "output_multiplier"]
    return result


def spillover_effects(
    A_interregional: pd.DataFrame,
    shock_region: str,
    shock_vector: pd.Series,
) -> Dict[str, pd.Series]:
    """Measure cross-region spillover from a demand shock.

    Args:
        A_interregional: Interregional A matrix.
        shock_region: Region receiving the shock.
        shock_vector: Final demand shock by sector (for the shock region).

    Returns:
        Dict of region_name -> output impact vector.
    """
    n = A_interregional.shape[0]
    L = linalg.inv(np.eye(n) - A_interregional.values)
    L_df = pd.DataFrame(L, index=A_interregional.index, columns=A_interregional.columns)

    regions = A_interregional.index.get_level_values("region").unique()
    sectors = A_interregional.index.get_level_values("sector").unique()

    f = pd.Series(0.0, index=A_interregional.index)
    for sector in shock_vector.index:
        if (shock_region, sector) in f.index:
            f[(shock_region, sector)] = shock_vector[sector]

    impact = L_df @ f

    results = {}
    for reg in regions:
        reg_impact = impact.loc[reg]
        results[reg] = reg_impact

    return results


def interregional_feedback(
    A_interregional: pd.DataFrame,
    regions: List[str],
) -> pd.DataFrame:
    """Decompose multipliers into intra-regional and inter-regional feedback.

    Args:
        A_interregional: Interregional A matrix.
        regions: List of region names.

    Returns:
        DataFrame with region, intra_multiplier, inter_multiplier, feedback_ratio.
    """
    n_total = A_interregional.shape[0]
    L_full = linalg.inv(np.eye(n_total) - A_interregional.values)

    sectors = A_interregional.index.get_level_values("sector").unique()
    n_sectors = len(sectors)

    rows = []
    for reg in regions:
        reg_idx = [(reg, s) for s in sectors]
        valid = [idx for idx in reg_idx if idx in A_interregional.index]
        if not valid:
            continue

        pos = [A_interregional.index.get_loc(idx) for idx in valid]

        A_intra = A_interregional.loc[valid, valid]
        L_intra = linalg.inv(np.eye(len(valid)) - A_intra.values)

        intra_mult = L_intra.sum() / len(valid)
        full_mult = sum(L_full[p].sum() for p in pos) / len(valid)
        inter_mult = full_mult - intra_mult

        rows.append({
            "region": reg,
            "intra_multiplier": float(intra_mult),
            "inter_multiplier": float(inter_mult),
            "total_multiplier": float(full_mult),
            "feedback_ratio": float(inter_mult / max(intra_mult, 1e-10)),
        })

    return pd.DataFrame(rows).set_index("region")
