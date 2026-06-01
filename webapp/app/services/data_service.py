"""Data service — manifest + parquet reads with LRU caching.

All parquet matrix files store the original index as a column named ``__index__``
(integer RangeIndex in the file; the label values live in ``df['__index__']``).
Columns are the sector codes, plus ``__index__`` as the first column.

``read_matrix`` reconstructs a properly-labeled DataFrame:
    - index  = row labels (from ``__index__`` column)
    - columns = remaining column names (sector codes, or F/V codes for non-square)

``read_series`` returns the DataFrame as-is (integer index, ``year`` + sector cols).

Raises:
    KeyError          — unknown table/series key
    FileNotFoundError — parquet file missing from site_data/cache/
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Path resolution — mirrors config.py without importing it at module level
# (avoids circular imports and makes the module importable standalone)
# ---------------------------------------------------------------------------

_WEBAPP_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_SITE_DATA: Path = _WEBAPP_ROOT / "site_data"


def _manifest_path() -> Path:
    return _SITE_DATA / "site_manifest.json"


def _sectors_path() -> Path:
    return _SITE_DATA / "sectors.json"


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_manifest() -> dict:
    """Load and cache site_manifest.json.

    Returns:
        The full manifest dict.

    Raises:
        FileNotFoundError: if site_manifest.json does not exist yet.
    """
    p = _manifest_path()
    if not p.exists():
        raise FileNotFoundError(
            f"site_manifest.json not found at {p}. "
            "Run data_pipeline/build_cache.py first."
        )
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_sectors() -> dict:
    """Load and cache sectors.json.

    Returns:
        The full sectors dict.

    Raises:
        FileNotFoundError: if sectors.json does not exist yet.
    """
    p = _sectors_path()
    if not p.exists():
        raise FileNotFoundError(
            f"sectors.json not found at {p}. "
            "Run data_pipeline/build_sectors.py first."
        )
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Listing helpers
# ---------------------------------------------------------------------------

def list_tables() -> list[dict]:
    """Return manifest['tables'] (empty list if manifest not built yet)."""
    try:
        return load_manifest().get("tables", [])
    except FileNotFoundError:
        return []


def list_series() -> list[dict]:
    """Return manifest['series'] (empty list if manifest not built yet)."""
    try:
        return load_manifest().get("series", [])
    except FileNotFoundError:
        return []


def list_studies() -> list[dict]:
    """Return manifest['studies'] (empty list if manifest not built yet)."""
    try:
        return load_manifest().get("studies", [])
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def get_table_meta(year: int, matrix: str) -> dict:
    """Return the manifest entry for a given (year, matrix) pair.

    Args:
        year:   e.g. 2002
        matrix: e.g. "L", "Use", "A_square"

    Returns:
        The table dict from manifest["tables"].

    Raises:
        KeyError: if no matching entry is found.
    """
    key = f"{year}__{matrix}"
    for t in list_tables():
        if t["key"] == key:
            return t
    raise KeyError(
        f"No table entry for year={year!r}, matrix={matrix!r} "
        f"(key={key!r}). Available: {[t['key'] for t in list_tables()]}"
    )


def get_series_meta(key: str) -> dict:
    """Return the manifest entry for a series key.

    Args:
        key: e.g. "multiplier_timeseries"

    Returns:
        The series dict from manifest["series"].

    Raises:
        KeyError: if the key is not found.
    """
    for s in list_series():
        if s["key"] == key:
            return s
    raise KeyError(
        f"No series entry for key={key!r}. "
        f"Available: {[s['key'] for s in list_series()]}"
    )


# ---------------------------------------------------------------------------
# Matrix reader
# ---------------------------------------------------------------------------

def read_matrix(year: int, matrix: str) -> pd.DataFrame:
    """Load a matrix parquet and return a labeled DataFrame.

    The parquet files store the original row-label values in a column named
    ``__index__`` (the file's RangeIndex is discarded). This function:
      1. Reads the parquet.
      2. Sets ``__index__`` as the DataFrame index (row labels = sector codes
         for square matrices; V-codes for VA; F-codes for FD row-axis etc.).
      3. Drops the ``__index__`` column so only data columns remain.
      4. Names the index ``"code"``.

    Args:
        year:   e.g. 2002
        matrix: e.g. "L", "Use", "Supply", "A", "A_square", "VA", "FD"

    Returns:
        DataFrame with labeled index (row codes) and labeled columns (col codes).

    Raises:
        KeyError:          if (year, matrix) is unknown in the manifest.
        FileNotFoundError: if the parquet file is missing from cache/.
    """
    meta = get_table_meta(year, matrix)
    parquet_rel = meta["parquet"]          # e.g. "cache/2002__L.parquet"
    parquet_path = _SITE_DATA / parquet_rel

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Parquet file not found: {parquet_path}. "
            "Run data_pipeline/build_cache.py to generate the cache."
        )

    raw = pd.read_parquet(parquet_path)

    if "__index__" not in raw.columns:
        raise ValueError(
            f"Expected an '__index__' column in {parquet_path}, "
            f"but got columns: {list(raw.columns)}"
        )

    # Reconstruct: set __index__ as the index, keep data columns
    df = raw.set_index("__index__")
    df.index.name = "code"
    return df


# ---------------------------------------------------------------------------
# Series reader
# ---------------------------------------------------------------------------

def read_series(key: str) -> pd.DataFrame:
    """Load a series parquet and return the raw DataFrame.

    Args:
        key: series key, e.g. "multiplier_timeseries"

    Returns:
        DataFrame (typically year x sector, with a 'year' column).

    Raises:
        KeyError:          if the key is unknown in the manifest.
        FileNotFoundError: if the parquet file is missing.
    """
    meta = get_series_meta(key)
    parquet_rel = meta["parquet"]          # e.g. "cache/multiplier_timeseries.parquet"
    parquet_path = _SITE_DATA / parquet_rel

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Series parquet not found: {parquet_path}. "
            "Run data_pipeline/build_cache.py to generate the cache."
        )

    return pd.read_parquet(parquet_path)


# ---------------------------------------------------------------------------
# Sector name helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def sector_names_map() -> dict[str, str]:
    """Return a dict mapping sector code -> sector name.

    Derived from sectors.json['sectors']. Cached after first call.
    """
    sectors = load_sectors().get("sectors", [])
    return {s["code"]: s["name"] for s in sectors}


def sector_name(code: str) -> str:
    """Return the human-readable name for a sector code.

    Args:
        code: BEA sector code, e.g. "111CA"

    Returns:
        The sector name string.

    Raises:
        KeyError: if the code is not in sectors.json.
    """
    mapping = sector_names_map()
    if code not in mapping:
        raise KeyError(
            f"Sector code {code!r} not found in sectors.json. "
            f"Known codes: {list(mapping.keys())}"
        )
    return mapping[code]
