"""Master script: Run all analytical modules across 28 years (1997-2024).

Loads parsed I-O data, computes multipliers, linkages, value analysis,
structural decomposition, Ghosh model, wage shares, and structural
change indices for every available year. Exports to Excel.

Usage:
    python run_historical_analysis.py
"""

import sys
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from enhanced_linkages import enhanced_linkage_indices
from price_model import cost_push_prices
from value_analysis import vertically_integrated_labor
from structural_decomposition import structural_decomposition_polar, sda_summary
from ghosh_model import allocation_coefficients, ghosh_inverse, forward_multipliers
from structural_change import lilien_index, cosine_similarity, absolute_structural_change, multiplier_concentration
from functional_distribution import wage_share_by_sector, aggregate_wage_share
from regime_metadata import get_regime, get_breaks_between, regime_annotation
from closed_model import close_model, type2_multipliers, type1_multipliers, induced_effects
from employment_analysis import compensation_coefficients, employment_multipliers
from import_analysis import aggregate_import_dependency
from structural_narratives import compute_all_narratives
from gdp_industry_parser import true_labor_share_timeseries

PROJECT = Path(__file__).parent.parent.parent
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "annual_71"
OUTPUTS = PROJECT / "Outputs" / "Data"

YEARS = list(range(1997, 2025))


def load_year(year: int) -> dict:
    """Load a single year's parsed I-O data."""
    path = PROCESSED / f"year_{year}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def compute_multipliers_timeseries(data: dict) -> pd.DataFrame:
    """Output multipliers (column sums of L) for all years."""
    print("\n--- Output Multipliers Time Series ---")
    rows = []
    for year in sorted(data.keys()):
        L = data[year]["L_matrix"]
        mult = L.sum(axis=0)
        mult.name = year
        rows.append(mult)
    df = pd.DataFrame(rows)
    df.index.name = "year"
    print(f"  {len(df)} years, {df.shape[1]} sectors")
    print(f"  Mean multiplier: {df.mean().mean():.4f}")
    return df


def compute_linkage_timeseries(data: dict) -> dict:
    """Enhanced linkage indices for all years."""
    print("\n--- Enhanced Linkage Classification ---")
    results = {}
    for year in sorted(data.keys()):
        L = data[year]["L_matrix"]
        linkages = enhanced_linkage_indices(L)
        results[year] = linkages
    # Summary: count key sectors per year
    counts = {y: (df["sector_type"] == "Key sector").sum() for y, df in results.items()}
    print(f"  Key sectors: min={min(counts.values())}, max={max(counts.values())}")
    return results


def compute_wage_share_timeseries(data: dict) -> pd.DataFrame:
    """Aggregate wage share for each year."""
    print("\n--- Wage Share Time Series ---")
    rows = []
    for year in sorted(data.keys()):
        va = data[year]["value_added"]
        if va.empty:
            continue
        ws = aggregate_wage_share(va)
        rows.append({"year": year, "wage_share": ws})
    df = pd.DataFrame(rows).set_index("year")
    if len(df) > 0:
        print(f"  Range: {df['wage_share'].min():.4f} to {df['wage_share'].max():.4f}")
        print(f"  1997: {df.loc[1997, 'wage_share']:.4f}" if 1997 in df.index else "")
        latest = df.index.max()
        print(f"  {latest}: {df.loc[latest, 'wage_share']:.4f}")
    return df


def compute_structural_change(data: dict) -> pd.DataFrame:
    """Structural change metrics between consecutive years."""
    print("\n--- Structural Change Metrics ---")
    rows = []
    years = sorted(data.keys())
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        A0 = data[y0].get("A_matrix")
        A1 = data[y1].get("A_matrix")
        if A0 is None or A1 is None or A0.empty or A1.empty:
            continue

        cs = cosine_similarity(A0, A1)
        asc = absolute_structural_change(A0, A1)

        # Lilien index from total output
        x0 = data[y0].get("total_output", pd.Series(dtype=float))
        x1 = data[y1].get("total_output", pd.Series(dtype=float))
        li = lilien_index(x0, x1) if not x0.empty and not x1.empty else np.nan

        rows.append({
            "year_from": y0, "year_to": y1,
            "cosine_similarity": cs,
            "absolute_change": asc,
            "lilien_index": li,
        })
    df = pd.DataFrame(rows)
    if len(df) > 0:
        print(f"  Cosine similarity range: {df['cosine_similarity'].min():.6f} - {df['cosine_similarity'].max():.6f}")
        # Find year with most change
        min_cos = df.loc[df["cosine_similarity"].idxmin()]
        print(f"  Most structural change: {int(min_cos['year_from'])}-{int(min_cos['year_to'])} (cos={min_cos['cosine_similarity']:.6f})")
    return df


