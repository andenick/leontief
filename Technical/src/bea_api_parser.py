"""Parse BEA API JSON responses into pandas DataFrames and I-O matrices.

Converts the long-format JSON from the BEA InputOutput API into:
- Leontief inverse (L) matrices
- Use tables (with VA and final demand separated)
- Supply/Make tables
- Derived A matrices (direct requirements)

Usage:
    from bea_api_parser import parse_all_years, parse_requirements_json
    data = parse_all_years()  # Returns dict: year -> IOYearData
"""

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent.parent
IO_DIR = PROJECT / "Inputs" / "bea_api" / "io_tables"
GDP_DIR = PROJECT / "Inputs" / "bea_api" / "gdp_by_industry"
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "annual_71"


@dataclass
class IOYearData:
    """Standardized I-O data for a single year."""
    year: int
    L_matrix: pd.DataFrame              # Total requirements (Leontief inverse) IxI
    use_table: Optional[pd.DataFrame] = None   # Full Use table
    supply_table: Optional[pd.DataFrame] = None  # Full Supply table
    A_matrix: Optional[pd.DataFrame] = None    # Direct requirements (derived)
    value_added: Optional[pd.DataFrame] = None  # VA components × sectors
    final_demand: Optional[pd.DataFrame] = None  # Sectors × FD categories
    total_output: Optional[pd.Series] = None   # Total industry output
    sectors: list = field(default_factory=list)
    sector_names: dict = field(default_factory=dict)


def _load_json(filepath: Path) -> list[dict]:
    """Load BEA API JSON and extract the data rows."""
    with open(filepath) as f:
        raw = json.load(f)
    try:
        return raw["BEAAPI"]["Results"][0]["Data"]
    except (KeyError, IndexError, TypeError):
        logger.warning(f"No data in {filepath.name}")
        return []


def _pivot_matrix(rows: list[dict], row_col="RowCode", col_col="ColCode",
                  val_col="DataValue") -> pd.DataFrame:
    """Pivot long-format BEA data into a matrix."""
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()

    # Clean DataValue — remove commas, handle missing
    df[val_col] = pd.to_numeric(
        df[val_col].str.replace(",", "").str.strip(),
        errors="coerce"
    )

    # Build name mapping from codes to descriptions
    name_map = {}
    for _, r in df.iterrows():
        if r.get("RowCode") and r.get("RowDescr"):
            name_map[r["RowCode"]] = r["RowDescr"]
        if r.get("ColCode") and r.get("ColDescr"):
            name_map[r["ColCode"]] = r["ColDescr"]

    # Filter out blank/empty codes
    df = df[df[row_col].str.strip().astype(bool) & df[col_col].str.strip().astype(bool)]

    matrix = df.pivot_table(
        index=row_col, columns=col_col,
        values=val_col, aggfunc="first"
    )
    return matrix, name_map


def parse_requirements_json(filepath: Path) -> tuple[pd.DataFrame, dict]:
    """Parse a Total Requirements (Leontief inverse) JSON file.

    Returns (L_matrix, name_map) where L_matrix is sectors × sectors.
    """
    rows = _load_json(filepath)
    if not rows:
        return pd.DataFrame(), {}

    matrix, name_map = _pivot_matrix(rows)

    # Filter to industry rows/cols only (exclude totals, notes, blanks)
    # Industry codes are alphanumeric (e.g., "111CA", "3361MV", "GSLG")
    # Exclude rows like "T005" (total), empty strings
    industry_rows = [r for r in matrix.index if r and not r.startswith("T0")]
    industry_cols = [c for c in matrix.columns if c and not c.startswith("T0")]

    # Use intersection for square matrix
    common = sorted(set(industry_rows) & set(industry_cols))
    L = matrix.loc[common, common].fillna(0)

    logger.info(f"  L matrix: {L.shape[0]}×{L.shape[1]} sectors")
    return L, name_map


def parse_use_json(filepath: Path) -> tuple[pd.DataFrame, dict]:
    """Parse a Use of Commodities JSON file.

    Returns (use_table, name_map) — full table including VA rows and FD columns.
    """
    rows = _load_json(filepath)
    if not rows:
        return pd.DataFrame(), {}
    matrix, name_map = _pivot_matrix(rows)
    logger.info(f"  Use table: {matrix.shape[0]}×{matrix.shape[1]}")
    return matrix, name_map


def parse_supply_json(filepath: Path) -> tuple[pd.DataFrame, dict]:
    """Parse a Supply/Make of Commodities JSON file."""
    rows = _load_json(filepath)
    if not rows:
        return pd.DataFrame(), {}
    matrix, name_map = _pivot_matrix(rows)
    logger.info(f"  Supply table: {matrix.shape[0]}×{matrix.shape[1]}")
    return matrix, name_map


