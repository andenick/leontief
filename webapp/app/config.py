"""Central configuration for the Leontief website.

Resolves project paths and site constants. All paths are computed relative to
this file so the app works regardless of where the venv lives.

Path hierarchy:
    webapp/app/config.py  ->  webapp/  ->  Leontief/  ->  Projects/  ->  Arcanum/
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------

# webapp/app/config.py -> webapp/ -> Leontief/
WEBAPP_ROOT: Path = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Path = WEBAPP_ROOT.parent           # …/Leontief/
ARCANUM_ROOT: Path = PROJECT_ROOT.parent.parent   # …/Arcanum/  (Leontief -> Projects -> Arcanum)

# ---------------------------------------------------------------------------
# Project source directories (read-only; populated outside webapp)
# ---------------------------------------------------------------------------

TECHNICAL: Path = PROJECT_ROOT / "Technical"
PROCESSED_DIR: Path = TECHNICAL / "data" / "processed" / "annual_71"
OUTPUTS_DATA: Path = PROJECT_ROOT / "Outputs" / "Data"
BUILD_STATE: Path = TECHNICAL / "website_build" / "build_state.json"

# ---------------------------------------------------------------------------
# Webapp runtime directories (generated; gitignored)
# ---------------------------------------------------------------------------

SITE_DATA: Path = WEBAPP_ROOT / "site_data"
CACHE_DIR: Path = SITE_DATA / "cache"
DOWNLOADS_DIR: Path = SITE_DATA / "downloads"

# ---------------------------------------------------------------------------
# Content + template + static directories
# ---------------------------------------------------------------------------

CONTENT_DIR: Path = WEBAPP_ROOT / "content"
TEMPLATES_DIR: Path = WEBAPP_ROOT / "app" / "templates"
STATIC_DIR: Path = WEBAPP_ROOT / "app" / "static"

# ---------------------------------------------------------------------------
# Site identity
# ---------------------------------------------------------------------------

SITE_TITLE: str = "Leontief"
SITE_TAGLINE: str = "U.S. Input-Output Tables, 1997–2024"
SITE_HOST: str = os.environ.get("LEONTIEF_HOST", "leontief.heterodata.org")

# Public source repository (Code mode "View on GitHub" button).
GITHUB_URL: str = os.environ.get("LEONTIEF_GITHUB_URL", "https://github.com/andenick/leontief")

# Pinned commit ref for replication-code permalinks (STUDY_PAGE_STANDARD requires a
# pinned SHA, not a branch). Set LEONTIEF_GITHUB_PIN to the release commit at deploy
# time; defaults to "main" only as a development fallback.
GITHUB_PIN: str = os.environ.get("LEONTIEF_GITHUB_PIN", "main")

# BEA data scope constants
BEA_YEARS: tuple[int, ...] = tuple(range(1997, 2025))   # 1997–2024 inclusive
SECTOR_COUNT: int = 71
MATRIX_KEYS: tuple[str, ...] = ("Use", "Supply", "A", "A_square", "L", "VA", "FD")


# ---------------------------------------------------------------------------
# Manifest / sector registry helpers
# ---------------------------------------------------------------------------

def get_manifest_path() -> Path:
    """Return the path to site_manifest.json (may not exist before build_cache.py runs)."""
    return SITE_DATA / "site_manifest.json"


def get_sectors_path() -> Path:
    """Return the path to sectors.json (may not exist before build_sectors.py runs)."""
    return SITE_DATA / "sectors.json"


# ---------------------------------------------------------------------------
# Startup helper
# ---------------------------------------------------------------------------

def ensure_dirs() -> None:
    """Create runtime directories that must exist at startup."""
    for d in (SITE_DATA, CACHE_DIR, DOWNLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)
