"""Download/export service — pure functions returning (bytes, media_type, filename).

The API router calls these and streams the bytes back to the client.
No temp files are written to disk; all serialisation happens in-memory via
io.BytesIO.

Public API
----------
export_matrix(year, matrix, fmt)  -> (bytes, media_type, filename)
export_series(key, fmt)            -> (bytes, media_type, filename)
bundle_year_zip(year)              -> (bytes, "application/zip", filename)
bundle_all_zip()                   -> (bytes, "application/zip", filename)
study_bundle_zip(slug)             -> (bytes, "application/zip", filename)

Supported formats: csv, xlsx, json, parquet.

Labeled-parquet convention
--------------------------
Matrix parquets are stored with a synthetic ``__index__`` column that holds
the row-label strings (BEA sector codes).  The remaining columns are the
column-label strings.  To reconstruct the labeled DataFrame:

    df = pd.read_parquet(path)
    if "__index__" in df.columns:
        df = df.set_index("__index__")
        df.index.name = None

Series parquets are stored with a conventional integer RangeIndex; the
``year`` (or similar) columns are just ordinary data columns.
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

# ---------------------------------------------------------------------------
# Config — resolve paths without depending on a running FastAPI app
# ---------------------------------------------------------------------------
try:
    from app.config import SITE_DATA, CACHE_DIR, CONTENT_DIR, get_manifest_path
except ImportError:
    # Fallback: compute paths relative to this file (webapp/app/services/…)
    _WEBAPP_ROOT = Path(__file__).resolve().parent.parent.parent
    SITE_DATA = _WEBAPP_ROOT / "site_data"
    CACHE_DIR = SITE_DATA / "cache"
    CONTENT_DIR = _WEBAPP_ROOT / "content"

    def get_manifest_path() -> Path:  # type: ignore[misc]
        return SITE_DATA / "site_manifest.json"


# ---------------------------------------------------------------------------
# Allowed export formats
# ---------------------------------------------------------------------------
_ALLOWED_FMTS = frozenset({"csv", "xlsx", "json", "parquet"})

_MEDIA = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
    "parquet": "application/octet-stream",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_fmt(fmt: str) -> None:
    """Raise ValueError for an unsupported format string."""
    if fmt not in _ALLOWED_FMTS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Allowed: {sorted(_ALLOWED_FMTS)}"
        )


def _load_manifest() -> dict:
    """Load site_manifest.json; return empty dict if not yet built."""
    p = get_manifest_path()
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def _read_matrix_parquet(year: int, matrix: str) -> pd.DataFrame:
    """Load a labeled matrix DataFrame.

    Tries data_service.read_matrix first (if the sibling module is present
    and functional), then falls back to reading the parquet directly.

    The ``__index__`` column is promoted to the DataFrame index so callers
    get row labels as df.index and column labels as df.columns.
    """
    # --- try sibling data_service ---
    try:
        from app.services.data_service import read_matrix  # type: ignore[import]
        df = read_matrix(year, matrix)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    # --- direct fallback via manifest / convention ---
    path = CACHE_DIR / f"{year}__{matrix}.parquet"
    if not path.exists():
        # Try manifest lookup
        manifest = _load_manifest()
        key = f"{year}__{matrix}"
        table_meta = next(
            (t for t in manifest.get("tables", []) if t["key"] == key), None
        )
        if table_meta:
            path = SITE_DATA / table_meta["parquet"]
        if not path.exists():
            raise FileNotFoundError(f"Matrix parquet not found: {year}/{matrix}")

    df = pd.read_parquet(path)
    if "__index__" in df.columns:
        df = df.set_index("__index__")
        df.index.name = None
    return df


def _read_series_parquet(key: str) -> pd.DataFrame:
    """Load a tidy series DataFrame.

    Tries data_service.read_series first, then falls back to direct parquet.
    """
    try:
        from app.services.data_service import read_series  # type: ignore[import]
        df = read_series(key)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    path = CACHE_DIR / f"{key}.parquet"
    if not path.exists():
        manifest = _load_manifest()
        series_meta = next(
            (s for s in manifest.get("series", []) if s["key"] == key), None
        )
        if series_meta:
            path = SITE_DATA / series_meta["parquet"]
        if not path.exists():
            raise FileNotFoundError(f"Series parquet not found: {key!r}")

    return pd.read_parquet(path)


def _df_to_bytes(df: pd.DataFrame, fmt: str, sheet_name: str = "data") -> bytes:
    """Serialise *df* to *fmt* and return raw bytes.

    For CSV/XLSX the index is included as the first column (sector codes).
    For JSON we use orient='split' (machine-readable, lossless column order).
    For parquet we round-trip through pyarrow in-memory.
    """
    buf = io.BytesIO()

    if fmt == "csv":
        # include_index=True means row labels land in column 0
        csv_text = df.to_csv(index=True)
        buf.write(csv_text.encode("utf-8"))
        return buf.getvalue()

    if fmt == "xlsx":
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=True)
        return buf.getvalue()

    if fmt == "json":
        # orient='split': {"index":[…],"columns":[…],"data":[[…],…]}
        # We also output as "values" key alias for spec compliance.
        split = json.loads(df.to_json(orient="split"))
        # Rename "data" -> "values" to match the spec wording
        payload = {
            "index": split["index"],
            "columns": split["columns"],
            "values": split["data"],
        }
        buf.write(json.dumps(payload).encode("utf-8"))
        return buf.getvalue()

    if fmt == "parquet":
        df.to_parquet(buf, index=True)
        return buf.getvalue()

    raise ValueError(f"Unknown format: {fmt!r}")  # unreachable after _check_fmt


def _series_to_bytes(df: pd.DataFrame, fmt: str, sheet_name: str = "data") -> bytes:
    """Serialise a series DataFrame (conventional integer index, no promotion)."""
    buf = io.BytesIO()

    if fmt == "csv":
        buf.write(df.to_csv(index=False).encode("utf-8"))
        return buf.getvalue()

    if fmt == "xlsx":
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return buf.getvalue()

    if fmt == "json":
        split = json.loads(df.to_json(orient="split"))
        payload = {
            "index": split["index"],
            "columns": split["columns"],
            "values": split["data"],
        }
        buf.write(json.dumps(payload).encode("utf-8"))
        return buf.getvalue()

    if fmt == "parquet":
        df.to_parquet(buf, index=False)
        return buf.getvalue()

    raise ValueError(f"Unknown format: {fmt!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_matrix(
    year: int,
    matrix: str,
    fmt: str,
) -> tuple[bytes, str, str]:
    """Return (bytes, media_type, filename) for a single matrix export.

    Parameters
    ----------
    year:   BEA year (1997–2024)
    matrix: one of Use, Supply, A, A_square, L, VA, FD
    fmt:    csv | xlsx | json | parquet
    """
    _check_fmt(fmt)
    df = _read_matrix_parquet(year, matrix)
    sheet = f"{matrix}_{year}"
    raw = _df_to_bytes(df, fmt, sheet_name=sheet)
    filename = f"wassily_{matrix}_{year}.{fmt}"
    return raw, _MEDIA[fmt], filename


def export_series(
    key: str,
    fmt: str,
) -> tuple[bytes, str, str]:
    """Return (bytes, media_type, filename) for a single series export.

    Parameters
    ----------
    key: series key from site_manifest.json (e.g. "multiplier_timeseries")
    fmt: csv | xlsx | json | parquet
    """
    _check_fmt(fmt)
    df = _read_series_parquet(key)
    raw = _series_to_bytes(df, fmt, sheet_name=key[:31])  # xlsx sheet name ≤31 chars
    filename = f"wassily_{key}.{fmt}"
    return raw, _MEDIA[fmt], filename


def bundle_year_zip(year: int) -> tuple[bytes, str, str]:
    """Build an in-memory zip of all 7 matrices for *year* as CSV files.

    Includes a README.txt with provenance info drawn from the manifest.

    Returns (bytes, "application/zip", filename).
    """
    manifest = _load_manifest()
    tables_for_year = [
        t for t in manifest.get("tables", []) if t["year"] == year
    ]
    if not tables_for_year:
        # Fallback: derive from MATRIX_KEYS constant
        try:
            from app.config import MATRIX_KEYS  # type: ignore[import]
        except ImportError:
            MATRIX_KEYS = ("Use", "Supply", "A", "A_square", "L", "VA", "FD")
        tables_for_year = [{"year": year, "matrix": m, "provenance": ""} for m in MATRIX_KEYS]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        csv_count = 0
        provenance_lines: list[str] = []

        for t in tables_for_year:
            matrix = t["matrix"]
            try:
                df = _read_matrix_parquet(year, matrix)
            except FileNotFoundError:
                continue
            csv_bytes = df.to_csv(index=True).encode("utf-8")
            arc_name = f"wassily_{matrix}_{year}.csv"
            zf.writestr(arc_name, csv_bytes)
            csv_count += 1
            prov = t.get("provenance", "")
            provenance_lines.append(f"  {arc_name}: {prov}")

        # README.txt
        readme = (
            f"Wassily I-O Data Bundle — Year {year}\n"
            f"=====================================\n\n"
            f"Contents: {csv_count} CSV file(s)\n\n"
            f"Provenance\n"
            f"----------\n"
            + "\n".join(provenance_lines)
            + "\n\n"
            f"Source: Bureau of Economic Analysis (BEA) Input-Output Accounts\n"
            f"Site: https://leontief.nickanderson.us\n"
            f"Generated: {manifest.get('generated', 'unknown')}\n"
        )
        zf.writestr("README.txt", readme.encode("utf-8"))

    filename = f"wassily_io_{year}.zip"
    return buf.getvalue(), "application/zip", filename


def bundle_all_zip() -> tuple[bytes, str, str]:
    """Build an in-memory zip of every matrix CSV across all years.

    Also includes:
    - README.txt  (top-level provenance)
    - sectors.json
    - site_manifest.json
    """
    manifest = _load_manifest()
    tables = manifest.get("tables", [])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        for t in tables:
            year = t["year"]
            matrix = t["matrix"]
            try:
                df = _read_matrix_parquet(year, matrix)
            except FileNotFoundError:
                continue
            csv_bytes = df.to_csv(index=True).encode("utf-8")
            arc_name = f"{year}/wassily_{matrix}_{year}.csv"
            zf.writestr(arc_name, csv_bytes)

        # Static data files
        sectors_path = SITE_DATA / "sectors.json"
        if sectors_path.exists():
            zf.write(sectors_path, "sectors.json")

        manifest_path = get_manifest_path()
        if manifest_path.exists():
            zf.write(manifest_path, "site_manifest.json")

        # Top-level README
        years_covered = sorted(set(t["year"] for t in tables))
        year_range = f"{min(years_covered)}–{max(years_covered)}" if years_covered else "unknown"
        readme = (
            f"Wassily I-O Data Bundle — All Years\n"
            f"=====================================\n\n"
            f"Years: {year_range}  ({len(years_covered)} annual tables)\n"
            f"Matrices per year: Use, Supply, A, A_square, L, VA, FD\n"
            f"Sector count: {manifest.get('coverage', {}).get('sector_count', 71)}\n"
            f"Classification: {manifest.get('coverage', {}).get('classification', 'BEA Summary')}\n\n"
            f"Directory layout: <year>/wassily_<matrix>_<year>.csv\n\n"
            f"Source: Bureau of Economic Analysis (BEA) Input-Output Accounts\n"
            f"Site: https://leontief.nickanderson.us\n"
            f"Generated: {manifest.get('generated', 'unknown')}\n"
        )
        zf.writestr("README.txt", readme.encode("utf-8"))

    return buf.getvalue(), "application/zip", "wassily_io_all.zip"


def study_bundle_zip(slug: str) -> tuple[bytes, str, str]:
    """Build an in-memory zip for a study code bundle.

    Bundles:
    - All files under content/studies/code/<slug>/
    - Any cached artifacts named study__{slug}__* in CACHE_DIR

    Raises FileNotFoundError with a clear message if neither source exists yet.
    Studies are authored in a later work package; this implementation is
    forward-compatible and will work once those files are placed.
    """
    code_dir = CONTENT_DIR / "studies" / "code" / slug
    cache_artifacts = list(CACHE_DIR.glob(f"study__{slug}__*"))

    if not code_dir.exists() and not cache_artifacts:
        raise FileNotFoundError(
            f"Study {slug!r} not found. "
            f"Expected code directory: {code_dir}  "
            f"or cached artifacts matching: {CACHE_DIR}/study__{slug}__*  "
            f"Studies are authored in a later work package."
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        # Code directory tree
        if code_dir.exists():
            for fpath in sorted(code_dir.rglob("*")):
                if fpath.is_file():
                    arc_name = "code/" + str(fpath.relative_to(code_dir)).replace("\\", "/")
                    zf.write(fpath, arc_name)

        # Cached study artifacts
        for fpath in sorted(cache_artifacts):
            zf.write(fpath, "cache/" + fpath.name)

    filename = f"wassily_study_{slug}.zip"
    return buf.getvalue(), "application/zip", filename
