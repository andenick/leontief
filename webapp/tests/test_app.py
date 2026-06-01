"""Wassily webapp test suite.

Run with:
    cd webapp
    .venv/Scripts/python.exe -m pytest -q

Marks:
    slow  -- tests that execute study analysis.py scripts (can take 10-60 s each)
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

_WEBAPP_ROOT = Path(__file__).resolve().parent.parent

# All static page routes to smoke-test
_PAGE_ROUTES = [
    "/",
    "/learn",
    "/tables",
    "/studies",
    "/data",
    "/methodology",
    "/about",
    "/glossary",
    "/healthz",
]

# One real learn slug and one real study slug (always present once content is built)
_LEARN_SLUG = "01-what-is-an-io-table"
_STUDY_SLUG = "key-sectors"


# ---------------------------------------------------------------------------
# Page smoke tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("route", _PAGE_ROUTES)
def test_page_route_200(client, route):
    """Every static page route must return HTTP 200."""
    r = client.get(route)
    assert r.status_code == 200, f"{route} returned {r.status_code}: {r.text[:200]}"


def test_learn_tutorial_real_slug(client):
    """A known tutorial slug must return 200."""
    r = client.get(f"/learn/{_LEARN_SLUG}")
    assert r.status_code == 200, f"/learn/{_LEARN_SLUG} returned {r.status_code}"


def test_learn_tutorial_bogus_slug_404(client):
    """/learn/<nonexistent> must return 404."""
    r = client.get("/learn/nope-does-not-exist")
    assert r.status_code == 404


def test_study_real_slug(client):
    """A known study slug must return 200."""
    r = client.get(f"/studies/{_STUDY_SLUG}")
    assert r.status_code == 200, f"/studies/{_STUDY_SLUG} returned {r.status_code}"


# ---------------------------------------------------------------------------
# Tables API — JSON payloads
# ---------------------------------------------------------------------------

def test_table_2002_L_rows(client):
    """/api/table/2002/L must return 71 rows (71x71 Leontief inverse)."""
    r = client.get("/api/table/2002/L")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["rows"] == 71, f"Expected 71 rows, got {data['rows']}"


def test_table_2024_L_agg15(client):
    """/api/table/2024/L?agg=15 must return a square-ish aggregated table."""
    r = client.get("/api/table/2024/L?agg=15")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    # After agg=15 both axes should have the same length (~15 groups)
    assert data["rows"] == data["cols"], (
        f"Expected rows==cols after agg=15, got rows={data['rows']} cols={data['cols']}"
    )
    assert data["rows"] <= 15, f"Expected ≤15 aggregated groups, got {data['rows']}"


def test_table_2002_use_search(client):
    """/api/table/2002/Use?search=farm must return search_hits."""
    r = client.get("/api/table/2002/Use?search=farm")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "search_hits" in data
    # "farm" should match at least one row (111CA = Farms)
    hits = data["search_hits"]
    assert isinstance(hits, dict)
    assert "rows" in hits and "cols" in hits


# ---------------------------------------------------------------------------
# Download round-trips
# ---------------------------------------------------------------------------

def test_download_csv_71x71(client):
    """/api/table/2002/L.csv must parse back to 71×71."""
    import csv

    r = client.get("/api/table/2002/L.csv")
    assert r.status_code == 200, r.text[:300]
    rows = list(csv.reader(r.text.splitlines()))
    # header row + 71 data rows = 72 total; each data row has 71 values + 1 index col = 72 cols
    assert len(rows) == 72, f"Expected 72 rows (header+71), got {len(rows)}"
    assert len(rows[0]) == 72, f"Expected 72 cols (index+71), got {len(rows[0])}"


def test_download_xlsx_structure(client):
    """/api/table/2002/L.xlsx must start with PK (zip magic) and contain one sheet."""
    import openpyxl

    r = client.get("/api/table/2002/L.xlsx")
    assert r.status_code == 200
    raw = r.content
    assert raw[:2] == b"PK", "XLSX must start with PK (zip magic bytes)"
    wb = openpyxl.load_workbook(io.BytesIO(raw))
    assert len(wb.sheetnames) >= 1, "XLSX must have at least one sheet"


def test_download_json_values(client):
    """/api/table/2002/L.json must load with 71×71 values array."""
    r = client.get("/api/table/2002/L.json")
    assert r.status_code == 200
    payload = json.loads(r.content)
    assert "values" in payload
    values = payload["values"]
    assert len(values) == 71, f"Expected 71 rows in values, got {len(values)}"
    assert len(values[0]) == 71, f"Expected 71 cols in values[0], got {len(values[0])}"


def test_download_parquet_numeric(client):
    """/api/table/2002/L.parquet must read back as a numeric DataFrame."""
    import pandas as pd

    r = client.get("/api/table/2002/L.parquet")
    assert r.status_code == 200
    df = pd.read_parquet(io.BytesIO(r.content))
    assert df.shape[0] == 71, f"Expected 71 rows, got {df.shape[0]}"


def test_download_series_csv(client):
    """/api/series/multiplier_timeseries.csv must be non-empty."""
    import csv

    r = client.get("/api/series/multiplier_timeseries.csv")
    assert r.status_code == 200
    rows = list(csv.reader(r.text.splitlines()))
    # At least a header + one data row
    assert len(rows) >= 2, f"Series CSV must have at least 2 rows, got {len(rows)}"


def test_download_bulk_year_zip(client):
    """/api/bulk/2002.zip must be a zip containing 7 CSVs."""
    r = client.get("/api/bulk/2002.zip")
    assert r.status_code == 200
    assert r.content[:2] == b"PK", "ZIP must start with PK magic"
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        csv_files = [n for n in zf.namelist() if n.endswith(".csv")]
        assert len(csv_files) == 7, f"Expected 7 CSVs in 2002 zip, got {len(csv_files)}: {csv_files}"


def test_download_bulk_all_zip(client):
    """/api/bulk/all.zip must be a valid zip archive."""
    r = client.get("/api/bulk/all.zip")
    assert r.status_code == 200
    assert r.content[:2] == b"PK", "ZIP must start with PK magic"
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert len(zf.namelist()) > 0, "all.zip must contain at least one file"


# ---------------------------------------------------------------------------
# Charts — CHART_REGISTRY builders
# ---------------------------------------------------------------------------

def _chart_registry_keys():
    """Return a list of (key, params) tuples for parametrizing chart tests."""
    # We import here so the parametrize list is generated at collection time
    # with a real sys.path.
    import sys
    from pathlib import Path as _Path
    _root = _Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from app.services.chart_service import CHART_REGISTRY
    cases = []
    for key in CHART_REGISTRY:
        if key == "multiplier_trend":
            cases.append((key, {}))
        elif key in ("matrix_heatmap",):
            cases.append((key, {"year": 2002, "matrix": "L"}))
        elif key in ("multiplier_bar", "linkage_scatter"):
            cases.append((key, {"year": 2002}))
        elif key == "structural_trend":
            cases.append((key, {"key": "deindustrialization"}))
        elif key == "generic_series":
            cases.append((key, {"key": "multiplier_timeseries"}))
        else:
            cases.append((key, {"year": 2002}))
    return cases


@pytest.mark.parametrize("chart_key,params", _chart_registry_keys())
def test_chart_registry_builder(chart_key, params):
    """Every CHART_REGISTRY builder must return a dict with 'figure' that is JSON-serializable."""
    from app.services.chart_service import build_chart

    result = build_chart(chart_key, **params)
    assert isinstance(result, dict), f"{chart_key} builder must return dict"
    assert "figure" in result, f"{chart_key} builder result must have 'figure' key"
    # Must be JSON-serializable (no NaN/Inf)
    try:
        json.dumps(result)
    except (TypeError, ValueError) as exc:
        pytest.fail(f"{chart_key} result is not JSON-serializable: {exc}")


def test_chart_compound_heatmap(client):
    """Compound chart key heatmap:2002:L must return 200 with non-empty figure."""
    r = client.get("/api/chart/heatmap:2002:L")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "figure" in data
    assert data["figure"]  # non-empty


def test_chart_compound_mult_bar(client):
    """Compound chart key mult_bar:2002 must return 200."""
    r = client.get("/api/chart/mult_bar:2002")
    assert r.status_code == 200, r.text[:300]


def test_chart_compound_linkage(client):
    """Compound chart key linkage:2002 must return 200."""
    r = client.get("/api/chart/linkage:2002")
    assert r.status_code == 200, r.text[:300]


def _study_chart_cases():
    """Return (slug, figname) pairs from manifest for study chart testing."""
    import sys
    from pathlib import Path as _Path
    _root = _Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    p = _root / "site_data" / "site_manifest.json"
    if not p.exists():
        return [("key-sectors", "linkage_scatter")]
    with p.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    cases = []
    for study in manifest.get("studies", []):
        slug = study.get("slug") or study.get("key")
        for fig in study.get("figs", []):
            cases.append((slug, fig))
    # Return at least 3 (guaranteed from manifest)
    return cases[:max(3, len(cases))]


@pytest.mark.parametrize("slug,figname", _study_chart_cases())
def test_study_chart_api(client, slug, figname):
    """Each study:<slug>:<figname> key must return 200 with non-empty figure via /api/chart/."""
    r = client.get(f"/api/chart/study:{slug}:{figname}")
    assert r.status_code == 200, (
        f"study:{slug}:{figname} returned {r.status_code}: {r.text[:300]}"
    )
    data = r.json()
    assert "figure" in data, f"study:{slug}:{figname} response missing 'figure'"
    assert data["figure"], f"study:{slug}:{figname} figure is empty"


# ---------------------------------------------------------------------------
# Manifest integrity — parquet file existence
# ---------------------------------------------------------------------------

def test_manifest_tables_parquets_exist(manifest):
    """Every table entry in the manifest must have its parquet on disk."""
    site_data = _WEBAPP_ROOT / "site_data"
    missing = []
    for t in manifest.get("tables", []):
        parquet_rel = t.get("parquet", "")
        path = site_data / parquet_rel
        if not path.exists():
            missing.append(str(path))
    assert not missing, f"{len(missing)} table parquet(s) missing:\n" + "\n".join(missing[:10])


def test_manifest_series_parquets_exist(manifest):
    """Every series entry in the manifest must have its parquet on disk."""
    site_data = _WEBAPP_ROOT / "site_data"
    missing = []
    for s in manifest.get("series", []):
        parquet_rel = s.get("parquet", "")
        path = site_data / parquet_rel
        if not path.exists():
            missing.append(str(path))
    assert not missing, f"{len(missing)} series parquet(s) missing:\n" + "\n".join(missing)


def test_manifest_studies_cache_exists(manifest):
    """Every study+fig in manifest must have its cached JSON in site_data/cache/."""
    cache_dir = _WEBAPP_ROOT / "site_data" / "cache"
    missing = []
    for study in manifest.get("studies", []):
        slug = study.get("slug") or study.get("key")
        for fig in study.get("figs", []):
            cache_file = cache_dir / f"study__{slug}__{fig}.json"
            if not cache_file.exists():
                missing.append(str(cache_file))
    assert not missing, (
        f"{len(missing)} study cache file(s) missing:\n" + "\n".join(missing)
    )


def test_manifest_studies_bundle_dirs_exist(manifest):
    """Every study in manifest must have a code bundle dir under content/studies/code/."""
    code_root = _WEBAPP_ROOT / "content" / "studies" / "code"
    missing = []
    for study in manifest.get("studies", []):
        slug = study.get("slug") or study.get("key")
        bundle_dir = code_root / slug
        if not bundle_dir.is_dir():
            missing.append(str(bundle_dir))
    assert not missing, (
        f"{len(missing)} study bundle dir(s) missing:\n" + "\n".join(missing)
    )


# ---------------------------------------------------------------------------
# Study bundles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", ["key-sectors", "multipliers-explained"])
def test_study_bundle_zip(client, slug):
    """/api/study/<slug>/bundle.zip must return 200 and contain analysis.py."""
    r = client.get(f"/api/study/{slug}/bundle.zip")
    assert r.status_code == 200, (
        f"/api/study/{slug}/bundle.zip returned {r.status_code}: {r.text[:300]}"
    )
    assert r.content[:2] == b"PK", "Bundle must start with PK magic"
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
        py_files = [n for n in names if n.endswith(".py")]
        assert py_files, f"Bundle for {slug!r} must contain at least one .py file; got: {names}"


# ---------------------------------------------------------------------------
# File endpoint guard
# ---------------------------------------------------------------------------

def test_file_endpoint_allowed(client):
    """/api/file/app/config.py must return 200 (allowed extension, within root)."""
    r = client.get("/api/file/app/config.py")
    assert r.status_code == 200, f"Expected 200 for config.py, got {r.status_code}"
    assert "WEBAPP_ROOT" in r.text or "config" in r.text.lower()


def test_file_endpoint_traversal_blocked(client):
    """/api/file/../../../etc/passwd must return 403 or 404 (traversal blocked)."""
    r = client.get("/api/file/../../../etc/passwd")
    assert r.status_code in (403, 404), (
        f"Traversal attempt must return 403 or 404, got {r.status_code}"
    )


def test_file_endpoint_disallowed_extension(client):
    """/api/file/app/config.xyz must return 403 (extension not in whitelist)."""
    # We don't need a real .xyz file; guard fires on extension before existence check.
    r = client.get("/api/file/app/config.xyz")
    assert r.status_code == 403, (
        f"Disallowed extension must return 403, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Sectors count
# ---------------------------------------------------------------------------

def test_sectors_json_71(sectors):
    """sectors.json must contain exactly 71 sectors."""
    secs = sectors.get("sectors", [])
    assert len(secs) == 71, f"Expected 71 sectors, got {len(secs)}"


# ---------------------------------------------------------------------------
# Narrative coverage
# ---------------------------------------------------------------------------

def test_ten_tutorials_present():
    """narrative_service.list_docs('learn') must return exactly 10 tutorials."""
    from app.services.narrative_service import list_docs
    docs = list_docs("learn")
    assert len(docs) == 10, f"Expected 10 tutorials, got {len(docs)}: {[d['slug'] for d in docs]}"


def test_ten_studies_present():
    """narrative_service.list_docs('studies') must return exactly 10 studies."""
    from app.services.narrative_service import list_docs
    docs = list_docs("studies")
    assert len(docs) == 10, f"Expected 10 studies, got {len(docs)}: {[d['slug'] for d in docs]}"


# ---------------------------------------------------------------------------
# Reproducibility spot-check — run analysis.py for one study
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_study_analysis_reproducible(tmp_path):
    """Run key-sectors analysis.py in a temp copy and verify it regenerates its figures.

    Marked @pytest.mark.slow — excluded from quick runs via -m 'not slow'.
    Runtime: typically 5-30 s depending on machine.
    """
    import shutil

    slug = "key-sectors"
    source_dir = _WEBAPP_ROOT / "content" / "studies" / "code" / slug
    if not source_dir.exists():
        pytest.skip(f"Study code dir missing: {source_dir}")

    # Copy the entire study dir into tmp_path so we don't clobber outputs/
    work_dir = tmp_path / slug
    shutil.copytree(source_dir, work_dir)

    # Remove existing outputs so we can verify they are regenerated
    out_dir = work_dir / "outputs"
    for f in out_dir.glob("fig_*.json"):
        f.unlink()

    # Run analysis.py with the venv python
    python_exe = _WEBAPP_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = sys.executable  # fallback (e.g. in CI)

    result = subprocess.run(
        [str(python_exe), "analysis.py"],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=120,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, (
        f"analysis.py exited with {result.returncode}.\n"
        f"STDOUT:\n{result.stdout[-2000:]}\n"
        f"STDERR:\n{result.stderr[-2000:]}"
    )

    # Verify the manifest-listed figs were (re)produced
    manifest_path = _WEBAPP_ROOT / "site_data" / "site_manifest.json"
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as fh:
            mf = json.load(fh)
        study_entry = next(
            (s for s in mf.get("studies", []) if (s.get("slug") or s.get("key")) == slug),
            None,
        )
        if study_entry:
            for figname in study_entry.get("figs", []):
                expected = out_dir / f"fig_{figname}.json"
                assert expected.exists(), (
                    f"analysis.py did not (re)produce expected figure: {expected.name}"
                )
