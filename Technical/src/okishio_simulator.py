"""Okishio theorem simulator for I-O tables.

Tests whether observed year-to-year technical change (A matrix shifts)
raises or lowers the general profit rate under the Okishio conditions.

Reference: Okishio (1961); Roemer (1981); Shaikh (2016) Ch. 6.
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def okishio_viable_technique(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    wages_coeff_0: pd.Series,
    prices_0: pd.Series,
) -> pd.Series:
    """Check Okishio viability: does new technique reduce cost at old prices?

    Viable iff cost_1_j = sum_i(a1_ij * p0_i) + w0_j < p0_j

    Args:
        A_0: Old direct requirements matrix.
        A_1: New direct requirements matrix.
        wages_coeff_0: Old wage cost per unit output.
        prices_0: Old equilibrium prices.

    Returns:
        Series[bool] — True where new technique is cost-reducing.
    """
    common = A_0.index.intersection(A_1.index)
    A1 = A_1.loc[common, common]
    p0 = prices_0.reindex(common).fillna(0).values
    w0 = wages_coeff_0.reindex(common).fillna(0).values

    cost_1 = A1.values.T @ p0 + w0
    viable = pd.Series(cost_1 < p0, index=common, name="okishio_viable")

    n_viable = viable.sum()
    logger.info(f"Okishio viability: {n_viable}/{len(common)} sectors ({n_viable/len(common)*100:.0f}%)")
    return viable


def okishio_profit_rate_effect(
    A_0: pd.DataFrame,
    A_1: pd.DataFrame,
    wages_0: pd.Series,
    total_output_0: pd.Series,
    value_added_0: pd.DataFrame,
) -> Dict[str, float]:
    """Compute profit rate under old vs new technique at old real wage.

    Args:
        A_0: Old A matrix.
        A_1: New A matrix.
        wages_0: Old wage bill by sector.
        total_output_0: Old total output.
        value_added_0: Old VA DataFrame.

    Returns:
        Dict with r_old, r_new_okishio, delta_r, okishio_confirmed.
    """
    from profit_rate_simulation import maximum_profit_rate

    common = A_0.index.intersection(A_1.index)
    A0 = A_0.loc[common, common]
    A1 = A_1.loc[common, common]

    r_old = maximum_profit_rate(A0)
    r_new = maximum_profit_rate(A1)

    delta_r = r_new - r_old
    confirmed = delta_r >= 0

    return {
        "r_old": float(r_old),
        "r_new_okishio": float(r_new),
        "delta_r": float(delta_r),
        "delta_r_pct": float(delta_r / max(abs(r_old), 1e-10) * 100),
        "okishio_confirmed": bool(confirmed),
    }


def okishio_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Run Okishio check for each consecutive year-pair.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year_pair, r_old, r_new_okishio, delta_r, okishio_confirmed.
    """
    years = sorted(data_by_year.keys())
    rows = []

    for i in range(1, len(years)):
        y0, y1 = years[i - 1], years[i]
        d0, d1 = data_by_year[y0], data_by_year[y1]

        A0 = d0.get("A_matrix")
        A1 = d1.get("A_matrix")
        w0 = d0.get("total_output")
        va0 = d0.get("value_added")

        if A0 is None or A1 is None:
            continue

        try:
            result = okishio_profit_rate_effect(A0, A1, w0, w0, va0)
            result["year_from"] = y0
            result["year_to"] = y1
            result["year_pair"] = f"{y0}-{y1}"

            # Also compute viable fraction
            sectors = A0.index.intersection(A1.index)
            n = len(sectors)
            L0 = linalg.inv(np.eye(n) - A0.loc[sectors, sectors].values)
            va_coeff = np.ones(n) / n
            p0 = va_coeff @ L0
            w_coeff = pd.Series(0.01, index=sectors)
            viable = okishio_viable_technique(
                A0.loc[sectors, sectors],
                A1.loc[sectors, sectors],
                w_coeff, pd.Series(p0, index=sectors),
            )
            result["viable_fraction"] = float(viable.mean())

            rows.append(result)
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year_pair")
