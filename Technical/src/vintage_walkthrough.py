"""Systematic vintage walkthrough — compare all I-O table vintages.

Loads every available vintage (benchmarks + annual), computes
comparisons, and generates comprehensive output.

Usage:
    python vintage_walkthrough.py
"""

import sys
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from vintage_catalog import (
    ALL_BENCHMARKS, ANNUAL_SYSTEM, sector_count_timeline,
    table_type_evolution, CLASSIFICATION_TIMELINE,
)
from regime_metadata import BREAKS, regime_annotation

PROJECT = Path(__file__).parent.parent.parent
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "annual_71"
IO_DIR = PROJECT / "Inputs" / "bea_api" / "io_tables"
OUTPUTS = PROJECT / "Outputs" / "Data"


def load_annual_years() -> dict:
    """Load all 28 annual pickle files."""
    data = {}
    for year in range(1997, 2025):
        path = PROCESSED / f"year_{year}.pkl"
        if path.exists():
            with open(path, "rb") as f:
                data[year] = pickle.load(f)
    return data


def load_sector_level_data() -> dict:
    """Load 15-sector (Sector level) data from API JSONs."""
    result = {}
    req_file = IO_DIR / "Total_Requirements_IxI_Sector_ALL.json"
    if not req_file.exists():
        return result

    with open(req_file) as f:
        raw = json.load(f)

    rows = raw["BEAAPI"]["Results"][0]["Data"]
    df = pd.DataFrame(rows)
    df["DataValue"] = pd.to_numeric(df["DataValue"].str.replace(",", ""), errors="coerce")

    for year in df["Year"].unique():
        subset = df[df["Year"] == year]
        # Build sector name mapping
        names = {}
        for _, r in subset.iterrows():
            if r["RowCode"]: names[r["RowCode"]] = r.get("RowDescr", "")
            if r["ColCode"]: names[r["ColCode"]] = r.get("ColDescr", "")

        # Pivot to matrix
        clean = subset[subset["RowCode"].str.strip().astype(bool) &
                       subset["ColCode"].str.strip().astype(bool)]
        matrix = clean.pivot_table(
            index="RowCode", columns="ColCode",
            values="DataValue", aggfunc="first"
        )
        # Filter to square
        common = sorted(set(matrix.index) & set(matrix.columns) - {"T005", ""})
        if len(common) > 5:
            result[int(year)] = {
                "L_matrix": matrix.loc[common, common].fillna(0),
                "sector_names": names,
                "sector_count": len(common),
            }

    return result


def compare_sector_counts() -> pd.DataFrame:
    """Sector count timeline from catalog."""
    rows = sector_count_timeline()
    df = pd.DataFrame(rows)
    print(f"\n=== Sector Count Evolution ({len(df)} benchmarks) ===")
    for _, row in df.iterrows():
        print(f"  {row['year']}: {row['detailed']:>4} detailed, "
              f"{row['summary']:>3} summary  ({row['classification']})")
    return df


def compare_annual_multipliers(annual_data: dict) -> pd.DataFrame:
    """Multiplier statistics for each annual year."""
    rows = []
    for year in sorted(annual_data.keys()):
        L = annual_data[year].get("L_matrix")
        if L is None or L.empty:
            continue
        mult = L.sum(axis=0)
        rows.append({
            "year": year,
            "sectors": L.shape[0],
            "mean_multiplier": mult.mean(),
            "median_multiplier": mult.median(),
            "std_multiplier": mult.std(),
            "min_multiplier": mult.min(),
            "max_multiplier": mult.max(),
            "regime": regime_annotation(year),
        })
    return pd.DataFrame(rows).set_index("year")


def compare_sector_level_multipliers(sector_data: dict) -> pd.DataFrame:
    """15-sector multiplier statistics across years."""
    rows = []
    for year in sorted(sector_data.keys()):
        L = sector_data[year]["L_matrix"]
        mult = L.sum(axis=0)
        rows.append({
            "year": year,
            "sectors": sector_data[year]["sector_count"],
            "mean_multiplier": mult.mean(),
            "min_multiplier": mult.min(),
            "max_multiplier": mult.max(),
        })
    return pd.DataFrame(rows).set_index("year")


