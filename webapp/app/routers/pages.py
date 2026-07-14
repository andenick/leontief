"""HTML page routes (server-rendered Jinja2).

All routes are fully implemented.  The /tables route renders tables.html which
is owned by a later work-package; if that file does not exist yet, a minimal
inline placeholder is returned so the route never 500s.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from app import config as C
from app.services import narrative_service as NS
from app.services import data_service as DS
from app.services import anu_service as ANU

router = APIRouter(tags=["pages"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _t(request: Request):
    """Retrieve Jinja2 Templates from app state."""
    return request.app.state.templates


def _prov_globals() -> dict:
    """Honest site-wide provenance facts for the shared .ark-provenance panel
    (Carson DNA A7/A10). Read once from the data manifest so the build/retrieval
    date, coverage years and sector count are real, never invented."""
    try:
        manifest = DS.load_manifest()
    except Exception:  # noqa: BLE001
        manifest = {}
    coverage = manifest.get("coverage", {}) or {}
    years: list[int] = []
    try:
        years = sorted(
            t["year"] for t in DS.list_tables() if t.get("year") is not None
        )
        years = sorted(set(years))
    except Exception:  # noqa: BLE001
        years = []
    return {
        "manifest_generated": manifest.get("generated", ""),
        "coverage": coverage,
        "years_sorted": years,
    }


def _ctx(request: Request, **kw) -> dict:
    """Base template context merged with extra keyword args."""
    base = {
        "request": request,
        "site_title": C.SITE_TITLE,
        "tagline": C.SITE_TAGLINE,
    }
    # Provenance facts available on every page (caller kw can override).
    base.update(_prov_globals())
    base.update(kw)
    return base


def _not_found_html(request: Request, message: str) -> Response:
    """Render a simple 404 page using narrative.html (or a minimal fallback)."""
    templates = _t(request)
    try:
        return templates.TemplateResponse(
            request,
            "narrative.html",
            _ctx(
                request,
                section="",
                title="Not Found",
                doc_html=f"<p>{message}</p>",
                citations=[],
            ),
            status_code=404,
        )
    except Exception:
        return HTMLResponse(
            f"<html><body><h1>404 Not Found</h1><p>{message}</p></body></html>",
            status_code=404,
        )


def _safe_render_doc(relpath: str) -> dict:
    """Render a content doc; return a placeholder dict if missing."""
    try:
        return NS.render_doc(relpath)
    except FileNotFoundError:
        name = Path(relpath).stem.replace("-", " ").replace("_", " ").title()
        return {
            "meta": {"title": name},
            "html": (
                f"<div class='stub-notice'>"
                f"<strong>{name}</strong> — content coming soon."
                f"</div>"
            ),
            "citations": [],
        }


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Landing page — hero with live stats and section cards."""
    # Pull counts from services (gracefully degrade if manifest not yet built)
    learn_docs  = NS.list_docs("learn")
    study_docs  = NS.list_docs("studies")
    series      = DS.list_series()

    n_tutorials = len(learn_docs)
    n_studies   = len(study_docs)
    n_years     = len(C.BEA_YEARS)           # 28
    n_sectors   = C.SECTOR_COUNT             # 71

    return _t(request).TemplateResponse(
        request,
        "home.html",
        _ctx(
            request,
            section="Home",
            n_tutorials=n_tutorials,
            n_studies=n_studies,
            n_years=n_years,
            n_sectors=n_sectors,
        ),
    )


# ---------------------------------------------------------------------------
# Learn track
# ---------------------------------------------------------------------------

@router.get("/learn", response_class=HTMLResponse)
def learn_index(request: Request):
    """Ordered tutorial curriculum."""
    tutorials = NS.list_docs("learn")
    return _t(request).TemplateResponse(
        request,
        "learn_index.html",
        _ctx(request, section="Learn", tutorials=tutorials),
    )


@router.get("/learn/{slug}", response_class=HTMLResponse)
def learn_tutorial(request: Request, slug: str):
    """Individual tutorial page with KaTeX + code blocks."""
    try:
        result = NS.render_doc(f"learn/{slug}.md")
    except FileNotFoundError:
        return _not_found_html(request, f"Tutorial '{slug}' not found.")

    # Build prev/next nav
    tutorials = NS.list_docs("learn")
    slugs = [t["slug"] for t in tutorials]
    idx   = slugs.index(slug) if slug in slugs else -1
    prev_doc = tutorials[idx - 1] if idx > 0 else None
    next_doc = tutorials[idx + 1] if 0 <= idx < len(tutorials) - 1 else None

    # Build "On this page" anchors from h2/h3 in the rendered HTML
    import re
    headings = re.findall(r'<h[23][^>]*id="([^"]+)"[^>]*>(.*?)</h[23]>', result["html"])
    # Fall back: extract headings without id
    if not headings:
        headings = []

    return _t(request).TemplateResponse(
        request,
        "tutorial.html",
        _ctx(
            request,
            section="Learn",
            title=result["meta"].get("title", slug),
            doc_html=result["html"],
            citations=result["citations"],
            meta=result["meta"],
            prev_doc=prev_doc,
            next_doc=next_doc,
            headings=headings,
        ),
    )


