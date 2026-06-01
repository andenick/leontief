"""Shaikh's integrated/classical rate of profit from I-O tables.

Computes r = S/(C+V) using vertically integrated measures, tracking
the secular tendency of the profit rate (LTPF hypothesis).

Reference: Shaikh (2016) Ch. 6; Basu & Manolakos (2013).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def shaikh_profit_rate_single(
    A: pd.DataFrame,
    labor_coeff: pd.Series,
    wages: pd.Series,
    total_output: pd.Series,
    capital_output_ratios: Optional[pd.Series] = None,
) -> Dict[str, float]:
    """Compute Shaikh's classical aggregate profit rate.

    r = S / (C + V)
    V = aggregate variable capital (wages)
    S = aggregate surplus = VA - wages
    C = aggregate constant capital (from capital stock or I-O proxy)

    Args:
        A: Direct requirements matrix.
        labor_coeff: Direct labor per unit output.
        wages: Total wage bill by sector.
        total_output: Total output by sector.
        capital_output_ratios: Capital/output ratios (optional satellite data).

    Returns:
        Dict with r_classical, V, S, C, organic_composition, surplus_rate.
    """
    sectors = A.index
    n = len(sectors)
    w = wages.reindex(sectors).fillna(0)
    x = total_output.reindex(sectors).fillna(0)
    l = labor_coeff.reindex(sectors).fillna(0)

    L_inv = linalg.inv(np.eye(n) - A.values)
    labor_values = l.values @ L_inv

    V = float(w.sum())
    total_value = float((labor_values * x.values).sum())
    S = total_value - V

    if capital_output_ratios is not None:
        k = capital_output_ratios.reindex(sectors).fillna(0)
        C = float((k * x).sum())
    else:
        # Proxy: constant capital = labor value of intermediate inputs
        intermediate_value = float((labor_values @ A.values * x.values).sum())
        C = intermediate_value

    r = S / max(C + V, 1e-10)
    oc = C / max(V, 1e-10)
    sr = S / max(V, 1e-10)

    return {
        "r_classical": float(r),
        "V_variable_capital": float(V),
        "S_surplus": float(S),
        "C_constant_capital": float(C),
        "organic_composition": float(oc),
        "surplus_rate": float(sr),
        "wage_share": float(V / max(V + S, 1e-10)),
    }


def shaikh_profit_rate_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Compute Shaikh profit rate for all available years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year, r_classical, organic_composition, surplus_rate, wage_share.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        va = d.get("value_added")
        x = d.get("total_output")

        if A is None or va is None or x is None:
            continue

        sectors = A.index

        if isinstance(va, pd.DataFrame):
            comp_rows = [r for r in va.index if "V001" in str(r)]
            if comp_rows:
                wages = va.loc[comp_rows[0]].reindex(sectors).fillna(0)
            else:
                wages = va.iloc[0].reindex(sectors).fillna(0)
            va_total = va.sum(axis=0).reindex(sectors).fillna(0)
        else:
            wages = va.reindex(sectors).fillna(0) * 0.5
            va_total = va.reindex(sectors).fillna(0)

        x_aligned = x.reindex(sectors).fillna(0)
        labor_coeff = (wages / x_aligned.replace(0, np.nan)).fillna(0)

        try:
            result = shaikh_profit_rate_single(A, labor_coeff, wages, x_aligned)
            result["year"] = year
            rows.append(result)
        except Exception:
            continue

    return pd.DataFrame(rows).set_index("year")


def ltpf_regression(
    profit_ts: pd.DataFrame,
    rate_column: str = "r_classical",
) -> Dict[str, float]:
    """OLS regression of log(profit rate) on time to test secular tendency.

    Args:
        profit_ts: DataFrame with profit rate time series.
        rate_column: Column name for profit rate.

    Returns:
        Dict with slope, t_stat, p_value, r_squared, interpretation.
    """
    if rate_column not in profit_ts.columns:
        return {"slope": np.nan, "t_stat": np.nan, "p_value": np.nan, "r_squared": np.nan}

    rates = profit_ts[rate_column].dropna()
    rates = rates[rates > 0]
    if len(rates) < 3:
        return {"slope": np.nan, "t_stat": np.nan, "p_value": np.nan, "r_squared": np.nan}

    years = np.array(rates.index, dtype=float)
    log_rates = np.log(rates.values)

    n = len(years)
    x_mean = years.mean()
    y_mean = log_rates.mean()
    ss_xy = ((years - x_mean) * (log_rates - y_mean)).sum()
    ss_xx = ((years - x_mean) ** 2).sum()

    slope = ss_xy / max(ss_xx, 1e-15)
    intercept = y_mean - slope * x_mean

    predicted = slope * years + intercept
    ss_res = ((log_rates - predicted) ** 2).sum()
    ss_tot = ((log_rates - y_mean) ** 2).sum()
    r_squared = 1 - ss_res / max(ss_tot, 1e-15)

    se_slope = np.sqrt(ss_res / max(n - 2, 1) / max(ss_xx, 1e-15))
    t_stat = slope / max(se_slope, 1e-15)

    from scipy import stats as sp_stats
    p_value = 2 * (1 - sp_stats.t.cdf(abs(t_stat), n - 2))

    interpretation = "falling" if slope < 0 else "rising"

    logger.info(f"LTPF regression: slope={slope:.6f}/yr ({interpretation}), p={p_value:.4f}")

    return {
        "slope_per_year": float(slope),
        "annual_pct_change": float(slope * 100),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "r_squared": float(r_squared),
        "n_observations": n,
        "interpretation": interpretation,
    }
