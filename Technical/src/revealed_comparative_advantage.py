"""Revealed Comparative Advantage (RCA) with I-O adjustment.

Computes standard Balassa RCA and an I-O-adjusted version that accounts
for domestic value added content using the Leontief inverse.

Reference: Balassa (1965); Koopman, Wang & Wei (2014).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def balassa_rca(
    exports: pd.Series,
    world_exports: pd.Series,
) -> pd.Series:
    """Compute standard Balassa Revealed Comparative Advantage.

    RCA_i = (x_i / X) / (w_i / W)
    Where x_i = country's exports of sector i, X = total exports,
    w_i = world exports of sector i, W = total world exports.

    RCA > 1: comparative advantage; RCA < 1: comparative disadvantage.

    Args:
        exports: Country's exports by sector.
        world_exports: World exports by sector.

    Returns:
        Series of RCA values by sector.
    """
    common = exports.index.intersection(world_exports.index)
    e = exports.reindex(common).fillna(0)
    w = world_exports.reindex(common).fillna(0)

    E_total = e.sum()
    W_total = w.sum()

    if E_total == 0 or W_total == 0:
        return pd.Series(0, index=common, name="rca")

    country_share = e / E_total
    world_share = w / W_total

    rca = country_share / world_share.replace(0, np.nan)
    rca = rca.fillna(0)
    rca.name = "rca"
    return rca


def normalized_rca(rca: pd.Series) -> pd.Series:
    """Normalize RCA to [-1, 1] range.

    NRCA = (RCA - 1) / (RCA + 1)

    Args:
        rca: Raw RCA values.

    Returns:
        Normalized RCA in [-1, 1].
    """
    result = (rca - 1) / (rca + 1).replace(0, np.nan)
    result = result.fillna(0)
    result.name = "normalized_rca"
    return result


def io_adjusted_rca(
    A: pd.DataFrame,
    L: pd.DataFrame,
    exports: pd.Series,
    world_exports: pd.Series,
    value_added_coeff: pd.Series,
) -> pd.DataFrame:
    """Compute I-O adjusted RCA using domestic value added content.

    Instead of gross exports, uses DVA (domestic value added) in exports:
    DVA_i = v' * L * e_i

    Args:
        A: Direct requirements matrix.
        L: Leontief inverse.
        exports: Country's gross exports by sector.
        world_exports: World gross exports by sector.
        value_added_coeff: Value added per unit output by sector (v = VA/x).

    Returns:
        DataFrame with raw_rca, adjusted_rca, dva_share columns.
    """
    sectors = A.index
    e = exports.reindex(sectors).fillna(0)
    w = world_exports.reindex(sectors).fillna(0)
    v = value_added_coeff.reindex(sectors).fillna(0)

    raw_rca = balassa_rca(e, w)

    # DVA in exports: for each sector j, DVA_j = sum_i(v_i * L_ij) * e_j
    v_integrated = v.values @ L.values
    dva = v_integrated * e.values

    dva_total = dva.sum()
    W_total = w.sum()

    if dva_total == 0 or W_total == 0:
        adjusted = pd.Series(0, index=sectors)
    else:
        dva_share = dva / dva_total
        world_share = w / W_total
        adjusted = dva_share / world_share.replace(0, np.nan).values
        adjusted = pd.Series(adjusted, index=sectors).fillna(0)

    gross_total = e.sum()
    dva_content = pd.Series(
        np.where(e.values > 0, dva / e.values, 0),
        index=sectors,
    )

    result = pd.DataFrame({
        "gross_exports": e,
        "dva_in_exports": dva,
        "dva_content_share": dva_content,
        "raw_rca": raw_rca.reindex(sectors).fillna(0),
        "adjusted_rca": adjusted,
        "raw_nrca": normalized_rca(raw_rca).reindex(sectors).fillna(0),
        "adjusted_nrca": normalized_rca(adjusted),
    })

    return result.sort_values("adjusted_rca", ascending=False)


def rca_timeseries(
    data_by_year: Dict[int, dict],
    exports_by_year: Dict[int, pd.Series],
    world_exports_by_year: Optional[Dict[int, pd.Series]] = None,
) -> pd.DataFrame:
    """Compute RCA across years.

    Args:
        data_by_year: I-O data dict by year.
        exports_by_year: Country exports by sector by year.
        world_exports_by_year: World exports by year (if None, uses country totals only).

    Returns:
        DataFrame with years as rows, sectors as columns (RCA values).
    """
    results = {}
    for year in sorted(exports_by_year.keys()):
        e = exports_by_year[year]

        if world_exports_by_year and year in world_exports_by_year:
            w = world_exports_by_year[year]
        else:
            w = e

        rca = balassa_rca(e, w)
        results[year] = rca

    df = pd.DataFrame(results).T
    df.index.name = "year"
    return df


def rca_structural_change(
    rca_ts: pd.DataFrame,
    threshold: float = 1.0,
) -> pd.DataFrame:
    """Identify sectors that gained or lost comparative advantage.

    Detects years where RCA crosses the threshold (1.0 by default).

    Args:
        rca_ts: RCA time series (years x sectors).
        threshold: RCA threshold for comparative advantage.

    Returns:
        DataFrame with sector, year, direction (gained/lost), rca_before, rca_after.
    """
    crossings = []
    for sector in rca_ts.columns:
        values = rca_ts[sector].dropna()
        for i in range(1, len(values)):
            prev = values.iloc[i - 1]
            curr = values.iloc[i]

            if prev < threshold <= curr:
                crossings.append({
                    "sector": sector,
                    "year": values.index[i],
                    "direction": "gained",
                    "rca_before": float(prev),
                    "rca_after": float(curr),
                })
            elif prev >= threshold > curr:
                crossings.append({
                    "sector": sector,
                    "year": values.index[i],
                    "direction": "lost",
                    "rca_before": float(prev),
                    "rca_after": float(curr),
                })

    return pd.DataFrame(crossings)


def rca_concentration(rca: pd.Series) -> Dict[str, float]:
    """Compute concentration metrics for the RCA distribution.

    Args:
        rca: RCA values by sector.

    Returns:
        Dict with n_advantage, hhi, gini, diversification_index.
    """
    n_adv = int((rca > 1).sum())
    n_total = len(rca)

    rca_positive = rca[rca > 0]
    shares = rca_positive / rca_positive.sum()
    hhi = float((shares ** 2).sum())

    sorted_rca = np.sort(rca.values)
    n = len(sorted_rca)
    if n == 0 or sorted_rca.sum() == 0:
        gini = 0.0
    else:
        index = np.arange(1, n + 1)
        gini = float((2 * np.sum(index * sorted_rca) / (n * sorted_rca.sum())) - (n + 1) / n)

    return {
        "n_sectors_with_advantage": n_adv,
        "n_total_sectors": n_total,
        "advantage_share": n_adv / max(n_total, 1),
        "hhi": hhi,
        "gini": max(gini, 0),
    }
