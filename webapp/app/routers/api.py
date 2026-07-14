"""JSON + download API endpoints for the Leontief I-O website.

Router is included by main.py with no extra prefix; the router itself
declares prefix="/api".  All routes below are relative to /api.

Route table
-----------
GET /api/ping                             -- liveness
GET /api/chart/{chart_key:path}          -- Plotly JSON (compound keys supported)
GET /api/table/{year}/{matrix}.{fmt}     -- matrix download (csv/xlsx/json/parquet)  [DECLARED FIRST]
GET /api/table/{year}/{matrix}           -- matrix JSON payload
GET /api/series/{key}.{fmt}             -- series download
GET /api/study/{slug}/bundle.zip        -- study code bundle (404 until authored)
GET /api/bulk/all.zip                   -- entire dataset  [DECLARED BEFORE {year}.zip]
GET /api/bulk/{year}.zip                -- all matrices for one year
GET /api/search?q=                      -- sector + page search
GET /api/file/{relpath:path}            -- serve source file (guarded)

Route ordering notes
--------------------
- /table/{year}/{matrix}.{fmt} is declared BEFORE /table/{year}/{matrix} so that
  requests like /table/2002/L.csv match the download handler. FastAPI (Starlette)
  matches routes in declaration order; a path param like ``{matrix}`` would
  otherwise greedily consume the ``L.csv`` segment before the dotted route fires.
  The Starlette router uses Convertors that distinguish literal segments from
  parameterised ones: ``{matrix}.{fmt}`` with an embedded literal dot is treated
  as a more-specific pattern and matches before the bare ``{matrix}`` pattern
  when declared first.
- /bulk/all.zip before /bulk/{year}.zip so "all" is not parsed as a year.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from carson_telemetry import telemetry  # Carson Telemetry Standard §4 (download events)

from app import config as C

logger = logging.getLogger(__name__)


def _emit_download(endpoint: str, raw: bytes) -> None:
    """Record a surface="download" usage event (TELEMETRY_STANDARD.md §3/§4).

    The ASGI middleware already logs every request as surface="rest"; these
    explicit calls re-classify the genuine data/code downloads so download
    counts are correct. ``endpoint`` is a route template (names only, never
    argument values, per §3). Telemetry must never break the request path.
    """
    try:
        telemetry.record_download("leontief", endpoint, bytes=len(raw or b""))
    except Exception:  # noqa: BLE001 — telemetry is best-effort, never fatal
        logger.debug("download telemetry emit failed for %s", endpoint, exc_info=True)

router = APIRouter(prefix="/api", tags=["api"])

# ---------------------------------------------------------------------------
# WEBAPP root — used for /file guard
# ---------------------------------------------------------------------------
_WEBAPP_ROOT: Path = C.WEBAPP_ROOT.resolve()

# Extensions allowed by /file endpoint
_ALLOWED_EXTENSIONS = {".py", ".ipynb", ".txt", ".md", ".csv", ".parquet"}

# Binary extensions served as a download (not inline text/plain)
_BINARY_EXTENSIONS = {".parquet"}
_BINARY_MEDIA = {".parquet": "application/vnd.apache.parquet"}

# ---------------------------------------------------------------------------
# Static page catalogue for /search
# ---------------------------------------------------------------------------
_PAGES: list[dict[str, str]] = [
    {"title": "Home",        "url": "/"},
    {"title": "Learn",       "url": "/learn"},
    {"title": "Tables",      "url": "/tables"},
    {"title": "Studies",     "url": "/studies"},
    {"title": "Data",        "url": "/data"},
    {"title": "Code",        "url": "/code"},
    {"title": "Methodology", "url": "/methodology"},
    {"title": "About",       "url": "/about"},
]


# ---------------------------------------------------------------------------
# Ping / liveness
# ---------------------------------------------------------------------------

@router.get("/ping")
def ping() -> JSONResponse:
    """Simple liveness probe."""
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

@router.get("/chart/{chart_key:path}")
def chart(
    chart_key: str,
    year: int | None = Query(default=None),
    matrix: str | None = Query(default=None),
    agg: str | None = Query(default=None),
    n: int | None = Query(default=None),
    key: str | None = Query(default=None),
    columns: str | None = Query(default=None),
) -> JSONResponse:
    """Return a Plotly JSON figure for a registered chart key.

    Accepts compound keys in the path (e.g. ``heatmap:2002:L:15``) and
    optional query parameters that are forwarded to the chart builder.
    """
    from app.services.chart_service import build_chart

    # Build the kwargs dict from query params that were supplied
    params: dict[str, Any] = {}
    if year is not None:
        params["year"] = year
    if matrix is not None:
        params["matrix"] = matrix
    if agg is not None:
        params["agg"] = agg
    if n is not None:
        params["n"] = n
    if key is not None:
        params["key"] = key
    if columns is not None:
        # Accept comma-separated column names
        params["columns"] = [c.strip() for c in columns.split(",") if c.strip()]

    try:
        result = build_chart(chart_key, **params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("chart build failed for key=%r params=%r", chart_key, params)
        raise HTTPException(status_code=500, detail=f"Chart build error: {exc}") from exc

    return JSONResponse(result)


# ---------------------------------------------------------------------------
# Table — download  (MUST be declared BEFORE the plain JSON route)
#
# FastAPI/Starlette matches routes in declaration order. The plain route
# /table/{year}/{matrix} would greedily capture "L.csv" as matrix="L.csv"
# if it came first.  By declaring the dotted route first, Starlette picks
# the more-specific (literal-dot-containing) pattern first.
# ---------------------------------------------------------------------------

@router.get("/table/{year}/{matrix}.{fmt}")
def table_download(year: int, matrix: str, fmt: str) -> Response:
    """Download a matrix as csv / xlsx / parquet.

    URL shape: /api/table/2002/L.csv
    """
    from app.services.download_service import export_matrix

    try:
        raw, media, filename = export_matrix(year, matrix, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("table_download failed year=%r matrix=%r fmt=%r", year, matrix, fmt)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/table/{year}/{matrix}.{fmt}", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Table — JSON payload
# ---------------------------------------------------------------------------

@router.get("/table/{year}/{matrix}")
def table_json(
    year: int,
    matrix: str,
    agg: str | None = Query(default=None),
    search: str | None = Query(default=None),
    fmt: str | None = Query(default=None),
) -> Response:
    """Return the matrix as a JSON payload for the Explorer grid / heatmap.

    If ``?fmt=csv|xlsx|json|parquet`` is supplied, this delegates to the file
    download handler so that catalog links of the form
    ``/api/table/{year}/{matrix}?fmt=csv`` return a real downloadable file with
    the correct Content-Type (the dotted route ``.{fmt}`` is the canonical
    equivalent). Without ``fmt`` it returns the Explorer JSON payload.
    """
    if fmt is not None:
        return table_download(year, matrix, fmt)

    from app.services.table_service import matrix_payload

    try:
        payload = matrix_payload(year, matrix, agg=agg, search=search)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("table_json failed year=%r matrix=%r", year, matrix)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(payload)


# ---------------------------------------------------------------------------
# Series — download
# ---------------------------------------------------------------------------

@router.get("/series/{key}.{fmt}")
def series_download(key: str, fmt: str) -> Response:
    """Download a derived series as csv / xlsx / json / parquet.

    URL shape: /api/series/multiplier_timeseries.csv
    """
    from app.services.download_service import export_series

    try:
        raw, media, filename = export_series(key, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("series_download failed key=%r fmt=%r", key, fmt)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/series/{key}.{fmt}", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Series — query-param download (catalog links use ?fmt=…)
#
# The catalog template links to /api/series/{key}?fmt=csv (no dotted ext); that
# would otherwise 404 since only the dotted route above exists. Honor ?fmt= by
# delegating to series_download. ``fmt`` defaults to csv so a bare key still
# yields a file rather than a 404.
# ---------------------------------------------------------------------------

@router.get("/series/{key}")
def series_query(key: str, fmt: str = Query(default="csv")) -> Response:
    """Download a derived series, format chosen via ``?fmt=``."""
    return series_download(key, fmt)


# ---------------------------------------------------------------------------
# Study bundle
# ---------------------------------------------------------------------------

@router.get("/study/{slug}/bundle.zip")
def study_bundle(slug: str) -> Response:
    """Return a zip bundle for a study (code + data).

    Returns 404 until study files are authored.
    """
    from app.services.download_service import study_bundle_zip

    try:
        raw, media, filename = study_bundle_zip(slug)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Study '{slug}' not yet available: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("study_bundle failed slug=%r", slug)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/study/{slug}/bundle.zip", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Code bundle (CDF Code triad leg) — pre-built matrix-build + study code zip.
# ---------------------------------------------------------------------------

@router.get("/code/bundle.zip")
def code_bundle() -> Response:
    """Download the matrix-build + study-analysis code bundle (Python + R)."""
    from app.services.download_service import code_bundle_zip

    try:
        raw, media, filename = code_bundle_zip()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("code_bundle failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/code/bundle.zip", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Bulk downloads
#
# /bulk/all.zip must be declared BEFORE /bulk/{year}.zip: "all" would otherwise
# be parsed as a year integer (and fail coercion, returning 422 instead of 200).
# ---------------------------------------------------------------------------

@router.get("/bulk/all.zip")
def bulk_all() -> Response:
    """Download the entire dataset as a zip archive."""
    from app.services.download_service import bundle_all_zip

    try:
        raw, media, filename = bundle_all_zip()
    except Exception as exc:  # noqa: BLE001
        logger.exception("bulk_all failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/bulk/all.zip", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/bulk/{year}.zip")
def bulk_year(year: int) -> Response:
    """Download all matrices for a single year as a zip archive."""
    from app.services.download_service import bundle_year_zip

    try:
        raw, media, filename = bundle_year_zip(year)
    except Exception as exc:  # noqa: BLE001
        logger.exception("bulk_year failed year=%r", year)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _emit_download("/api/bulk/{year}.zip", raw)
    return Response(
        content=raw,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search")
def search(q: str = Query(default="")) -> JSONResponse:
    """Search sector codes/names and site pages.

    Returns::

        {
            "sectors": [{"code": str, "name": str}, ...],
            "pages":   [{"title": str, "url": str}, ...]
        }
    """
    from app.services.data_service import load_sectors

    sector_hits: list[dict[str, str]] = []
    page_hits: list[dict[str, str]] = []

    if q:
        q_lower = q.strip().lower()

        # Sector search
        try:
            sectors_data = load_sectors()
            for sec in sectors_data.get("sectors", []):
                code: str = sec.get("code", "")
                name: str = sec.get("name", "")
                if q_lower in code.lower() or q_lower in name.lower():
                    sector_hits.append({"code": code, "name": name})
        except FileNotFoundError:
            pass  # sectors not built yet — return empty

        # Page search (title keyword match)
        for page in _PAGES:
            if q_lower in page["title"].lower() or q_lower in page["url"].lower():
                page_hits.append(page)

    return JSONResponse({"sectors": sector_hits, "pages": page_hits})


# ---------------------------------------------------------------------------
# File serve (guarded)
# ---------------------------------------------------------------------------

@router.get("/file/{relpath:path}")
def serve_file(relpath: str) -> Response:
    """Serve a source file from under the webapp directory as text/plain.

    Guards:
    - Resolves the path and asserts it stays under WEBAPP_ROOT (no traversal).
    - Only allows extensions: .py .ipynb .txt .md .csv
    - Returns 404 if the file does not exist or is a directory.
    - Returns 403 if the path escapes WEBAPP_ROOT or has a disallowed extension.
    """
    # Normalise any URL-encoded separators and strip leading slashes
    clean_rel = relpath.replace("\\", "/").lstrip("/")

    try:
        resolved = (_WEBAPP_ROOT / clean_rel).resolve()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=403, detail="Invalid path") from exc

    # Guard: must stay inside webapp root
    try:
        resolved.relative_to(_WEBAPP_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Path traversal not allowed",
        )

    # Guard: extension whitelist
    if resolved.suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=403,
            detail=f"Extension '{resolved.suffix}' not allowed. "
                   f"Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )

    # Guard: must be a regular file
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {relpath}",
        )

    ext = resolved.suffix.lower()
    if ext in _BINARY_EXTENSIONS:
        raw = resolved.read_bytes()
        return Response(
            content=raw,
            media_type=_BINARY_MEDIA.get(ext, "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="{resolved.name}"'},
        )

    content = resolved.read_text(encoding="utf-8", errors="replace")
    return Response(content=content, media_type="text/plain; charset=utf-8")
