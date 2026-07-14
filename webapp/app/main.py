"""FastAPI application factory for the Leontief website.

Usage:
    uvicorn app.main:app --reload --port 8080
"""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from carson_telemetry import telemetry  # Carson Telemetry Standard §4 (Layer-3 usage events)

from app import config as C
from app import chrome  # Arcanum Site Kit (ASK) v1 — shared-chrome context processor

logger = logging.getLogger(__name__)


def _load_manifest_at_startup(app: FastAPI) -> None:
    """Attempt to load site_manifest.json into app.state at startup.

    Non-fatal: the site boots and serves stub pages even if the manifest
    has not been built yet (build_cache.py has not been run).
    """
    mp = C.get_manifest_path()
    if mp.exists():
        try:
            with open(mp, encoding="utf-8") as f:
                app.state.manifest = json.load(f)
            logger.info("Manifest loaded: %d tables, %d series, %d studies",
                        len(app.state.manifest.get("tables", [])),
                        len(app.state.manifest.get("series", [])),
                        len(app.state.manifest.get("studies", [])))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load manifest: %s", exc)
            app.state.manifest = {}
    else:
        logger.info("site_manifest.json not found — run data_pipeline/build_cache.py to generate it")
        app.state.manifest = {}


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Lifespan handler: startup → yield → shutdown."""
    _load_manifest_at_startup(app)
    yield
    # Nothing to clean up on shutdown


def _asset_ver(static_dir) -> str:
    """Short content hash of the vendored kit (_shared) + site css/js — changes
    whenever any of those change, so ?v=<hash> busts the CDN cache on deploy."""
    import hashlib
    from pathlib import Path
    h = hashlib.md5()
    root = Path(static_dir)
    for sub in ("_shared", "css", "js"):
        d = root / sub
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                try:
                    h.update(p.read_bytes())
                except Exception:  # noqa: BLE001
                    pass
    return h.hexdigest()[:8]


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    C.ensure_dirs()

    app = FastAPI(
        title=f"{C.SITE_TITLE} — {C.SITE_TAGLINE}",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=_lifespan,
    )

    # ------------------------------------------------------------------
    # Carson telemetry (TELEMETRY_STANDARD.md §4) — Layer-3 usage events.
    # Emits one usage_events row per request (surface="rest"/"download") into
    # the shared SQLite DB at $CARSON_TELEMETRY_DB. Download routes are tagged
    # explicitly via telemetry.record_download() in app/routers/api.py, since
    # Leontief's downloads live under /api/table|series|bulk and /…/bundle.zip
    # (not the library's default /download prefix).
    app.add_middleware(telemetry.ASGIMiddleware, service="leontief")

    # ------------------------------------------------------------------
    # Jinja2 templates
    # ------------------------------------------------------------------
    # context_processors=[chrome.ark_context] injects the Arcanum Site Kit
    # shared-chrome vars (site_key, site_title, site_home, dpr_url, ecosystem,
    # nav) into EVERY TemplateResponse — no per-route changes needed.
    templates = Jinja2Templates(
        directory=str(C.TEMPLATES_DIR),
        context_processors=[chrome.ark_context],
    )
    templates.env.globals["site_title"] = C.SITE_TITLE
    templates.env.globals["tagline"] = C.SITE_TAGLINE
    # asset_ver: short content-hash of the vendored kit + site static, stamped as
    # ?v=<hash> on asset URLs so a kit/CSS/JS change busts the Cloudflare cache
    # automatically (the box has no CF purge token; kit assets are cached 4h).
    templates.env.globals["asset_ver"] = _asset_ver(C.STATIC_DIR)
    app.state.templates = templates

    # ------------------------------------------------------------------
    # Static files
    # ------------------------------------------------------------------
    app.mount("/static", StaticFiles(directory=str(C.STATIC_DIR)), name="static")

    # ------------------------------------------------------------------
    # Routers — guarded imports so the app boots even if router files
    # reference services that are still stubs.
    # ------------------------------------------------------------------
    try:
        from app.routers import pages as pages_router
        app.include_router(pages_router.router)
    except Exception as exc:  # noqa: BLE001
        logger.warning("pages router unavailable: %s", exc)

    try:
        from app.routers import api as api_router
        app.include_router(api_router.router)
    except Exception as exc:  # noqa: BLE001
        logger.warning("api router unavailable: %s", exc)

    # ------------------------------------------------------------------
    # Health check (always present regardless of router status)
    # ------------------------------------------------------------------
    @app.get("/healthz", tags=["ops"])
    async def healthz(request: Request):  # noqa: ANN201
        manifest = getattr(request.app.state, "manifest", {})
        return JSONResponse({
            "status": "ok",
            "site": C.SITE_TITLE,
            "manifest_present": bool(manifest),
            "tables": len(manifest.get("tables", [])),
            "series": len(manifest.get("series", [])),
            "studies": len(manifest.get("studies", [])),
        })

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)