def compare_sector_lists_annual(annual_data: dict) -> dict:
    """Check if sector lists are identical across all annual years."""
    sector_sets = {}
    for year in sorted(annual_data.keys()):
        L = annual_data[year].get("L_matrix")
        if L is not None and not L.empty:
            sector_sets[year] = set(L.index.tolist())

    years = sorted(sector_sets.keys())
    if not years:
        return {"consistent": False, "details": "No data"}

    base = sector_sets[years[0]]
    differences = {}
    for year in years[1:]:
        added = sector_sets[year] - base
        removed = base - sector_sets[year]
        if added or removed:
            differences[year] = {"added": sorted(added), "removed": sorted(removed)}

    return {
        "consistent": len(differences) == 0,
        "base_year": years[0],
        "base_sectors": len(base),
        "differences": differences,
    }


def compare_va_structure(annual_data: dict) -> pd.DataFrame:
    """Value-added structure across years."""
    rows = []
    for year in sorted(annual_data.keys()):
        va = annual_data[year].get("value_added")
        if va is None or va.empty:
            continue
        totals = {}
        for idx in va.index:
            totals[str(idx)] = va.loc[idx].sum()
        totals["year"] = year
        rows.append(totals)
    return pd.DataFrame(rows).set_index("year")


def generate_walkthrough_report(
    sector_counts: pd.DataFrame,
    annual_mult: pd.DataFrame,
    sector_mult: pd.DataFrame,
    sector_consistency: dict,
    va_structure: pd.DataFrame,
) -> str:
    """Generate the VINTAGE_WALKTHROUGH.md report."""
    lines = [
        "# U.S. Input-Output Tables: Complete Vintage Walkthrough",
        "",
        "## Overview",
        "",
        f"This document covers {len(ALL_BENCHMARKS)} benchmark tables (1947-2017) "
        f"and {len(annual_mult)} years of annual data (1997-2024).",
        "",
    ]

    # Sector counts
    lines.append("## Sector Count Evolution")
    lines.append("")
    lines.append("| Year | Detailed | Summary | Classification |")
    lines.append("|------|----------|---------|---------------|")
    for _, row in sector_counts.iterrows():
        lines.append(f"| {row['year']} | {row['detailed']} | {row['summary']} | {row['classification']} |")
    lines.append("")

    # Table type evolution
    lines.append("## Table Type Evolution")
    lines.append("")
    lines.append("| Year | Table Types | Make/Use | Import Split | Redefinitions |")
    lines.append("|------|------------|----------|-------------|--------------|")
    for tte in table_type_evolution():
        types_str = ", ".join(tte["types"][:4]) + ("..." if len(tte["types"]) > 4 else "")
        lines.append(f"| {tte['year']} | {types_str} | "
                     f"{'Yes' if tte['has_make_use'] else 'No'} | "
                     f"{'Yes' if tte['has_imports_separate'] else 'No'} | "
                     f"{'Yes' if tte['has_redefinitions'] else 'No'} |")
    lines.append("")

    # Classification timeline
    lines.append("## Classification System Timeline")
    lines.append("")
    for ct in CLASSIFICATION_TIMELINE:
        lines.append(f"- **{ct['years']}**: {ct['system']} — {ct['notes']}")
    lines.append("")

    # Regime breaks
    lines.append("## Methodological Regime Breaks")
    lines.append("")
    for b in sorted(BREAKS, key=lambda x: x.year):
        lines.append(f"- **{b.year}** [{b.severity}]: {b.name} — {b.description[:100]}")
    lines.append("")

    # Annual multiplier summary
    if not annual_mult.empty:
        lines.append("## Annual Multiplier Statistics (71-sector, 1997-2024)")
        lines.append("")
        lines.append("| Year | Mean | Median | Std | Min | Max |")
        lines.append("|------|------|--------|-----|-----|-----|")
        for year, row in annual_mult.iterrows():
            lines.append(f"| {year} | {row['mean_multiplier']:.4f} | "
                        f"{row['median_multiplier']:.4f} | {row['std_multiplier']:.4f} | "
                        f"{row['min_multiplier']:.4f} | {row['max_multiplier']:.4f} |")
        lines.append("")

    # Sector consistency
    lines.append("## Annual Sector Consistency Check")
    lines.append("")
    if sector_consistency["consistent"]:
        lines.append(f"All {len(annual_mult)} years use identical {sector_consistency['base_sectors']}-sector classification.")
    else:
        lines.append(f"Base year ({sector_consistency['base_year']}): {sector_consistency['base_sectors']} sectors")
        for year, diff in sector_consistency["differences"].items():
            lines.append(f"- {year}: added {diff['added']}, removed {diff['removed']}")
    lines.append("")

    # Data availability
    lines.append("## Data Availability in Leontief")
    lines.append("")
    lines.append("| Benchmark | Data? | Files |")
    lines.append("|-----------|-------|-------|")
    for b in ALL_BENCHMARKS:
        status = "Yes" if b.data_in_project else "No"
        files = ", ".join(b.files[:3]) + ("..." if len(b.files) > 3 else "") if b.files else "—"
        lines.append(f"| {b.year} | {status} | {files} |")
    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("VINTAGE WALKTHROUGH — All U.S. I-O Tables (1947-2024)")
    print("=" * 70)

    # 1. Sector count evolution
    sector_counts = compare_sector_counts()

    # 2. Load annual data
    print("\nLoading annual data (71-sector, 1997-2024)...")
    annual_data = load_annual_years()
    print(f"  Loaded {len(annual_data)} years")

    # 3. Load 15-sector data
    print("\nLoading sector-level data (15-sector)...")
    sector_data = load_sector_level_data()
    print(f"  Loaded {len(sector_data)} years")

    # 4. Compare multipliers
    print("\n=== Annual Multiplier Statistics (71-sector) ===")
    annual_mult = compare_annual_multipliers(annual_data)
    print(f"  Mean multiplier range: {annual_mult['mean_multiplier'].min():.4f} - "
          f"{annual_mult['mean_multiplier'].max():.4f}")

    print("\n=== Sector-Level Multipliers (15-sector) ===")
    sector_mult = compare_sector_level_multipliers(sector_data)
    if not sector_mult.empty:
        print(f"  Mean multiplier range: {sector_mult['mean_multiplier'].min():.4f} - "
              f"{sector_mult['mean_multiplier'].max():.4f}")

    # 5. Sector consistency
    print("\n=== Sector Consistency Check ===")
    sector_consistency = compare_sector_lists_annual(annual_data)
    print(f"  Consistent: {sector_consistency['consistent']}")
    if not sector_consistency['consistent']:
        for year, diff in sector_consistency['differences'].items():
            print(f"  {year}: +{diff['added']}, -{diff['removed']}")

    # 6. VA structure
    print("\n=== Value-Added Structure ===")
    va_structure = compare_va_structure(annual_data)
    if not va_structure.empty:
        print(f"  Components tracked: {[c for c in va_structure.columns]}")

    # 7. Generate report
    report = generate_walkthrough_report(
        sector_counts, annual_mult, sector_mult, sector_consistency, va_structure
    )
    report_path = PROJECT / "Technical" / "research" / "VINTAGE_WALKTHROUGH.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved: {report_path}")

    # 8. Export Excel outputs
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    exports = {
        "vintage_sector_counts.xlsx": sector_counts,
        "vintage_multiplier_comparison.xlsx": annual_mult,
        "vintage_15sector_multipliers.xlsx": sector_mult,
        "vintage_va_structure.xlsx": va_structure,
    }

    print("\n--- Exporting ---")
    for name, df in exports.items():
        if df is not None and not df.empty:
            path = OUTPUTS / name
            sheet = name.replace(".xlsx", "").replace("_", " ")[:31]
            df.to_excel(path, sheet_name=sheet)
            print(f"  Saved: {name} ({len(df)} rows)")

    print("\n" + "=" * 70)
    print("VINTAGE WALKTHROUGH COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
