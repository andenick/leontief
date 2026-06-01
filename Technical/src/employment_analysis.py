"""Employment (compensation-based) multiplier analysis.

Uses compensation of employees as a proxy for labor input to compute
employment multipliers: total compensation generated per unit of
final demand in each sector.

Reference: Miller & Blair (2009), Ch. 6 — from Wynne KB.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def compensation_coefficients(
    value_added: pd.DataFrame,
    total_output: pd.Series,
) -> pd.Series:
    """Direct compensation per unit output by sector.

    e_j = comp_j / x_j

    Args:
        value_added: VA components × sectors (must include V001).
        total_output: Total industry output.

    Returns:
        Series of compensation coefficients.
    """
    comp_row = None
    for idx in value_added.index:
        if "V001" in str(idx):
            comp_row = idx
            break
    if comp_row is None:
        comp_row = value_added.index[0]

    comp = value_added.loc[comp_row]
    x_safe = total_output.reindex(comp.index).replace(0, np.nan)
    coeff = (comp / x_safe).fillna(0)
    coeff.name = "compensation_coefficient"
    return coeff


def employment_multipliers(
    L: pd.DataFrame,
    comp_coeff: pd.Series,
) -> pd.Series:
    """Employment (compensation) multipliers.

    m_j^e = e' × L — total compensation generated across all sectors
    per unit of final demand in sector j.

    Args:
        L: Leontief inverse matrix.
        comp_coeff: Direct compensation coefficients by sector.

    Returns:
        Series of employment multipliers.
    """
    common = comp_coeff.index.intersection(L.index)
    e = comp_coeff.reindex(common).fillna(0).values
    L_aligned = L.loc[common, common].fillna(0).values
    mult = e @ L_aligned
    result = pd.Series(mult, index=common, name="employment_multiplier")
    logger.info(f"Employment multipliers: mean={result.mean():.4f}")
    return result


def compensation_intensity_timeseries(
    data_by_year: dict,
) -> pd.DataFrame:
    """Track compensation intensity across years.

    Args:
        data_by_year: dict of year -> parsed I-O data dict.

    Returns:
        DataFrame with years as index, sectors as columns, values = comp/output.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        va = d.get("value_added")
        x = d.get("total_output")
        if va is None or x is None or va.empty or x.empty:
            continue
        coeff = compensation_coefficients(va, x)
        coeff.name = year
        rows.append(coeff)

    df = pd.DataFrame(rows)
    df.index.name = "year"
    return df
