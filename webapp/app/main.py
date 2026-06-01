"""FastAPI application factory for the Wassily (Leontief) website.

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

from app import config as C

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
    # Jinja2 templates
    # ------------------------------------------------------------------
    templates = Jinja2Templates(directory=str(C.TEMPLATES_DIR))
    templates.env.globals["site_title"] = C.SITE_TITLE
    templates.env.globals["tagline"] = C.SITE_TAGLINE
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
