"""Import dependency analysis from I-O Use tables.

Tracks how dependent each sector is on imported intermediate inputs,
and how this changes over time (globalization indicator).

Reference: Miller & Blair (2009), Ch. 3 — from Wynne KB.
"""

import numpy as np
import pandas as pd
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def import_content_by_sector(
    final_demand: pd.DataFrame,
    total_output: pd.Series,
) -> pd.Series:
    """Calculate import dependency ratio for each commodity.

    Uses final demand columns: F02E (exports) and F02N (net exports).
    Imports = Exports - Net Exports (when net exports < exports).

    Alternatively: BEA Use tables embed imports as negative values
    within commodity rows (competitive imports). This function uses
    the FD-based approach.

    Returns: estimated imports / total output per commodity.
    """
    if final_demand.empty:
        return pd.Series(dtype=float)

    # Find export and net-export columns
    export_col = [c for c in final_demand.columns if "F02E" in str(c)]
    net_export_col = [c for c in final_demand.columns if "F02N" in str(c)]

    if not export_col and not net_export_col:
        # Try broader match
        export_col = [c for c in final_demand.columns if "F030" in str(c)]  # exports
        net_export_col = [c for c in final_demand.columns if "F040" in str(c)]

    if export_col:
        exports = final_demand[export_col].sum(axis=1)
    else:
        exports = pd.Series(0, index=final_demand.index)

    # Net exports: positive = exports > imports; negative = imports > exports
    if net_export_col:
        net_exports = final_demand[net_export_col].sum(axis=1)
        # Imports = Exports - Net Exports
        imports = (exports - net_exports).clip(lower=0)
    else:
        imports = exports * 0  # Can't estimate without net exports

    x = total_output.reindex(imports.index).fillna(0).replace(0, np.nan)
    ratio = (imports / x).fillna(0)
    ratio.name = "import_content_ratio"
    return ratio


def aggregate_import_dependency(
    use_table: pd.DataFrame = None,
    final_demand: pd.DataFrame = None,
    total_output: pd.Series = None,
) -> float:
    """Economy-wide import dependency ratio.

    Accepts either use_table (legacy) or final_demand + total_output (preferred).
    """
    if final_demand is not None and total_output is not None:
        ratios = import_content_by_sector(final_demand, total_output)
        if ratios.empty:
            return 0.0
        # Weight by output
        x = total_output.reindex(ratios.index).fillna(0)
        total = x.sum()
        if total == 0:
            return 0.0
        return float((ratios * x).sum() / total)

    # Legacy fallback with use_table
    if use_table is not None:
        # Look for negative values in commodity rows as import indicator
        industry_rows = [r for r in use_table.index if r and not str(r).startswith(("V", "T", "F"))]
        industry_cols = [c for c in use_table.columns if c and not str(c).startswith(("F", "T"))]
        Z = use_table.loc[industry_rows, industry_cols].fillna(0)
        negative_sum = Z[Z < 0].sum().sum()
        total_sum = Z.abs().sum().sum()
        if total_sum == 0:
            return 0.0
        return float(abs(negative_sum) / total_sum)

    return 0.0


def import_dependency_timeseries(data_by_year: dict) -> pd.DataFrame:
    """Track aggregate import dependency across years."""
    rows = []
    for year in sorted(data_by_year.keys()):
        use = data_by_year[year].get("use_table")
        if use is None or use.empty:
            continue
        dep = aggregate_import_dependency(use)
        rows.append({"year": year, "import_dependency": dep})
    return pd.DataFrame(rows).set_index("year")


def split_use_table(
    use_table: pd.DataFrame,
    import_row_prefix: str = "F050",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Approximate split of Use table into domestic and import flows.

    BEA Use tables embed imports as negative values or in specific rows.
    This function distributes import totals across commodity rows
    proportional to total use (standard RAS-based approximation).

    Args:
        use_table: Full Use table.
        import_row_prefix: Row code prefix for import rows.

    Returns:
        Tuple of (domestic Use table, import Use table).
    """
    import_rows = [r for r in use_table.index if str(r).startswith(import_row_prefix)]
    industry_rows = [r for r in use_table.index
                     if r and not str(r).startswith(("V", "T", "F", "S"))]
    industry_cols = [c for c in use_table.columns
                     if c and not str(c).startswith(("F", "T"))]

    Z = use_table.loc[industry_rows, industry_cols].fillna(0)

    if import_rows:
        import_totals = use_table.loc[import_rows, industry_cols].sum(axis=0).abs()
    else:
        # Fall back to negative values in Z
        neg_vals = Z[Z < 0]
        import_totals = neg_vals.sum(axis=0).abs()
        Z = Z.clip(lower=0)

    # Distribute imports proportional to total use
    col_sums = Z.sum(axis=0).replace(0, np.nan)
    import_shares = Z.div(col_sums, axis=1).fillna(0)

    Z_import = import_shares.multiply(import_totals, axis=1)
    Z_domestic = Z - Z_import
    Z_domestic = Z_domestic.clip(lower=0)

    return Z_domestic, Z_import


def import_content_of_exports(
    A_domestic: pd.DataFrame,
    f_exports: pd.Series,
    value_added_coeff: pd.Series,
) -> pd.DataFrame:
    """Compute import content of exports (Hummels-Ishii-Yi method).

    ICE_j = 1 - v' * L_d * e_j / e_j

    Where L_d = (I - A_d)^(-1) is the domestic Leontief inverse,
    and v is the value added coefficient vector.

    Args:
        A_domestic: Domestic direct requirements matrix.
        f_exports: Export values by sector.
        value_added_coeff: Value added per unit output (v = VA/x).

    Returns:
        DataFrame with dva_share, import_content, export_value per sector.
    """
    from scipy import linalg as sp_linalg

    n = A_domestic.shape[0]
    sectors = A_domestic.index
    v = value_added_coeff.reindex(sectors).fillna(0).values
    e = f_exports.reindex(sectors).fillna(0).values

    L_d = sp_linalg.inv(np.eye(n) - A_domestic.values)

    # DVA share per unit of exports: v' * L_d (row vector)
    dva_coeff = v @ L_d

    # DVA in actual exports
    dva = dva_coeff * e
    import_content = e - dva

    e_safe = np.where(e > 0, e, np.nan)

    return pd.DataFrame({
        "export_value": e,
        "dva_in_exports": dva,
        "import_content": import_content,
        "dva_share": dva / e_safe,
        "import_content_share": import_content / e_safe,
    }, index=sectors).fillna(0)


def domestic_value_added_in_exports(
    L_domestic: pd.DataFrame,
    value_added_coeff: pd.Series,
    f_exports: pd.Series,
) -> pd.Series:
    """Compute domestic value added embodied in exports.

    DVA_j = v' * L_d * e_j

    Args:
        L_domestic: Domestic Leontief inverse.
        value_added_coeff: VA per unit output.
        f_exports: Exports by sector.

    Returns:
        Series of DVA in exports by sector.
    """
    sectors = L_domestic.index
    v = value_added_coeff.reindex(sectors).fillna(0).values
    e = f_exports.reindex(sectors).fillna(0).values

    dva_coeff = v @ L_domestic.values
    dva = dva_coeff * e

    result = pd.Series(dva, index=sectors, name="dva_in_exports")
    return result
