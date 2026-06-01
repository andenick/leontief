"""Cross-cutting structural narrative indices for the U.S. economy.

Computes theme-based indices tracking major structural transformations:
- Financialization
- Deindustrialization
- Labor share decline
- Key sector stability
- COVID structural disruption

Uses 28 years of parsed I-O data (1997-2024).
"""

import numpy as np
import pandas as pd
from enhanced_linkages import enhanced_linkage_indices
import logging

logger = logging.getLogger(__name__)

# BEA 71-sector codes for financial industries
FINANCIAL_SECTORS = ["521CI", "523", "524", "525"]

# Manufacturing sectors (NAICS 31-33)
MANUFACTURING_SECTORS = [
    "321", "327", "331", "332", "333", "334", "335",
    "3361MV", "3364OT", "337", "339",
    "311FT", "313TT", "315AL", "322", "323", "324", "325", "326",
]


def financialization_index(data_by_year: dict) -> pd.DataFrame:
    """Track financial sector's share of the economy over time.

    Measures: financial sectors' share of total value added.
    """
    rows = []
    for year in sorted(data_by_year.keys()):
        va = data_by_year[year].get("value_added")
        if va is None or va.empty:
            continue
        total_va = va.sum(axis=0)
        fin_cols = [c for c in total_va.index if c in FINANCIAL_SECTORS]
        fin_va = total_va.reindex(fin_cols).sum()
        total = total_va.sum()
        rows.append({
            "year": year,
            "financial_va_share": fin_va / total if total > 0 else 0,
            "financial_va": fin_va,
            "total_va": total,
        })
    return pd.DataFrame(rows).set_index("year")


def deindustrialization_index(data_by_year: dict) -> pd.DataFrame:
    """Track manufacturing sector's declining share over time."""
    rows = []
    for year in sorted(data_by_year.keys()):
        va = data_by_year[year].get("value_added")
        x = data_by_year[year].get("total_output")
        if va is None or va.empty:
            continue

        total_va = va.sum(axis=0)
        mfg_cols = [c for c in total_va.index if c in MANUFACTURING_SECTORS]
        mfg_va = total_va.reindex(mfg_cols).sum()
        total = total_va.sum()

        mfg_output = x.reindex(mfg_cols).sum() if x is not None and not x.empty else 0
        total_output = x.sum() if x is not None and not x.empty else 0

        rows.append({
            "year": year,
            "manufacturing_va_share": mfg_va / total if total > 0 else 0,
            "manufacturing_output_share": mfg_output / total_output if total_output > 0 else 0,
        })
    return pd.DataFrame(rows).set_index("year")


def labor_share_timeseries(data_by_year: dict) -> pd.DataFrame:
    """Track compensation share of value added (functional distribution)."""
    rows = []
    for year in sorted(data_by_year.keys()):
        va = data_by_year[year].get("value_added")
        if va is None or va.empty:
            continue

        comp_row = None
        for idx in va.index:
            if "V001" in str(idx):
                comp_row = idx
                break
        if comp_row is None:
            continue

        total_comp = va.loc[comp_row].sum()
        # Use VABAS or sum of V001+V003 for total VA
        va_total = 0
        for idx in va.index:
            if "VABAS" in str(idx) or "VAPRO" in str(idx):
                va_total = va.loc[idx].sum()
                break
        if va_total == 0:
            va_total = va.sum().sum()

        rows.append({
            "year": year,
            "labor_share": total_comp / va_total if va_total > 0 else 0,
            "total_compensation": total_comp,
            "total_va": va_total,
        })
    return pd.DataFrame(rows).set_index("year")


def key_sector_stability(data_by_year: dict) -> pd.DataFrame:
    """Count how many years each sector is classified as 'Key'.

    A sector is 'Key' when both backward and forward linkage indices > 1.
    Stable key sectors drive the economy persistently.
    """
    sector_counts = {}
    total_years = 0

    for year in sorted(data_by_year.keys()):
        L = data_by_year[year].get("L_matrix")
        if L is None or L.empty:
            continue
        total_years += 1
        linkages = enhanced_linkage_indices(L)
        key = linkages[linkages["sector_type"] == "Key sector"]
        for sector in key.index:
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

    result = pd.DataFrame([
        {"sector": s, "years_as_key": c, "pct_of_years": c / total_years * 100}
        for s, c in sector_counts.items()
    ])
    if not result.empty:
        result = result.sort_values("years_as_key", ascending=False).set_index("sector")
    return result


def covid_structural_shift(data_by_year: dict) -> pd.DataFrame:
    """Compare 2019 vs 2020 A-matrix coefficients to identify COVID disruptions.

    Returns sectors with largest absolute change in input structure.
    """
    if 2019 not in data_by_year or 2020 not in data_by_year:
        return pd.DataFrame()

    A_2019 = data_by_year[2019].get("A_matrix")
    A_2020 = data_by_year[2020].get("A_matrix")
    if A_2019 is None or A_2020 is None or A_2019.empty or A_2020.empty:
        return pd.DataFrame()

    common = sorted(set(A_2019.index) & set(A_2019.columns) & set(A_2020.index) & set(A_2020.columns))
    diff = (A_2020.loc[common, common] - A_2019.loc[common, common]).abs()

    # Mean absolute change per sector (as buyer = column)
    col_change = diff.mean(axis=0).sort_values(ascending=False)
    col_change.name = "mean_abs_change_as_buyer"

    # Mean absolute change per sector (as seller = row)
    row_change = diff.mean(axis=1).sort_values(ascending=False)
    row_change.name = "mean_abs_change_as_seller"

    result = pd.DataFrame({
        "change_as_buyer": col_change,
        "change_as_seller": row_change,
        "total_change": col_change + row_change,
    }).sort_values("total_change", ascending=False)

    return result


def compute_all_narratives(data_by_year: dict) -> dict[str, pd.DataFrame]:
    """Run all structural narrative analyses."""
    logger.info("Computing structural narratives...")

    results = {
        "financialization": financialization_index(data_by_year),
        "deindustrialization": deindustrialization_index(data_by_year),
        "labor_share": labor_share_timeseries(data_by_year),
        "key_sector_stability": key_sector_stability(data_by_year),
        "covid_shift": covid_structural_shift(data_by_year),
    }

    for name, df in results.items():
        if not df.empty:
            logger.info(f"  {name}: {len(df)} rows")

    return results