def compute_sda_pairs(data: dict) -> pd.DataFrame:
    """Structural decomposition between consecutive years."""
    print("\n--- Structural Decomposition (Polar) ---")
    rows = []
    years = sorted(data.keys())
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        A0 = data[y0].get("A_matrix")
        A1 = data[y1].get("A_matrix")
        fd0 = data[y0].get("final_demand")
        fd1 = data[y1].get("final_demand")
        if A0 is None or A1 is None or A0.empty or A1.empty:
            continue
        if fd0 is None or fd1 is None or fd0.empty or fd1.empty:
            continue

        # Aggregate final demand to sector level
        common_rows = A0.index.intersection(A1.index)
        common_fd = fd0.columns.intersection(fd1.columns)
        f0 = fd0.loc[fd0.index.intersection(common_rows), common_fd].sum(axis=1)
        f1 = fd1.loc[fd1.index.intersection(common_rows), common_fd].sum(axis=1)

        # Align A matrices — use only rows/cols present in BOTH A matrices
        shared_sectors = sorted(
            set(A0.index) & set(A0.columns) & set(A1.index) & set(A1.columns)
        )
        if len(shared_sectors) < 10:
            continue
        A0a = A0.loc[shared_sectors, shared_sectors].fillna(0)
        A1a = A1.loc[shared_sectors, shared_sectors].fillna(0)
        f0a = f0.reindex(shared_sectors).fillna(0)
        f1a = f1.reindex(shared_sectors).fillna(0)

        try:
            result = structural_decomposition_polar(A0a, A1a, f0a, f1a)
            rows.append({
                "year_from": y0, "year_to": y1,
                "total_change": result["total_change"].sum(),
                "demand_effect": result["demand_effect"].sum(),
                "technology_effect": result["technology_effect"].sum(),
            })
        except Exception as e:
            print(f"  SDA {y0}-{y1} failed: {e}")

    df = pd.DataFrame(rows)
    if len(df) > 0:
        print(f"  {len(df)} year-pairs computed")
        print(f"  Demand effect range: {df['demand_effect'].min():.0f} to {df['demand_effect'].max():.0f}")
    return df


def compute_ghosh_timeseries(data: dict) -> pd.DataFrame:
    """Forward (supply-side) multipliers for all years."""
    print("\n--- Ghosh Forward Multipliers ---")
    rows = []
    for year in sorted(data.keys()):
        use = data[year].get("use_table")
        x = data[year].get("total_output")
        if use is None or x is None or use.empty or x.empty:
            continue
        try:
            L = data[year].get("L_matrix")
            B = allocation_coefficients(use, x, L_matrix=L)
            G = ghosh_inverse(B)
            fm = forward_multipliers(G)
            fm.name = year
            rows.append(fm)
        except Exception as e:
            print(f"  {year}: Ghosh failed: {e}")
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    if not df.empty:
        df.index.name = "year"
        print(f"  {len(df)} years, mean forward mult: {df.mean().mean():.4f}")
    return df


def export_results(
    multipliers: pd.DataFrame,
    wage_shares: pd.DataFrame,
    structural: pd.DataFrame,
    sda: pd.DataFrame,
    ghosh: pd.DataFrame,
):
    """Export all results to Druck-compliant single-sheet Excel files."""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    print("\n--- Exporting Results ---")

    files = {
        "multiplier_timeseries_1997_2024.xlsx": multipliers,
        "wage_share_timeseries_1997_2024.xlsx": wage_shares,
        "structural_change_1997_2024.xlsx": structural,
        "structural_decomposition_pairs.xlsx": sda,
        "ghosh_forward_multipliers_1997_2024.xlsx": ghosh,
    }

    for name, df in files.items():
        if df is not None and not df.empty:
            path = OUTPUTS / name
            sheet = name.replace(".xlsx", "").replace("_", " ")[:31]
            df.to_excel(path, sheet_name=sheet)
            print(f"  Saved: {name} ({len(df)} rows)")
        else:
            print(f"  Skipped: {name} (empty)")


