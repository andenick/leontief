"""Parse BEA GDP-by-Industry API data for compensation, VA, and gross output.

Provides TRUE compensation and value-added data by industry and year,
enabling accurate labor share calculations (53-57% range).

The Use-table V001 row understates compensation because it uses
a different measurement concept. GDP-by-Industry Table 6 provides
the standard national accounts measure.

Usage:
    from gdp_industry_parser import load_gdp_components, true_labor_share_timeseries
"""

import json
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent.parent
GDP_DIR = PROJECT / "Inputs" / "bea_api" / "gdp_by_industry"


def _load_gdp_json(filepath: Path) -> list[dict]:
    """Load a GDP-by-Industry API JSON and extract data rows."""
    with open(filepath) as f:
        raw = json.load(f)
    try:
        return raw["BEAAPI"]["Results"][0]["Data"]
    except (KeyError, IndexError, TypeError):
        logger.warning(f"No data in {filepath.name}")
        return []


def parse_table6_components(filepath: Path = None) -> dict[str, pd.DataFrame]:
    """Parse GDP-by-Industry Table 6 (Components of Value Added).

    Returns dict with keys like "Compensation of employees",
    "Taxes on production and imports, less subsidies",
    "Gross operating surplus", each mapping to a DataFrame
    of year × industry with values in billions of dollars.
    """
    if filepath is None:
        filepath = GDP_DIR / "gdpind_6_Components_of_Value_Added.json"

    rows = _load_gdp_json(filepath)
    if not rows:
        return {}

    df = pd.DataFrame(rows)
    # BEA has typo: "IndustrYDescription" (capital Y)
    desc_col = "IndustrYDescription" if "IndustrYDescription" in df.columns else "IndustryDescription"

    components = {}
    for component_name in df[desc_col].unique():
        subset = df[df[desc_col] == component_name].copy()
        subset["DataValue"] = pd.to_numeric(
            subset["DataValue"].str.replace(",", ""), errors="coerce"
        )
        pivot = subset.pivot_table(
            index="Year", columns="Industry",
            values="DataValue", aggfunc="first"
        )
        pivot.index = pivot.index.astype(int)
        components[component_name] = pivot.sort_index()

    logger.info(f"Parsed Table 6: {len(components)} components, "
                f"{len(rows)} total rows")
    return components


def parse_table1_value_added(filepath: Path = None) -> pd.DataFrame:
    """Parse GDP-by-Industry Table 1 (Value Added by Industry).

    Returns DataFrame: year × industry, values in billions of dollars.
    """
    if filepath is None:
        filepath = GDP_DIR / "gdpind_1_Value_Added_by_Industry.json"

    rows = _load_gdp_json(filepath)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["DataValue"] = pd.to_numeric(
        df["DataValue"].str.replace(",", ""), errors="coerce"
    )
    pivot = df.pivot_table(
        index="Year", columns="Industry",
        values="DataValue", aggfunc="first"
    )
    pivot.index = pivot.index.astype(int)
    return pivot.sort_index()


def parse_table15_gross_output(filepath: Path = None) -> pd.DataFrame:
    """Parse GDP-by-Industry Table 15 (Gross Output by Industry)."""
    if filepath is None:
        filepath = GDP_DIR / "gdpind_15_Gross_Output_by_Industry.json"

    rows = _load_gdp_json(filepath)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["DataValue"] = pd.to_numeric(
        df["DataValue"].str.replace(",", ""), errors="coerce"
    )
    pivot = df.pivot_table(
        index="Year", columns="Industry",
        values="DataValue", aggfunc="first"
    )
    pivot.index = pivot.index.astype(int)
    return pivot.sort_index()


def true_labor_share_timeseries() -> pd.DataFrame:
    """Compute true labor share from GDP-by-Industry data.

    Labor share = Compensation of employees / Value Added

    Returns DataFrame with year, labor_share, compensation, value_added.
    """
    components = parse_table6_components()
    va = parse_table1_value_added()

    if not components or va.empty:
        logger.warning("Cannot compute labor share: missing data")
        return pd.DataFrame()

    # Find compensation component
    comp_key = None
    for key in components:
        if "compensation" in key.lower() or "Compensation" in key:
            comp_key = key
            break

    if comp_key is None:
        logger.warning(f"Compensation component not found. Available: {list(components.keys())}")
        return pd.DataFrame()

    comp = components[comp_key]
    logger.info(f"Using component: '{comp_key}'")

    # Compute aggregate labor share per year
    rows = []
    for year in sorted(set(comp.index) & set(va.index)):
        total_comp = comp.loc[year].sum()
        total_va = va.loc[year].sum()
        share = total_comp / total_va if total_va > 0 else 0
        rows.append({
            "year": year,
            "labor_share": share,
            "total_compensation": total_comp,
            "total_value_added": total_va,
        })

    result = pd.DataFrame(rows).set_index("year")
    if len(result) > 0:
        logger.info(
            f"Labor share range: {result['labor_share'].min():.4f} - "
            f"{result['labor_share'].max():.4f}"
        )
    return result


def labor_share_by_industry(year: int = 2020) -> pd.DataFrame:
    """Compute labor share by industry for a specific year."""
    components = parse_table6_components()
    va = parse_table1_value_added()

    comp_key = None
    for key in components:
        if "compensation" in key.lower() or "Compensation" in key:
            comp_key = key
            break
    if comp_key is None:
        return pd.DataFrame()

    comp = components[comp_key]
    if year not in comp.index or year not in va.index:
        return pd.DataFrame()

    c = comp.loc[year]
    v = va.loc[year]
    common = c.index.intersection(v.index)
    v_safe = v.reindex(common).replace(0, pd.NA)

    result = pd.DataFrame({
        "compensation": c.reindex(common),
        "value_added": v.reindex(common),
        "labor_share": (c.reindex(common) / v_safe).fillna(0),
    })
    return result.sort_values("labor_share", ascending=False)


if __name__ == "__main__":
    print("=== GDP-by-Industry Parser ===\n")

    print("--- Table 6: Components of Value Added ---")
    comp = parse_table6_components()
    for name, df in comp.items():
        print(f"  {name}: {df.shape[0]} years × {df.shape[1]} industries")

    print("\n--- Table 1: Value Added ---")
    va = parse_table1_value_added()
    print(f"  {va.shape[0]} years × {va.shape[1]} industries")

    print("\n--- Table 15: Gross Output ---")
    go = parse_table15_gross_output()
    print(f"  {go.shape[0]} years × {go.shape[1]} industries")

    print("\n--- True Labor Share ---")
    ls = true_labor_share_timeseries()
    if not ls.empty:
        print(ls.to_string())
