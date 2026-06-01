"""Run all enhanced analytical modules on 2002 BEA benchmark data.

Executes: enhanced linkages, price model, value analysis, sectoral balances.
Exports results to single-sheet Excel files (Druck compliant).

Usage:
    python run_enhanced_analysis.py
"""

import sys
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_linkages import enhanced_linkage_indices, extraction_based_linkages
from price_model import cost_push_prices, price_decomposition
from value_analysis import value_analysis_summary
from sectoral_balances import map_io_to_sectoral_balances

PROJECT = Path(__file__).parent.parent.parent
OUTPUTS = PROJECT / "Outputs" / "Data"
PROCESSED = PROJECT / "Technical" / "data" / "processed"


def load_2002_data():
    """Load all 2002 benchmark data from pickles."""
    with open(PROCESSED / "io_table_2002.pkl", "rb") as f:
        io_table = pickle.load(f)

    with open(OUTPUTS / "industry_by_industry_2002.pkl", "rb") as f:
        ixi = pickle.load(f)

    return io_table, ixi


def run_enhanced_linkages(ixi, io_table):
    """Step 1: Enhanced linkage analysis with CV weighting."""
    print("\n" + "=" * 70)
    print("ENHANCED LINKAGE ANALYSIS (2002)")
    print("=" * 70)

    L = ixi["L_industry"]
    linkages = enhanced_linkage_indices(L)

    # Summary
    counts = linkages["sector_type"].value_counts()
    print(f"\nSector Classification:")
    for stype, count in counts.items():
        print(f"  {stype}: {count}")

    # Top 10 key sectors
    key = linkages[linkages["sector_type"] == "Key sector"]
    if len(key) > 0:
        print(f"\nTop 10 Key Sectors (both indices > 1):")
        top = key.sort_values("backward_index", ascending=False).head(10)
        for idx, row in top.iterrows():
            print(f"  {idx}: BL={row['backward_index']:.3f}, FL={row['forward_index']:.3f}, CV_b={row['backward_cv']:.3f}")

    # Export
    out_path = OUTPUTS / "enhanced_linkages_2002.xlsx"
    linkages.to_excel(out_path, sheet_name="Linkages")
    print(f"\nSaved: {out_path}")

    return linkages


def run_price_model(ixi, io_table):
    """Step 2: Cost-push price model and decomposition."""
    print("\n" + "=" * 70)
    print("PRICE MODEL (2002)")
    print("=" * 70)

    A = ixi["A_industry"]
    x = io_table["total_industry_output"]
    va = io_table["value_added"]

    # Total VA coefficients
    x_safe = x.replace(0, np.nan)
    va_total = va.sum(axis=0)
    va_coeff = (va_total / x_safe).fillna(0)

    # Equilibrium prices
    prices = cost_push_prices(A, va_coeff)
    print(f"\nEquilibrium prices: mean={prices.mean():.4f}, std={prices.std():.4f}")
    print(f"Should be ~1.0 for balanced system")

    # Price decomposition by VA component
    rows = {}
    for code, name in [
        ("V00100", "Compensation"),
        ("V00200", "Taxes"),
        ("V00300", "Gross Operating Surplus"),
    ]:
        rows[name] = (va.loc[code] / x_safe).fillna(0).values

    va_components = pd.DataFrame(rows, index=A.columns).T
    decomp = price_decomposition(A, va_components)

    print(f"\nPrice decomposition (economy-wide averages):")
    for col in decomp.columns:
        if col != "total_price":
            print(f"  {col}: {decomp[col].mean():.4f}")

    # Export
    out_path = OUTPUTS / "price_decomposition_2002.xlsx"
    decomp.to_excel(out_path, sheet_name="Price_Decomposition")
    print(f"\nSaved: {out_path}")

    return prices, decomp