# ---------------------------------------------------------------------------
# I-O Table Explorer  (template owned by later WP)
# ---------------------------------------------------------------------------

@router.get("/tables", response_class=HTMLResponse)
def tables(request: Request):
    """I-O Table Explorer (tables.html — full kit chrome via base.html)."""
    return _t(request).TemplateResponse(
        request,
        "tables.html",
        _ctx(request, section="Tables"),
    )


# ---------------------------------------------------------------------------
# Studies
# ---------------------------------------------------------------------------

@router.get("/studies", response_class=HTMLResponse)
def studies_index(request: Request):
    """Card grid of example studies."""
    studies = NS.list_docs("studies")
    return _t(request).TemplateResponse(
        request,
        "studies_index.html",
        _ctx(request, section="Studies", studies=studies),
    )


@router.get("/studies/{slug}", response_class=HTMLResponse)
def study(request: Request, slug: str):
    """Individual study with narrative + charts + download bundle."""
    try:
        result = NS.render_doc(f"studies/{slug}.md")
    except FileNotFoundError:
        return _not_found_html(request, f"Study '{slug}' not found.")

    # Derive code files + primary data table from manifest (studies entry)
    code_files: list[str] = []
    data_tables: list[str] = []
    for s in DS.list_studies():
        if s.get("slug") == slug or s.get("key") == slug:
            code_files = s.get("code_files", [])
            data_tables = s.get("tables", [])
            break

    # Primary-data download links (STUDY_PAGE_STANDARD: CSV + parquet). The study
    # writes its result table to content/studies/code/<slug>/outputs/<table>.csv
    # (with a generated .parquet companion); both are served by /api/file.
    data_downloads: dict[str, str] | None = None
    if data_tables:
        primary = data_tables[0]
        base = f"content/studies/code/{slug}/outputs/{primary}"
        data_downloads = {
            "name": primary,
            "csv": f"/api/file/{base}.csv",
            "parquet": f"/api/file/{base}.parquet",
        }

    # Replication-code permalink (pinned commit). STUDY_PAGE_STANDARD wants a
    # GitHub permalink; we point at the exact study analysis.py at the pinned ref.
    repo = C.GITHUB_URL.rstrip("/")
    # Study code lives under webapp/ in the public repo (github.com/andenick/leontief);
    # the path MUST include the webapp/ prefix or the permalink 404s (LEF-2).
    code_permalink = f"{repo}/blob/{C.GITHUB_PIN}/webapp/content/studies/code/{slug}/analysis.py"

    return _t(request).TemplateResponse(
        request,
        "study.html",
        _ctx(
            request,
            section="Studies",
            title=result["meta"].get("title", slug),
            doc_html=result["html"],
            citations=result["citations"],
            meta=result["meta"],
            slug=slug,
            code_files=code_files,
            data_downloads=data_downloads,
            code_permalink=code_permalink,
        ),
    )


# ---------------------------------------------------------------------------
# /download — convenience alias so a hand-typed URL lands on the catalog.
# The nav points at /data (canonical); /download just redirects there so a
# visitor typing it is not dead-ended on a JSON 404.
# ---------------------------------------------------------------------------

@router.get("/download")
def download_redirect():
    """Redirect /download to the canonical /data catalog (308 permanent)."""
    return RedirectResponse(url="/data", status_code=308)


# ---------------------------------------------------------------------------
# llms.txt — agent-first resource map (CODE_DATA_FIRST_STANDARD.md §B1.5).
# Generated from ecosystem.json's cdf block by data_pipeline (make_llms_txt.py)
# and shipped in site_data/llms.txt.
# ---------------------------------------------------------------------------

@router.get("/llms.txt")
def llms_txt():
    """Serve the agent-first resource map as text/plain."""
    p = C.SITE_DATA / "llms.txt"
    if not p.exists():
        return Response(content="llms.txt not available", status_code=404,
                        media_type="text/plain; charset=utf-8")
    return Response(content=p.read_text(encoding="utf-8"),
                    media_type="text/plain; charset=utf-8")


# ---------------------------------------------------------------------------
# Data catalog
# ---------------------------------------------------------------------------

