"""Arcanum Site Kit (ASK) v1 — shared-chrome context processor.

This is the single mechanism that injects the shared header/footer/switcher
variables into **every** Jinja template render, regardless of which route or
helper builds the per-route context. It is wired in ``main.py`` via::

    Jinja2Templates(directory=..., context_processors=[chrome.ark_context])

Starlette runs each context processor for every ``TemplateResponse`` (it
receives only the ``Request`` and returns a dict that is merged into the
context), so no per-route edits are needed and existing per-route variables are
preserved. The keys injected here (``ecosystem``, ``nav``, ``site_key``, …) do
not collide with leontief's page variables.

Reference recipe for the other seven FastAPI+Jinja sites: copy this file, change
``SITE_KEY`` / ``SITE_TITLE`` / ``DPR_URL`` and the ``NAV`` table to the site's
real routes, and add the ``context_processors=[chrome.ark_context]`` argument to
the site's ``Jinja2Templates(...)`` call.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from starlette.requests import Request

from app import config as C

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-site identity (the only values another site changes)
# ---------------------------------------------------------------------------
SITE_KEY: str = "leontief"            # ecosystem.json site.key -> switcher "current"
SITE_HOME: str = "/"                  # what the site title links to
DPR_URL: str = "/methodology"         # this site's provenance / DPR target (footer link)

# Blueprint nav vocabulary mapped to leontief's REAL routes.
# Each entry: (label, href). ``active`` is computed per request from the path.
NAV: list[tuple[str, str]] = [
    ("Learn",       "/learn"),
    ("Explore",     "/tables"),
    ("Studies",     "/studies"),
    ("Data",        "/data"),
    ("Code",        "/code"),
    ("Methodology", "/methodology"),
    ("About",       "/about"),
]

# Vendored canonical manifest (served at /static/_shared/ecosystem.json).
_ECOSYSTEM_PATH = C.STATIC_DIR / "_shared" / "ecosystem.json"


@lru_cache(maxsize=1)
def load_ecosystem() -> dict:
    """Parse the vendored ecosystem.json once (cached). Non-fatal on error."""
    try:
        with open(_ECOSYSTEM_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001 — chrome must never break a render
        logger.warning("ecosystem.json not loaded (%s): %s", _ECOSYSTEM_PATH, exc)
        return {}


def _nav_for(path: str) -> list[dict]:
    """Build the nav list with ``active`` set from the current request path.

    Path-derived (not section-derived) so it is route-agnostic: any route under
    a section's prefix lights the right tab without the route having to remember
    to pass ``section``. A nav item is active when the path equals its href or
    sits beneath it (e.g. /learn/04-... -> Learn).
    """
    items: list[dict] = []
    for label, href in NAV:
        active = path == href or (href != "/" and path.startswith(href + "/"))
        items.append({"label": label, "href": href, "active": active})
    return items


def ark_context(request: Request) -> dict:
    """Starlette context processor — runs for every TemplateResponse."""
    return {
        "site_key": SITE_KEY,
        "site_title": C.SITE_TITLE,   # "Leontief"
        "site_home": SITE_HOME,
        "dpr_url": DPR_URL,
        "ecosystem": load_ecosystem(),
        "nav": _nav_for(request.url.path),
    }
