"""Selfcheck gate for the Leontief I-O website.

Run with the webapp venv python:
    .venv/Scripts/python.exe data_pipeline/selfcheck.py

Checks critical invariants and exits nonzero on any failure (for CI/deploy
gating). Prints a checklist with pass/fail markers and a final summary line.

Exit codes:
    0 — all checks passed (SELFCHECK PASS)
    1 — one or more checks failed (SELFCHECK FAIL)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure webapp root is importable
# ---------------------------------------------------------------------------
_WEBAPP_ROOT = Path(__file__).resolve().parent.parent
if str(_WEBAPP_ROOT) not in sys.path:
    sys.path.insert(0, str(_WEBAPP_ROOT))

# ---------------------------------------------------------------------------
# Checklist state
# ---------------------------------------------------------------------------
_results: list[tuple[bool, str]] = []


def _check(ok: bool, label: str, detail: str = "") -> bool:
    """Record a check result and print it."""
    mark = "OK" if ok else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"\n         {detail}"
    print(line)
    _results.append((ok, label))
    return ok


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_present() -> bool:
    p = _WEBAPP_ROOT / "site_data" / "site_manifest.json"
    return _check(p.exists(), "site_manifest.json present", str(p) if not p.exists() else "")


def check_parquets_exist(manifest: dict) -> bool:
    site_data = _WEBAPP_ROOT / "site_data"
    missing = []
    for t in manifest.get("tables", []):
        path = site_data / t.get("parquet", "")
        if not path.exists():
            missing.append(t.get("parquet", ""))
    for s in manifest.get("series", []):
        path = site_data / s.get("parquet", "")
        if not path.exists():
            missing.append(s.get("parquet", ""))
    ok = len(missing) == 0
    detail = f"{len(missing)} missing" + (f": {missing[:3]}" if missing else "")
    return _check(ok, "All referenced parquets exist", "" if ok else detail)


def check_sectors_json() -> bool:
    p = _WEBAPP_ROOT / "site_data" / "sectors.json"
    if not p.exists():
        return _check(False, "sectors.json has 71 sectors", "sectors.json not found")
    with p.open(encoding="utf-8") as fh:
        data = json.load(fh)
    n = len(data.get("sectors", []))
    ok = n == 71
    return _check(ok, "sectors.json has 71 sectors", f"got {n}" if not ok else "")


def check_app_imports() -> bool:
    try:
        from app.main import create_app  # noqa: F401
        return _check(True, "app imports and create_app() callable")
    except Exception as exc:
        return _check(False, "app imports and create_app() callable", str(exc))


def check_app_boots() -> bool:
    try:
        from app.main import create_app
        app = create_app()
        return _check(bool(app), "create_app() returns a FastAPI instance")
    except Exception as exc:
        return _check(False, "create_app() returns a FastAPI instance", str(exc))


def _make_client() -> Any:
    from fastapi.testclient import TestClient
    from app.main import create_app
    app = create_app()
    return TestClient(app)


def check_routes(client: Any) -> bool:
    routes = ["/healthz", "/", "/tables", "/data"]
    fails = []
    for route in routes:
        try:
            r = client.get(route)
            if r.status_code != 200:
                fails.append(f"{route} -> {r.status_code}")
        except Exception as exc:
            fails.append(f"{route} -> ERROR: {exc}")
    ok = len(fails) == 0
    return _check(ok, f"Page routes all 200 ({', '.join(routes)})",
                  "; ".join(fails) if fails else "")


def check_table_api(client: Any) -> bool:
    try:
        r = client.get("/api/table/2002/L")
        ok = r.status_code == 200 and r.json().get("rows") == 71
        detail = "" if ok else f"status={r.status_code}, rows={r.json().get('rows')}"
        return _check(ok, "/api/table/2002/L returns 200 with 71 rows", detail)
    except Exception as exc:
        return _check(False, "/api/table/2002/L returns 200 with 71 rows", str(exc))


def check_study_chart(client: Any, manifest: dict) -> bool:
    """Hit the first available study chart via the API."""
    try:
        studies = manifest.get("studies", [])
        if not studies:
            return _check(False, "Study chart API check", "No studies in manifest")
        study = studies[0]
        slug = study.get("slug") or study.get("key")
        figs = study.get("figs", [])
        if not figs:
            return _check(False, "Study chart API check", f"Study {slug!r} has no figs")
        fig = figs[0]
        r = client.get(f"/api/chart/study:{slug}:{fig}")
        ok = r.status_code == 200 and bool(r.json().get("figure"))
        detail = "" if ok else f"status={r.status_code}: {r.text[:200]}"
        return _check(ok, f"Study chart API /api/chart/study:{slug}:{fig} -> 200", detail)
    except Exception as exc:
        return _check(False, "Study chart API check", str(exc))


def check_tutorials_count() -> bool:
    try:
        from app.services.narrative_service import list_docs
        docs = list_docs("learn")
        ok = len(docs) >= 10
        return _check(ok, f"10 tutorials present (found {len(docs)})",
                      "" if ok else f"Need 10, got {len(docs)}")
    except Exception as exc:
        return _check(False, "10 tutorials present", str(exc))


def check_studies_count() -> bool:
    try:
        from app.services.narrative_service import list_docs
        docs = list_docs("studies")
        ok = len(docs) >= 10
        return _check(ok, f"10 studies present (found {len(docs)})",
                      "" if ok else f"Need 10, got {len(docs)}")
    except Exception as exc:
        return _check(False, "10 studies present", str(exc))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("Leontief Self-Check Gate")
    print("=" * 60)

    # 1. Manifest present
    manifest_ok = check_manifest_present()
    manifest: dict = {}
    if manifest_ok:
        with (_WEBAPP_ROOT / "site_data" / "site_manifest.json").open(encoding="utf-8") as fh:
            manifest = json.load(fh)

    # 2. Parquets exist (requires manifest)
    if manifest_ok:
        check_parquets_exist(manifest)
    else:
        _check(False, "All referenced parquets exist", "skipped — manifest missing")

    # 3. sectors.json has 71 sectors
    check_sectors_json()

    # 4. App imports
    imports_ok = check_app_imports()

    # 5. App boots
    boots_ok = imports_ok and check_app_boots()

    # 6-9. HTTP checks (requires booted app)
    client = None
    if boots_ok:
        try:
            client = _make_client()
        except Exception as exc:
            _check(False, "TestClient creation", str(exc))

    if client is not None:
        check_routes(client)
        check_table_api(client)
        if manifest_ok:
            check_study_chart(client, manifest)
        else:
            _check(False, "Study chart API check", "skipped — manifest missing")
    else:
        _check(False, "Page routes all 200", "skipped — client unavailable")
        _check(False, "/api/table/2002/L returns 200 with 71 rows", "skipped — client unavailable")
        _check(False, "Study chart API check", "skipped — client unavailable")

    # 10. Tutorial count
    if imports_ok:
        check_tutorials_count()
        check_studies_count()
    else:
        _check(False, "10 tutorials present", "skipped — app not importable")
        _check(False, "10 studies present", "skipped — app not importable")

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print()
    print("=" * 60)
    total = len(_results)
    passed = sum(1 for ok, _ in _results if ok)
    failed = total - passed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print()
    if failed == 0:
        print("SELFCHECK PASS")
        return 0
    else:
        print("SELFCHECK FAIL")
        failed_labels = [lbl for ok, lbl in _results if not ok]
        for lbl in failed_labels:
            print(f"  FAILED: {lbl}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