def main():
    print("=" * 70)
    print("LEONTIEF.IO — HISTORICAL ANALYSIS (1997-2024)")
    print("28 Years of U.S. Input-Output Structure")
    print("=" * 70)

    # Load all years
    print("\nLoading parsed data...")
    data = {}
    for year in YEARS:
        d = load_year(year)
        if d is not None:
            data[year] = d
    print(f"Loaded {len(data)} years: {sorted(data.keys())[0]}-{sorted(data.keys())[-1]}")

    # Run core analyses
    multipliers = compute_multipliers_timeseries(data)
    linkages = compute_linkage_timeseries(data)
    wage_shares = compute_wage_share_timeseries(data)
    structural = compute_structural_change(data)
    sda = compute_sda_pairs(data)
    ghosh = compute_ghosh_timeseries(data)

    # Run new modules
    print("\n--- Employment (Compensation) Multipliers ---")
    emp_rows = []
    for year in sorted(data.keys()):
        d = data[year]
        va, x, L = d.get("value_added"), d.get("total_output"), d.get("L_matrix")
        if va is None or x is None or L is None or va.empty or x.empty or L.empty:
            continue
        try:
            cc = compensation_coefficients(va, x)
            em = employment_multipliers(L, cc)
            em.name = year
            emp_rows.append(em)
        except Exception as e:
            print(f"  {year}: employment failed: {e}")
    emp_mult = pd.DataFrame(emp_rows) if emp_rows else pd.DataFrame()
    if not emp_mult.empty:
        emp_mult.index.name = "year"
        print(f"  {len(emp_mult)} years, mean={emp_mult.mean().mean():.4f}")

    print("\n--- Import Dependency ---")
    imp_rows = []
    for year in sorted(data.keys()):
        fd = data[year].get("final_demand")
        x = data[year].get("total_output")
        if fd is None or x is None or fd.empty or x.empty:
            continue
        dep = aggregate_import_dependency(final_demand=fd, total_output=x)
        imp_rows.append({"year": year, "import_dependency": dep})
    import_dep = pd.DataFrame(imp_rows).set_index("year") if imp_rows else pd.DataFrame()
    if not import_dep.empty:
        print(f"  Range: {import_dep['import_dependency'].min():.4f} - {import_dep['import_dependency'].max():.4f}")

    print("\n--- True Labor Share (GDP-by-Industry) ---")
    true_ls = true_labor_share_timeseries()
    if not true_ls.empty:
        print(f"  Range: {true_ls['labor_share'].min():.4f} - {true_ls['labor_share'].max():.4f}")
        print(f"  2000: {true_ls.loc[2000, 'labor_share']:.4f}" if 2000 in true_ls.index else "")
        latest = true_ls.index.max()
        print(f"  {latest}: {true_ls.loc[latest, 'labor_share']:.4f}")

    print("\n--- Type II (Closed Model) Multipliers ---")
    t2_rows = []
    for year in sorted(data.keys()):
        d = data[year]
        A, use, va, fd, x, L = (d.get("A_matrix"), d.get("use_table"),
            d.get("value_added"), d.get("final_demand"),
            d.get("total_output"), d.get("L_matrix"))
        if any(v is None or (hasattr(v, 'empty') and v.empty) for v in [A, use, va, fd, x, L]):
            continue
        try:
            A_bar, L_bar = close_model(A, use, va, fd, x)
            t2 = type2_multipliers(L_bar)
            t2.name = year
            t2_rows.append(t2)
        except Exception as e:
            print(f"  {year}: Type II failed: {e}")
    type2_df = pd.DataFrame(t2_rows) if t2_rows else pd.DataFrame()
    if not type2_df.empty:
        type2_df.index.name = "year"
        print(f"  {len(type2_df)} years, mean Type II: {type2_df.mean().mean():.4f}")

    print("\n--- Structural Narratives ---")
    narratives = compute_all_narratives(data)
    for name, df in narratives.items():
        if not df.empty:
            print(f"  {name}: {len(df)} rows")

    # Export all results
    print("\n--- Exporting Results ---")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    all_files = {
        "multiplier_timeseries_1997_2024.xlsx": multipliers,
        "wage_share_timeseries_1997_2024.xlsx": wage_shares,
        "structural_change_1997_2024.xlsx": structural,
        "structural_decomposition_pairs.xlsx": sda,
        "ghosh_forward_multipliers_1997_2024.xlsx": ghosh,
        "employment_multipliers_1997_2024.xlsx": emp_mult,
        "import_dependency_1997_2024.xlsx": import_dep,
        "true_labor_share_1997_2024.xlsx": true_ls,
        "type2_multipliers_1997_2024.xlsx": type2_df,
        "financialization_1997_2024.xlsx": narratives.get("financialization", pd.DataFrame()),
        "deindustrialization_1997_2024.xlsx": narratives.get("deindustrialization", pd.DataFrame()),
        "labor_share_1997_2024.xlsx": narratives.get("labor_share", pd.DataFrame()),
        "key_sector_stability.xlsx": narratives.get("key_sector_stability", pd.DataFrame()),
        "covid_structural_shift.xlsx": narratives.get("covid_shift", pd.DataFrame()),
    }

    for name, df in all_files.items():
        if df is not None and not df.empty:
            path = OUTPUTS / name
            sheet = name.replace(".xlsx", "").replace("_", " ")[:31]
            df.to_excel(path, sheet_name=sheet)
            print(f"  Saved: {name} ({len(df)} rows)")
        else:
            print(f"  Skipped: {name} (empty)")

    # Master annotated output
    print("\n--- Master Regime-Annotated Output ---")
    master_rows = []
    for year in sorted(data.keys()):
        row = {"year": year, "regime": regime_annotation(year)}
        if not multipliers.empty and year in multipliers.index:
            row["mean_multiplier"] = multipliers.loc[year].mean()
        if not wage_shares.empty and year in wage_shares.index:
            row["wage_share"] = wage_shares.loc[year, "wage_share"]
        if not import_dep.empty and year in import_dep.index:
            row["import_dependency"] = import_dep.loc[year, "import_dependency"]
        fin = narratives.get("financialization", pd.DataFrame())
        if not fin.empty and year in fin.index:
            row["financial_va_share"] = fin.loc[year, "financial_va_share"]
        deind = narratives.get("deindustrialization", pd.DataFrame())
        if not deind.empty and year in deind.index:
            row["manufacturing_va_share"] = deind.loc[year, "manufacturing_va_share"]
        ls = narratives.get("labor_share", pd.DataFrame())
        if not ls.empty and year in ls.index:
            row["labor_share_use_table"] = ls.loc[year, "labor_share"]
        if not true_ls.empty and year in true_ls.index:
            row["true_labor_share"] = true_ls.loc[year, "labor_share"]
        if not type2_df.empty and year in type2_df.index:
            row["mean_type2_multiplier"] = type2_df.loc[year].mean()
        master_rows.append(row)

    master = pd.DataFrame(master_rows).set_index("year")
    master_path = OUTPUTS / "comprehensive_regime_annotated.xlsx"
    master.to_excel(master_path, sheet_name="Master")
    print(f"  Saved: comprehensive_regime_annotated.xlsx ({len(master)} rows)")

    # Regime annotations
    print("\n--- Regime Context ---")
    for year in [1997, 2002, 2007, 2012, 2017, 2020, 2024]:
        if year in data:
            print(f"  {year}: {regime_annotation(year)}")

    breaks = get_breaks_between(1997, 2024)
    print(f"\n  Regime breaks in period: {len(breaks)}")
    for b in breaks:
        print(f"    {b.year}: [{b.severity}] {b.name}")

    print("\n" + "=" * 70)
    print("HISTORICAL ANALYSIS COMPLETE")
    print(f"  {len(all_files)} output files generated")
    print("=" * 70)


if __name__ == "__main__":
    main()
