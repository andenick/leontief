"""HTML page routes (server-rendered Jinja2).

All routes are fully implemented.  The /tables route renders tables.html which
is owned by a later work-package; if that file does not exist yet, a minimal
inline placeholder is returned so the route never 500s.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from app import config as C
from app.services import narrative_service as NS
from app.services import data_service as DS

router = APIRouter(tags=["pages"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _t(request: Request):
    """Retrieve Jinja2 Templates from app state."""
    return request.app.state.templates


def _ctx(request: Request, **kw) -> dict:
    """Base template context merged with extra keyword args."""
    base = {
        "request": request,
        "site_title": C.SITE_TITLE,
        "tagline": C.SITE_TAGLINE,
    }
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
    """I-O Table Explorer — template provided by later work-package."""
    templates = _t(request)
    tables_tmpl = C.TEMPLATES_DIR / "tables.html"
    if tables_tmpl.exists():
        return templates.TemplateResponse(
            request,
            "tables.html",
            _ctx(request, section="Tables"),
        )
    # Placeholder until tables.html is delivered
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<title>Tables — Wassily</title>
<link rel="stylesheet" href="/static/css/site.css">
</head>
<body>
<header class="nav"><div class="inner">
  <a class="brand" href="/">Wassily</a>
  <nav><a href="/learn">Learn</a> <a href="/tables" class="active">Tables</a>
  <a href="/studies">Studies</a> <a href="/data">Data</a></nav>
</div></header>
<main class="content"><div class="container">
  <h1>I-O Table Explorer</h1>
  <div class="stub-notice">
    <strong>Coming soon:</strong> The interactive table explorer is being built.
    In the meantime, browse the <a href="/data">Data catalog</a> for direct downloads.
  </div>
</div></main>
</body></html>""",
        status_code=200,
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

    # Derive list of code files from manifest (studies entry)
    code_files: list[str] = []
    manifest_studies = DS.list_studies()
    for s in manifest_studies:
        if s.get("slug") == slug or s.get("key") == slug:
            code_files = s.get("code_files", [])
            break

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
        ),
    )


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
