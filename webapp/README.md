# Wassily — U.S. Input-Output Tables, 1997–2024

**Wassily** is a free, public website that publishes all 28 annual U.S. Bureau of Economic Analysis (BEA) input-output tables (1997–2024, 71-sector detail) as machine-readable downloads, alongside an educational Learn track of 10 progressive tutorials and 10 fully reproducible empirical studies.

Live site: `leontief.nickanderson.us` (go-live gated on Carson hardware — see `deploy/README.md`).

---

## What the site provides

- **28 annual I-O tables (1997–2024), 71-sector detail** — Use, Supply, technical coefficient matrix A, square A, Leontief inverse L, Value Added, and Final Demand; downloadable as CSV / XLSX / JSON / Parquet for every year.
- **Derived series** — multiplier time-series, employment multipliers, labor share, and more; bulk ZIP downloads.
- **Learn track** — 10 ordered tutorials covering I-O concepts from first principles through price-value theory, rendered with KaTeX math and syntax-highlighted Python code.
- **Studies** — 10 reproducible empirical studies (key sectors, deindustrialization, COVID structural shift, fiscal multipliers, profit-rate trends, …), each with a downloadable code+data bundle.
- **Interactive heatmaps and charts** — Plotly-powered, rendered server-side and hydrated in-browser.
- **No login, no paywall** — all data and code is freely accessible.

### A note on matrix dimensions

The canonical "Use" matrix (71 × 71) is commodity-by-industry. The derived technical-coefficient matrix **A** is 70 × 71 (one commodity row is dropped during BEA's reconciliation step); **A_square** pads it to a full 71 × 71 for the Leontief inverse computation. The Leontief inverse **L** is therefore 71 × 71. This is an intentional methodological choice, documented in `/methodology`.

---

## Architecture

```
webapp/
  app/
    main.py           # FastAPI app factory (lifespan handler, static mount, router wiring)
    config.py         # All path constants and BEA scope constants
    routers/
      pages.py        # HTML routes (Jinja2 server-side rendering)
      api.py          # JSON + download API (/api/chart, /api/table, /api/series, /api/bulk, …)
    services/
      narrative_service.py   # Markdown → HTML (frontmatter, KaTeX, Pygments, chart/table directives)
      chart_service.py       # Plotly figure builders; CHART_REGISTRY dispatch
      table_service.py       # matrix_payload — aggregation, filtering, JSON shape for grid/heatmap
      data_service.py        # Parquet reads, manifest queries, sector-name map
      download_service.py    # In-memory export: CSV/XLSX/JSON/Parquet/ZIP
    templates/         # Jinja2 HTML templates (base.html, home, tutorial, study, catalog, …)
    static/
      css/             # site.css, tables.css
      js/              # app.js (chart hydration, copy buttons), tables.js (grid)
      vendor/          # plotly.min.js, KaTeX (vendored; no npm/Node required)
  content/
    learn/             # 01-*.md … 10-*.md tutorial Markdown files
    studies/           # one .md per study (narrative + {{chart:…}} directives)
    methodology.md, about.md, glossary.md   # static narrative pages
    citations.json     # citation metadata for [cite:KEY] directives
  data_pipeline/
    vendor.py          # Download/vendor front-end assets (plotly, KaTeX, Pygments CSS)
    build_sectors.py   # Build site_data/sectors.json from BEA sector list
    build_cache.py     # Build site_data/site_manifest.json + cache/*.parquet from source pkl files
    run_studies.py     # Pre-compute study chart JSON caches
    selfcheck.py       # Data integrity self-check (run after build_cache.py)
  site_data/           # Generated at build time; gitignored
    sectors.json
    site_manifest.json
    cache/             # Per-year parquet files + study chart JSON
  tests/               # pytest suite (conftest + test_app.py)
  deploy/              # Docker Compose, Caddyfile, systemd unit, nginx.conf, deploy README
  requirements.txt
```

**Stack:** FastAPI + Jinja2 (server-rendered HTML) + Plotly (JSON figures, browser-hydrated) + Parquet (columnar matrix cache via pandas/pyarrow). No npm, no Node, no build step for front-end assets.

---

## How to run locally

All commands assume you are in `webapp/`.

### 1. Create and activate the virtual environment

```powershell
# Windows
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Pre-build pipeline (already done — site_data/ is populated)

These scripts generate `site_data/` from source data. They have already been run; you do not need to re-run them unless source data changes.

```bash
python data_pipeline/vendor.py          # vendor front-end assets
python data_pipeline/build_sectors.py   # build sectors.json
python data_pipeline/build_cache.py     # build site_manifest.json + parquet cache
python data_pipeline/run_studies.py     # pre-compute study chart JSON
```

### 3. Start the dev server

```bash
python -m uvicorn app.main:app --app-dir . --port 8080
```

Then open `http://127.0.0.1:8080`.

For auto-reload during development:

```bash
python -m uvicorn app.main:app --app-dir . --port 8080 --reload
```

---

## How to test

```bash
# Unit + integration tests (uses TestClient, no live server needed)
pytest -q

# Data integrity self-check (validates parquet files and manifest)
python data_pipeline/selfcheck.py
```

---

## How to deploy

See `deploy/README.md` for the full production runbook. Summary:

- **Target:** Carson mini PC, `leontief.nickanderson.us`, Cloudflare Tunnel (no open ports)
- **Stack:** gunicorn/uvicorn behind Caddy 2, Dockerized
- **Go-live gate:** Carson hardware not yet online as of 2026-05-31 — runbook is complete and ready to execute
- **No refresh service:** BEA I-O tables are published annually; redeploy once per vintage

```bash
# From the Leontief/ project root (one level above webapp/)
docker compose -f webapp/deploy/docker-compose.yml up -d --build
```

---

## Data provenance

All I-O data sourced from the U.S. Bureau of Economic Analysis (BEA) annual input-output accounts. Source files: `Technical/data/processed/annual_71/year_{1997..2024}.pkl` (built from raw BEA downloads). BEA data is U.S. government public domain.

Site content (tutorials, studies, methodology text) is intended for release under **CC-BY** (attribution required). Study code bundles are intended for release under **MIT**.

---

## Directory map (top-level)

| Path | Contents |
|------|---------|
| `app/` | FastAPI application (routes, services, templates, static assets) |
| `content/` | Markdown source for all narrative pages |
| `data_pipeline/` | Build scripts (run once; output goes to `site_data/`) |
| `site_data/` | Generated cache — gitignored; must be built before serving |
| `tests/` | pytest suite |
| `deploy/` | Production deployment files (Docker, Caddy, systemd, Cloudflare) |
| `requirements.txt` | Python dependencies |
