"""Build the Parquet cache and site_manifest.json for the Leontief website.

For each year 1997-2024, reads the source pickle and writes 7 labeled
DataFrames (Use, Supply, A, A_square, L, VA, FD) to:
    site_data/cache/{year}__{matrix}.parquet

For each of the 12 Outputs/Data workbooks, reads the first sheet, normalizes
to a tidy DataFrame, and writes:
    site_data/cache/{series_key}.parquet

Finally emits site_data/site_manifest.json with coverage, tables[], series[],
and an empty studies[] placeholder.

Run:  python webapp/data_pipeline/build_cache.py

Parquet convention: index is reset and stored as a column named "__index__" so
that the labeled matrix (sector codes as row labels) roundtrips exactly:
    df -> reset_index -> to_parquet -> read_parquet -> set_index("__index__")
This preserves both index and column labels for the matrix Explorer.
"""
from __future__ import annotations

import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
WEBAPP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAPP_ROOT))
from app import config as C  # noqa: E402

# ---------------------------------------------------------------------------
# Series registry: maps series_key -> (filename, human label, FD-col info)
# ---------------------------------------------------------------------------
SERIES_REGISTRY: dict[str, tuple[str, str]] = {
    "multiplier_timeseries":       ("multiplier_timeseries_1997_2024.xlsx",     "Output multipliers by sector, 1997-2024"),
    "employment_multipliers":      ("employment_multipliers_1997_2024.xlsx",     "Employment multipliers by sector, 1997-2024"),
    "ghosh_forward_multipliers":   ("ghosh_forward_multipliers_1997_2024.xlsx",  "Ghosh forward multipliers by sector, 1997-2024"),
    "type2_multipliers":           ("type2_multipliers_1997_2024.xlsx",          "Type II multipliers by sector, 1997-2024"),
    "labor_share":                 ("labor_share_1997_2024.xlsx",                "Labor share of value added, 1997-2024"),
    "wage_share_timeseries":       ("wage_share_timeseries_1997_2024.xlsx",      "Wage share time series, 1997-2024"),
    "import_dependency":           ("import_dependency_1997_2024.xlsx",          "Import dependency ratio, 1997-2024"),
    "deindustrialization":         ("deindustrialization_1997_2024.xlsx",        "Deindustrialization indicators, 1997-2024"),
    "financialization":            ("financialization_1997_2024.xlsx",           "Financialization indicators, 1997-2024"),
    "structural_change":           ("structural_change_1997_2024.xlsx",          "Structural change metrics, 1997-2024"),
    "topology_timeseries":         ("topology_timeseries.xlsx",                  "I-O network topology metrics, 1997-2024"),
    "vintage_multiplier_comparison": ("vintage_multiplier_comparison.xlsx",      "Vintage multiplier comparison, 1997-2024"),
}

# Human-readable matrix labels
MATRIX_LABELS: dict[str, str] = {
    "Use":     "Use Table (commodity x industry)",
    "Supply":  "Supply Table (commodity x industry)",
    "A":       "Direct Requirements (A matrix, non-square 70x71)",
    "A_square":"Direct Requirements (A matrix, squared to intersection)",
    "L":       "Total Requirements / Leontief Inverse (L matrix, 71x71)",
    "VA":      "Value Added (V-codes x industries)",
    "FD":      "Final Demand (industries/commodities x F-codes)",
}