def derive_A_from_use(use_table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Derive A matrix, value-added, and final demand from Use table.

    Returns: (A_matrix, value_added, final_demand, total_output)
    """
    if use_table.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.Series(dtype=float)

    # Separate industry columns from final demand columns
    # BEA codes: industries are alphanumeric, FD starts with F, VA rows start with V
    # Total output row starts with T
    all_rows = use_table.index.tolist()
    all_cols = use_table.columns.tolist()

    industry_cols = [c for c in all_cols if c and not c.startswith(("F", "T"))]
    fd_cols = [c for c in all_cols if c.startswith("F")]
    industry_rows = [r for r in all_rows if r and not r.startswith(("V", "T", "F"))]
    va_rows = [r for r in all_rows if r.startswith("V")]
    total_rows = [r for r in all_rows if r.startswith("T")]

    # Intermediate flows matrix (commodities × industries)
    Z = use_table.loc[industry_rows, industry_cols].fillna(0)

    # Value added
    va = use_table.loc[va_rows, industry_cols].fillna(0) if va_rows else pd.DataFrame()

    # Final demand
    fd = use_table.loc[industry_rows, fd_cols].fillna(0) if fd_cols else pd.DataFrame()

    # Total output = sum of intermediate + VA for each industry
    if total_rows:
        total_output = use_table.loc[total_rows[0], industry_cols].fillna(0)
    else:
        total_output = Z.sum(axis=0) + va.sum(axis=0) if not va.empty else Z.sum(axis=0)

    # A matrix = Z / total_output (column division)
    total_safe = total_output.replace(0, np.nan)
    A = Z.div(total_safe, axis=1).fillna(0)

    return A, va, fd, total_output


def parse_single_year(year: int) -> Optional[IOYearData]:
    """Parse all three table types for a single year."""
    logger.info(f"Parsing year {year}...")

    # Total Requirements (Leontief inverse)
    req_file = IO_DIR / f"Total_Requirements_IxI_Summary_{year}.json"
    if not req_file.exists():
        logger.warning(f"  No requirements file for {year}")
        return None
    L, name_map = parse_requirements_json(req_file)

    # Use table
    use_file = IO_DIR / f"Use_of_Commodities_Summary_{year}.json"
    use_table = pd.DataFrame()
    va = pd.DataFrame()
    fd = pd.DataFrame()
    total_output = pd.Series(dtype=float)
    A = pd.DataFrame()

    if use_file.exists():
        use_table, use_names = parse_use_json(use_file)
        name_map.update(use_names)
        A, va, fd, total_output = derive_A_from_use(use_table)

    # Supply table
    supply_file = IO_DIR / f"Supply_of_Commodities_Summary_{year}.json"
    supply_table = pd.DataFrame()
    if supply_file.exists():
        supply_table, supply_names = parse_supply_json(supply_file)
        name_map.update(supply_names)

    sectors = sorted(L.index.tolist()) if not L.empty else []

    return IOYearData(
        year=year,
        L_matrix=L,
        use_table=use_table,
        supply_table=supply_table,
        A_matrix=A,
        value_added=va,
        final_demand=fd,
        total_output=total_output,
        sectors=sectors,
        sector_names=name_map,
    )


def parse_all_years(start=1997, end=2024) -> dict[int, IOYearData]:
    """Parse all available years and return dict of year -> IOYearData."""
    results = {}
    for year in range(start, end + 1):
        data = parse_single_year(year)
        if data is not None and not data.L_matrix.empty:
            results[year] = data
    logger.info(f"Parsed {len(results)} years successfully")
    return results


def save_all_years(data: dict[int, IOYearData]) -> None:
    """Save parsed data to pickle files."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for year, yd in data.items():
        out_path = PROCESSED / f"year_{year}.pkl"
        with open(out_path, "wb") as f:
            pickle.dump({
                "year": yd.year,
                "L_matrix": yd.L_matrix,
                "A_matrix": yd.A_matrix,
                "use_table": yd.use_table,
                "supply_table": yd.supply_table,
                "value_added": yd.value_added,
                "final_demand": yd.final_demand,
                "total_output": yd.total_output,
                "sectors": yd.sectors,
                "sector_names": yd.sector_names,
            }, f)
    logger.info(f"Saved {len(data)} year files to {PROCESSED}")


def main():
    """Parse all BEA I-O JSON files and save as pickles."""
    print("=" * 70)
    print("BEA API PARSER — Converting JSON to I-O Matrices")
    print("=" * 70)

    data = parse_all_years()

    # Summary
    print(f"\nYears parsed: {sorted(data.keys())}")
    for year, yd in sorted(data.items()):
        n = yd.L_matrix.shape[0]
        has_use = "Use" if not yd.use_table.empty else "---"
        has_va = f"VA({yd.value_added.shape[0]})" if not yd.value_added.empty else "---"
        has_fd = f"FD({yd.final_demand.shape[1]})" if not yd.final_demand.empty else "---"
        print(f"  {year}: {n}×{n} L, {has_use}, {has_va}, {has_fd}")

    # Validate: check 2002 multipliers
    if 2002 in data:
        mult = data[2002].L_matrix.sum(axis=0)
        print(f"\n2002 output multipliers: mean={mult.mean():.4f}, "
              f"min={mult.min():.4f}, max={mult.max():.4f}")

    save_all_years(data)
    print("\nDone.")


if __name__ == "__main__":
    main()