@router.get("/data", response_class=HTMLResponse)
def data_catalog(request: Request):
    """Machine-readable catalog: matrices + derived series, all download links."""
    tables  = DS.list_tables()
    series  = DS.list_series()

    # Group matrix tables by year for display
    # Each entry: {year, matrix, dims, csv, xlsx, json, parquet}
    by_year: dict[int, list[dict]] = {}
    for t in tables:
        yr = t.get("year")
        if yr is None:
            continue
        by_year.setdefault(yr, []).append(t)

    years_sorted = sorted(by_year.keys())

    # --------------------------------------------------------------
    # Data inventory: one row per raw/derived BEA dataset type, with
    # the vintage span, count, dimensions, source identifier, and the
    # snapshot (build) date recorded in the manifest. Lets a user see
    # exactly which BEA datasets underlie the whole site at a glance.
    # --------------------------------------------------------------
    try:
        manifest = DS.load_manifest()
    except Exception:  # noqa: BLE001
        manifest = {}
    manifest_generated = manifest.get("generated", "")
    coverage = manifest.get("coverage", {})

    # Per matrix-type: count, year span, dims (from a sample entry), provenance
    _MATRIX_KIND = {
        "Use":      ("raw",     "BEA Use table (Use_IxI_Summary_YYYY.json) — commodity × industry intermediate use + final demand"),
        "Supply":   ("raw",     "BEA Supply/Make table (Supply_IxI_Summary_YYYY.json) — commodity × industry production"),
        "L":        ("raw",     "BEA Total Requirements / Leontief inverse (Total_Requirements_IxI_Summary_YYYY.json)"),
        "A":        ("derived", "Direct-requirements coefficients (non-square 70×71), derived from the Use table"),
        "A_square": ("derived", "Direct-requirements coefficients, squared to the row∩col intersection"),
        "VA":       ("derived", "Value-added rows (V-codes) extracted from the BEA accounts"),
        "FD":       ("derived", "Final-demand columns (F-codes) extracted from the Use table"),
    }
    inventory: list[dict] = []
    for mk in C.MATRIX_KEYS:
        entries = [t for t in tables if t.get("matrix") == mk]
        if not entries:
            continue
        yrs = sorted(t["year"] for t in entries if t.get("year") is not None)
        sample = entries[0]
        kind, desc = _MATRIX_KIND.get(mk, ("", sample.get("provenance", "")))
        inventory.append({
            "matrix": mk,
            "kind": kind,
            "description": desc,
            "count": len(entries),
            "year_min": yrs[0] if yrs else None,
            "year_max": yrs[-1] if yrs else None,
            "dims": f"{sample.get('rows', '?')} × {sample.get('cols', '?')}",
        })

    return _t(request).TemplateResponse(
        request,
        "catalog.html",
        _ctx(
            request,
            section="Data",
            by_year=by_year,
            years_sorted=years_sorted,
            matrix_keys=list(C.MATRIX_KEYS),
            series=series,
            inventory=inventory,
            manifest_generated=manifest_generated,
            coverage=coverage,
        ),
    )


# ---------------------------------------------------------------------------
# Code mode — Anu-pipeline explainer + GitHub button
# ---------------------------------------------------------------------------

@router.get("/code", response_class=HTMLResponse)
def code(request: Request):
    """Code mode — friendly explainer of the Anu pipeline stages + GitHub link."""
    return _t(request).TemplateResponse(
        request,
        "code.html",
        _ctx(
            request,
            section="Code",
            stages=ANU.stages(),
            github_url=C.GITHUB_URL,
        ),
    )


# ---------------------------------------------------------------------------
# Static narrative pages
# ---------------------------------------------------------------------------

@router.get("/methodology", response_class=HTMLResponse)
def methodology(request: Request):
    """BEA accounts + derivation methodology."""
    result = _safe_render_doc("methodology.md")
    return _t(request).TemplateResponse(
        request,
        "narrative.html",
        _ctx(
            request,
            section="Methodology",
            title=result["meta"].get("title", "Methodology"),
            doc_html=result["html"],
            citations=result["citations"],
            show_provenance=True,
        ),
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    """Project + reproducibility philosophy + how to cite."""
    result = _safe_render_doc("about.md")
    return _t(request).TemplateResponse(
        request,
        "narrative.html",
        _ctx(
            request,
            section="About",
            title=result["meta"].get("title", "About"),
            doc_html=result["html"],
            citations=result["citations"],
        ),
    )


@router.get("/glossary", response_class=HTMLResponse)
def glossary(request: Request):
    """I-O terminology glossary."""
    result = _safe_render_doc("glossary.md")
    return _t(request).TemplateResponse(
        request,
        "glossary.html",
        _ctx(
            request,
            section="Glossary",
            title=result["meta"].get("title", "Glossary"),
            doc_html=result["html"],
            citations=result["citations"],
        ),
    )