# Provenance templates
PROVENANCE_TPL: dict[str, str] = {
    "Use":     "BEA Use_IxI_Summary_{year}.json (use_table)",
    "Supply":  "BEA Supply_IxI_Summary_{year}.json (supply_table)",
    "A":       "BEA derived A_matrix (direct requirements, non-square 70x71); see §3 of WEBSITE_BUILD_PLAN.md",
    "A_square":"BEA derived A_matrix reindexed to row∩col intersection (square variant)",
    "L":       "BEA Total_Requirements_IxI_Summary_{year}.json (L_matrix, 71x71 Leontief inverse)",
    "VA":      "BEA value_added table (V-codes: V001 compensation, V003 taxes, VABAS, VAPRO)",
    "FD":      "BEA final_demand table (F-codes: F010 PCE, F02x investment, F04x exports, F06-10x government)",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Parquet helpers — labeled matrix roundtrip
# ---------------------------------------------------------------------------

def write_matrix_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a labeled DataFrame to parquet with index as '__index__' column."""
    out = df.copy()
    out.index.name = "__index__"
    out = out.reset_index()
    out.columns = [str(c) for c in out.columns]
    out.to_parquet(path, index=False)


def read_matrix_parquet(path: Path) -> pd.DataFrame:
    """Read a labeled matrix parquet and restore the index."""
    df = pd.read_parquet(path)
    if "__index__" in df.columns:
        df = df.set_index("__index__")
        df.index.name = None
    return df


def write_tidy_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a tidy (non-matrix) DataFrame to parquet without special index treatment."""
    df = df.copy()
    df.columns = [str(c) for c in df.columns]
    df.to_parquet(path, index=False)


# ---------------------------------------------------------------------------
# Table download URL helper
# ---------------------------------------------------------------------------

# DNA: CSV / XLSX / Parquet only — no JSON.
def table_downloads(year: int, matrix: str) -> dict[str, str]:
    base = f"/api/table/{year}/{matrix}"
    return {fmt: f"{base}.{fmt}" for fmt in ("csv", "xlsx", "parquet")}


def series_downloads(key: str) -> dict[str, str]:
    return {fmt: f"/api/series/{key}.{fmt}" for fmt in ("csv", "xlsx", "parquet")}


# ---------------------------------------------------------------------------
# Pickle loader
# ---------------------------------------------------------------------------

def load_pickle(year: int) -> dict:
    p = C.PROCESSED_DIR / f"year_{year}.pkl"
    with open(p, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Matrix extractor
# ---------------------------------------------------------------------------

def extract_matrices(data: dict, year: int) -> dict[str, Optional[pd.DataFrame]]:
    """Extract the 7 matrices from a year's pickle dict."""
    mats: dict[str, Optional[pd.DataFrame]] = {}

    mats["Use"]    = data["use_table"]
    mats["Supply"] = data["supply_table"]

    a = data["A_matrix"]
    mats["A"] = a

    # A_square: reindex to intersection of row and column index
    common = a.index.intersection(a.columns)
    mats["A_square"] = a.loc[common, common]

    mats["L"]  = data["L_matrix"]
    mats["VA"] = data["value_added"]
    mats["FD"] = data["final_demand"]

    return mats


# ---------------------------------------------------------------------------
# Series normalizer
# ---------------------------------------------------------------------------

def normalize_series(df: pd.DataFrame) -> pd.DataFrame:
    """Light normalization for tidy series DataFrames."""
    # Drop fully-unnamed columns (e.g. index artifacts from Excel)
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed: ?\d+$")]
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build() -> None:
    C.ensure_dirs()

    manifest: dict = {
        "generated": _now(),
        "coverage": {
            "years": list(C.BEA_YEARS),
            "sector_count": C.SECTOR_COUNT,
            "classification": "BEA Summary",
        },
        "tables": [],
        "series": [],
        "studies": [],  # placeholder; populated by run_studies.py later
    }

    tables_built = 0
    tables_missing: list[str] = []

    # ------------------------------------------------------------------
    # P1: Matrix parquets (7 matrices x 28 years)
    # ------------------------------------------------------------------
    print("== Building matrix parquets ==")
    for year in C.BEA_YEARS:
        print(f"  {year}", end=" ", flush=True)
        data = load_pickle(year)

        matrices = extract_matrices(data, year)
        for matrix_key, df in matrices.items():
            if df is None or df.empty:
                print(f"\n    WARNING: {year}__{matrix_key} is empty — skipping")
                tables_missing.append(f"{year}__{matrix_key}")
                continue

            parquet_name = f"{year}__{matrix_key}.parquet"
            parquet_path = C.CACHE_DIR / parquet_name
            write_matrix_parquet(df, parquet_path)

            nrows, ncols = df.shape
            is_square = (nrows == ncols)
            label_tmpl = MATRIX_LABELS.get(matrix_key, matrix_key)
            label = f"{label_tmpl}, {year}"
            prov_tmpl = PROVENANCE_TPL.get(matrix_key, "BEA pkl")
            provenance = prov_tmpl.format(year=year) if "{year}" in prov_tmpl else prov_tmpl

            entry: dict = {
                "key":       f"{year}__{matrix_key}",
                "year":      year,
                "matrix":    matrix_key,
                "label":     label,
                "rows":      nrows,
                "cols":      ncols,
                "square":    is_square,
                "parquet":   f"cache/{parquet_name}",
                "downloads": table_downloads(year, matrix_key),
                "provenance": provenance,
            }
            manifest["tables"].append(entry)
            tables_built += 1

        print("OK")

    print(f"\nMatrix parquets written: {tables_built} (missing: {len(tables_missing)})")
    if tables_missing:
        print(f"  Missing: {tables_missing}")

    # ------------------------------------------------------------------
    # P2: Series parquets (12 workbooks)
    # ------------------------------------------------------------------
    print("\n== Building series parquets ==")
    series_built = 0
    series_skipped: list[str] = []

    for key, (filename, label) in SERIES_REGISTRY.items():
        src_path = C.OUTPUTS_DATA / filename
        if not src_path.exists():
            print(f"  SKIP  {key}: file not found ({filename})")
            series_skipped.append(key)
            continue

        try:
            xl = pd.ExcelFile(src_path)
            df = xl.parse(xl.sheet_names[0])
            df = normalize_series(df)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {key}: {e} — skipping")
            series_skipped.append(key)
            continue

        parquet_name = f"{key}.parquet"
        parquet_path = C.CACHE_DIR / parquet_name
        write_tidy_parquet(df, parquet_path)

        cols = [str(c) for c in df.columns]
        entry: dict = {
            "key":      key,
            "label":    label,
            "parquet":  f"cache/{parquet_name}",
            "source":   f"Outputs/Data/{filename}",
            "columns":  cols,
            "rows":     int(len(df)),
            "downloads": series_downloads(key),
        }
        manifest["series"].append(entry)
        series_built += 1
        print(f"  OK    {key}: {df.shape[0]}x{df.shape[1]} <- {filename}")

    print(f"\nSeries parquets written: {series_built} (skipped: {len(series_skipped)})")
    if series_skipped:
        print(f"  Skipped: {series_skipped}")

    # ------------------------------------------------------------------
    # Write manifest
    # ------------------------------------------------------------------
    manifest_path = C.get_manifest_path()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\nWrote {manifest_path}")
    print(f"  tables: {len(manifest['tables'])}  series: {len(manifest['series'])}  studies: 0 (placeholder)")

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    print("\n== Verification ==")

    # 1. L matrix for 2002 roundtrips to 71x71 numeric
    l_path = C.CACHE_DIR / "2002__L.parquet"
    assert l_path.exists(), f"2002__L.parquet not found at {l_path}"
    df_l = read_matrix_parquet(l_path)
    assert df_l.shape == (71, 71), f"Expected (71,71), got {df_l.shape}"
    assert df_l.dtypes.apply(lambda dt: dt == "float64").all(), \
        f"Non-float dtypes: {df_l.dtypes.unique()}"
    print(f"  [PASS] 2002__L.parquet roundtrips to {df_l.shape} float64 matrix")

    # 2. Manifest tables count (target 196 = 28*7)
    n_tables = len(manifest["tables"])
    expected = 28 * 7
    if n_tables == expected:
        print(f"  [PASS] manifest tables count = {n_tables} (== 28*7)")
    else:
        print(f"  [NOTE] manifest tables count = {n_tables} (expected {expected}; diff: {expected - n_tables} missing)")

    # 3. Every parquet referenced in manifest actually exists
    bad_parquets: list[str] = []
    for entry in manifest["tables"]:
        p = C.SITE_DATA / entry["parquet"]
        if not p.exists():
            bad_parquets.append(entry["parquet"])
    for entry in manifest["series"]:
        p = C.SITE_DATA / entry["parquet"]
        if not p.exists():
            bad_parquets.append(entry["parquet"])
    if bad_parquets:
        print(f"  [FAIL] {len(bad_parquets)} missing parquets: {bad_parquets[:5]}...")
    else:
        print(f"  [PASS] all {n_tables + series_built} referenced parquets exist on disk")

    # 4. Cache dir size
    cache_files = list(C.CACHE_DIR.glob("*.parquet"))
    total_bytes = sum(f.stat().st_size for f in cache_files)
    total_mb = total_bytes / (1024 * 1024)
    print(f"  Cache dir: {len(cache_files)} files, {total_mb:.1f} MB total")

    # 5. Sector sample + agg15 distribution
    sectors_path = C.get_sectors_path()
    if sectors_path.exists():
        with open(sectors_path, encoding="utf-8") as f:
            sdata = json.load(f)
        print("\n  Sample sectors:")
        for s in sdata["sectors"][:3]:
            print(f"    {s['code']}: {s['name']}  [{s['agg15']}]")
        print("\n  agg15 distribution:")
        agg15 = sdata["agg15"]
        for grp, codes in agg15.items():
            print(f"    {grp:40s}: {len(codes):2d}")
    else:
        print("  sectors.json not found — run build_sectors.py first")


if __name__ == "__main__":
    build()
