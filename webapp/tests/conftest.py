"""pytest configuration and shared fixtures for Wassily webapp tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure webapp root is on sys.path so `app.*` imports resolve regardless
# of where pytest is invoked from.
_WEBAPP_ROOT = Path(__file__).resolve().parent.parent
if str(_WEBAPP_ROOT) not in sys.path:
    sys.path.insert(0, str(_WEBAPP_ROOT))


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous TestClient wrapping the FastAPI app.

    Uses session scope so the startup event (manifest load) fires once for all
    tests; avoids repeated startup overhead.
    """
    from app.main import create_app

    app = create_app()
    # TestClient's context manager triggers startup/shutdown events.
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def manifest() -> dict:
    """Loaded site_manifest.json dict.

    Skips the test gracefully if the manifest has not been built yet
    (build_cache.py has not been run).
    """
    p = _WEBAPP_ROOT / "site_data" / "site_manifest.json"
    if not p.exists():
        pytest.skip("site_manifest.json not found — run data_pipeline/build_cache.py")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def sectors() -> dict:
    """Loaded sectors.json dict.

    Skips the test gracefully if sectors.json has not been built yet.
    """
    p = _WEBAPP_ROOT / "site_data" / "sectors.json"
    if not p.exists():
        pytest.skip("sectors.json not found — run data_pipeline/build_sectors.py")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)
