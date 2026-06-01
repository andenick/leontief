"""Table service — matrix slicing, aggregation, labeling, and JSON payloads.

Public API
----------
matrix_payload(year, matrix, agg=None, search=None) -> dict
    Build the full JSON-serializable payload for the Explorer table view.

matrix_as_records(year, matrix) -> list[dict]
    Convenience: return the matrix as a list of row dicts (code -> value).

heatmap_payload(year, matrix, agg=None, search=None) -> dict
    Thin alias for matrix_payload; chart_service builds the Plotly figure.

Aggregation (agg=="15")
-----------------------
When agg=="15" is requested the service sums values within each of the 15
broad NAICS-derived groups defined in sectors.json["agg15"].

- Applies to axes whose labels are the 71 BEA sector codes:
    Use, Supply, A, A_square, L  — both rows and columns aggregated.
    VA  — only columns (sector axis) aggregated; V-code rows left intact.
    FD  — only rows (sector axis) aggregated; F-code columns left intact.

- Groups are ordered by their first appearance in the sectors.json["sectors"]
  list (stable, reproducible order matching BEA sector ordering).

- Row and column labels in the output are the group names (e.g. "Agriculture").

- If a label is NOT a recognized sector code (e.g. a V-code like "V001" or an
  F-code like "F010"), that axis is left un-aggregated and returned as-is.

JSON safety
-----------
All float values are sanitized: NaN and ±Inf become None so json.dumps works.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.services.data_service import (
    get_table_meta,
    load_sectors,
    read_matrix,
    sector_names_map,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Matrices whose sector-labeled axes should be aggregated under agg=="15"
_SECTOR_LABELED_MATRICES = {"Use", "Supply", "A", "A_square", "L", "VA", "FD"}

# For these matrices BOTH axes are sector codes -> aggregate both
_BOTH_AXES_SECTOR = {"Use", "Supply", "A", "A_square", "L"}

# For VA: cols are sector codes, rows are V-codes
# For FD: rows are sector codes, cols are F-codes


def _agg15_group_order() -> list[str]:
    """Return agg15 group names in stable first-appearance order."""
    sectors_data = load_sectors()
    seen: list[str] = []
    seen_set: set[str] = set()
    for sec in sectors_data["sectors"]:
        g = sec["agg15"]
        if g not in seen_set:
            seen.append(g)
            seen_set.add(g)
    return seen


def _code_to_group() -> dict[str, str]:
    """Return mapping sector_code -> agg15_group_name."""
    sectors_data = load_sectors()
    return {sec["code"]: sec["agg15"] for sec in sectors_data["sectors"]}


def _aggregate_axis(df: pd.DataFrame, axis: int, code_to_group: dict[str, str],
                    group_order: list[str]) -> pd.DataFrame:
    """Aggregate a DataFrame along one axis using the agg15 crosswalk.

    Only aggregates labels that appear in code_to_group; unrecognized labels
    are passed through unchanged (so V-codes / F-codes survive).

    Args:
        df:            Input DataFrame.
        axis:          0 = aggregate rows, 1 = aggregate columns.
        code_to_group: Sector code -> group name mapping.
        group_order:   Ordered list of group names.

    Returns:
        Aggregated DataFrame (summed within groups).
    """
    if axis == 0:
        # Check whether the row index looks like sector codes
        labels = list(df.index)
        if not any(lbl in code_to_group for lbl in labels):
            return df  # nothing to aggregate (e.g. V-code rows in VA)

        # Map each label to its group (non-sector labels -> keep as-is)
        new_index = [code_to_group.get(lbl, lbl) for lbl in labels]
        df2 = df.copy()
        df2.index = pd.Index(new_index, name="group")
        result = df2.groupby(df2.index, sort=False).sum()
        # Re-order rows to canonical group order (only groups present)
        present = [g for g in group_order if g in result.index]
        return result.loc[present]

    else:  # axis == 1
        labels = list(df.columns)
        if not any(lbl in code_to_group for lbl in labels):
            return df  # nothing to aggregate

        new_cols = [code_to_group.get(lbl, lbl) for lbl in labels]
        df2 = df.copy()
        df2.columns = pd.Index(new_cols, name="group")
        # groupby columns
        result = df2.T.groupby(df2.columns, sort=False).sum().T
        # Re-order columns
        present = [g for g in group_order if g in result.columns]
        return result[present]


def _sanitize_value(v: Any) -> Any:
    """Replace NaN/Inf with None for JSON safety."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _df_to_values(df: pd.DataFrame) -> list[list[Any]]:
    """Convert DataFrame to row-major nested list with NaN->None."""
    rows = []
    for _, row in df.iterrows():
        rows.append([_sanitize_value(v) for v in row])
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def matrix_payload(
    year: int,
    matrix: str,
    agg: str | None = None,
    search: str | None = None,
) -> dict:
    """Build the full JSON-serializable payload for a matrix.

    Args:
        year:   Table year, e.g. 2002.
        matrix: Matrix key, e.g. "L", "Use", "VA".
        agg:    Pass "15" to aggregate the sector-labeled axis/axes into the
                15 broad NAICS groups (summed). Any other value is ignored.
        search: Case-insensitive substring to match against sector codes
                AND sector names. Returns indices of matching rows/columns
                in ``search_hits``.

    Returns:
        JSON-serializable dict::

            {
              "year": int,
              "matrix": str,
              "label": str,
              "square": bool,
              "index": [row_codes_or_group_names],
              "index_names": [human_readable_row_names],
              "columns": [col_codes_or_group_names],
              "column_names": [human_readable_col_names],
              "values": [[float_or_null, ...], ...],
              "rows": int,
              "cols": int,
              "search_hits": {"rows": [int, ...], "cols": [int, ...]}
            }

    Aggregation behavior (agg=="15"):
        - Use, Supply, A, A_square, L: both axes aggregated by summing within
          each of the 15 agg15 groups from sectors.json. Row/col labels become
          group names (e.g. "Agriculture").
        - VA: columns (sector axis) aggregated; V-code rows left intact.
        - FD: rows (sector axis) aggregated; F-code columns left intact.
        - Groups are ordered by first appearance in sectors.json["sectors"].

    Search behavior:
        search_hits["rows"] contains 0-based row indices whose code or name
        contains the search string (case-insensitive).
        search_hits["cols"] similarly for columns.
        If agg=="15", search is matched against group names.
    """
    meta = get_table_meta(year, matrix)
    df = read_matrix(year, matrix)

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    if agg == "15":
        code_to_group = _code_to_group()
        group_order = _agg15_group_order()

        if matrix in _BOTH_AXES_SECTOR:
            df = _aggregate_axis(df, axis=0, code_to_group=code_to_group,
                                 group_order=group_order)
            df = _aggregate_axis(df, axis=1, code_to_group=code_to_group,
                                 group_order=group_order)
        elif matrix == "VA":
            # rows = V-codes (leave intact), cols = sector codes (aggregate)
            df = _aggregate_axis(df, axis=1, code_to_group=code_to_group,
                                 group_order=group_order)
        elif matrix == "FD":
            # rows = sector codes (aggregate), cols = F-codes (leave intact)
            df = _aggregate_axis(df, axis=0, code_to_group=code_to_group,
                                 group_order=group_order)

    # ------------------------------------------------------------------
    # Build index/column label arrays with human-readable names
    # ------------------------------------------------------------------
    names_map = sector_names_map()
    sectors_data = load_sectors()
    va_rows: dict = sectors_data.get("va_rows", {})
    fd_cols: dict = sectors_data.get("fd_cols", {})

    def _resolve_name(code: str) -> str:
        """Look up a human-readable name for any code (sector, V-, F-, group)."""
        if code in names_map:
            return names_map[code]
        if code in va_rows:
            return va_rows[code]
        if code in fd_cols:
            return fd_cols[code]
        # agg15 group name or unknown — return as-is
        return code

    index_codes = list(df.index)
    col_codes = list(df.columns)
    index_names = [_resolve_name(c) for c in index_codes]
    column_names = [_resolve_name(c) for c in col_codes]

    # ------------------------------------------------------------------
    # Search hits
    # ------------------------------------------------------------------
    search_hits: dict[str, list[int]] = {"rows": [], "cols": []}
    if search:
        q = search.lower()
        for i, (code, name) in enumerate(zip(index_codes, index_names)):
            if q in code.lower() or q in name.lower():
                search_hits["rows"].append(i)
        for j, (code, name) in enumerate(zip(col_codes, column_names)):
            if q in code.lower() or q in name.lower():
                search_hits["cols"].append(j)

    # ------------------------------------------------------------------
    # Values (NaN/Inf -> None)
    # ------------------------------------------------------------------
    values = _df_to_values(df)

    return {
        "year": year,
        "matrix": matrix,
        "label": meta["label"],
        "square": meta["square"],
        "index": index_codes,
        "index_names": index_names,
        "columns": col_codes,
        "column_names": column_names,
        "values": values,
        "rows": len(index_codes),
        "cols": len(col_codes),
        "search_hits": search_hits,
    }


def matrix_as_records(year: int, matrix: str) -> list[dict]:
    """Return the matrix as a list of row dicts (code -> float|None).

    Each record is {row_code: {col_code: value, ...}}.
    Convenience helper for downstream consumers (chart_service, etc.).

    Args:
        year:   Table year.
        matrix: Matrix key.

    Returns:
        List of dicts, one per row. Keys are column codes; values are
        float or None (NaN sanitized).
    """
    df = read_matrix(year, matrix)
    records = []
    for row_code, row in df.iterrows():
        rec = {"__row__": row_code}
        for col_code, val in row.items():
            rec[col_code] = _sanitize_value(val)
        records.append(rec)
    return records


def heatmap_payload(
    year: int,
    matrix: str,
    agg: str | None = None,
    search: str | None = None,
) -> dict:
    """Return the matrix payload for heatmap rendering.

    This is a thin alias for matrix_payload; chart_service constructs
    the Plotly figure dict from the returned payload.

    Args:
        year:   Table year.
        matrix: Matrix key.
        agg:    Aggregation level ("15" or None).
        search: Search string for highlighting.

    Returns:
        Same dict as matrix_payload.
    """
    return matrix_payload(year, matrix, agg=agg, search=search)