def run_value_analysis(ixi, io_table):
    """Step 3: Marxian value analysis and Pasinetti vertical integration."""
    print("\n" + "=" * 70)
    print("VALUE ANALYSIS (2002)")
    print("=" * 70)

    A = ixi["A_industry"]
    x = io_table["total_industry_output"]
    va = io_table["value_added"]

    # Compensation as labor proxy
    compensation = va.loc["V00100"]
    x_safe = x.replace(0, np.nan)
    labor_coeff = (compensation / x_safe).fillna(0)

    print(f"Labor coefficient: mean={labor_coeff.mean():.4f}")
    print(f"Compensation total: ${compensation.sum():,.0f}M")

    summary = value_analysis_summary(
        A=A,
        labor_coefficients=labor_coeff,
        wages=compensation,
        total_output=x,
    )

    print(f"\nLabor values: mean={summary['labor_value'].mean():.4f}")
    print(f"Rate of surplus value: mean={summary['rate_of_surplus_value'].mean():.3f}")
    print(f"Organic composition: mean={summary['organic_composition'].mean():.3f}")

    # Top sectors by labor value
    print(f"\nTop 10 sectors by labor value (most labor-intensive):")
    top = summary.nlargest(10, "labor_value")
    for idx, row in top.iterrows():
        print(f"  {idx}: LV={row['labor_value']:.4f}, s/v={row['rate_of_surplus_value']:.2f}")

    # Export
    out_path = OUTPUTS / "value_analysis_2002.xlsx"
    summary.to_excel(out_path, sheet_name="Value_Analysis")
    print(f"\nSaved: {out_path}")

    return summary


def run_sectoral_balances(io_table):
    """Step 4: Godley sectoral financial balances."""
    print("\n" + "=" * 70)
    print("SECTORAL FINANCIAL BALANCES (2002)")
    print("=" * 70)

    va = io_table["value_added"]
    fd = io_table["final_demand"]

    # BEA final demand code mapping
    column_mapping = {
        "consumption": ["F01000"],
        "investment": ["F02000", "F06I00", "F07I00", "F08I00", "F09I00"],
        "government": ["F04000"],
        "exports": ["F03000"],
        "imports": ["F05000"],
        "taxes": ["V00200"],
    }

    balances = map_io_to_sectoral_balances(va, fd, column_mapping)

    print(f"\n  Government spending:  ${balances['government_spending']:>12,.0f}M")
    print(f"  Taxes:               ${balances['taxes']:>12,.0f}M")
    print(f"  Government balance:  ${balances['government_balance']:>12,.0f}M")
    print(f"  Consumption:         ${balances['consumption']:>12,.0f}M")
    print(f"  Investment:          ${balances['investment']:>12,.0f}M")
    print(f"  Private balance:     ${balances['private_balance']:>12,.0f}M")
    print(f"  Exports:             ${balances['exports']:>12,.0f}M")
    print(f"  Imports:             ${balances['imports']:>12,.0f}M")
    print(f"  Net exports:         ${balances['net_exports']:>12,.0f}M")
    print(f"  Identity check:      ${balances['identity_check']:>12,.1f}M (should be ~0)")

    # Export
    out_path = OUTPUTS / "sectoral_balances_2002.xlsx"
    pd.DataFrame([balances]).to_excel(out_path, sheet_name="Balances", index=False)
    print(f"\nSaved: {out_path}")

    return balances


def main():
    print("=" * 70)
    print("LEONTIEF.IO — ENHANCED ANALYSIS SUITE")
    print("Running all new analytical modules on 2002 BEA Benchmark")
    print("=" * 70)

    io_table, ixi = load_2002_data()
    print(f"Loaded 2002 data: {len(ixi['industries'])} industries")

    linkages = run_enhanced_linkages(ixi, io_table)
    prices, decomp = run_price_model(ixi, io_table)
    values = run_value_analysis(ixi, io_table)
    balances = run_sectoral_balances(io_table)

    print("\n" + "=" * 70)
    print("ALL ANALYSES COMPLETE")
    print("=" * 70)
    print(f"\nOutputs saved to: {OUTPUTS}")
    print("  - enhanced_linkages_2002.xlsx")
    print("  - price_decomposition_2002.xlsx")
    print("  - value_analysis_2002.xlsx")
    print("  - sectoral_balances_2002.xlsx")


if __name__ == "__main__":
    main()
