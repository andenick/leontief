# Leontief — U.S. Input-Output Tables Analysis

**Leontief** is an open analysis toolkit and website for U.S. and international
input-output (I-O) accounts. It collects every annual U.S. Bureau of Economic
Analysis (BEA) I-O table from **1997 through 2024** at the BEA Summary 71-sector
level, computes the standard derived matrices, and publishes them as
machine-readable downloads alongside tutorials and reproducible empirical studies.

Named after **Wassily Leontief** (1906–1999), Nobel laureate and pioneer of
input-output analysis.

> **This is a code-only repository.** The raw BEA inputs and generated outputs are
> not committed. The collectors below rebuild the source data from the public BEA
> API; the website's `site_data/` cache is built from those outputs.

---

## What it does

- **Collects** all 28 annual U.S. BEA I-O tables (1997–2024) plus GDP-by-industry
  and satellite accounts (trade, capital, energy) via the BEA API.
- **Derives**, for each year, seven matrices: the raw **Use** and **Supply**
  tables, the direct-requirements matrix **A**, a squared variant **A_square**,
  the **Leontief inverse** L = (I − A)⁻¹, the **value-added** rows, and the
  **final-demand** columns.
- **Validates** derived matrices against BEA's own published benchmark figures.
- **Publishes** everything through a FastAPI website (`webapp/`) with downloads in
  CSV / XLSX / JSON / Parquet, a 10-tutorial Learn track, and 10 reproducible studies.

---

## Repository layout

```
.
├── Technical/          # Data construction pipeline (run to rebuild source data)
│   ├── src/            # BEA collectors, parsers, I-O analysis, integration modules
│   ├── scripts/        # One-off analysis / comparison / download scripts
│   ├── apps/           # Streamlit exploration platform (leontief platform)
│   ├── docs/           # LaTeX report templates
│   └── research/       # Research notes
├── webapp/             # FastAPI website (see webapp/README.md for the full guide)
├── requirements.txt    # Top-level Python dependencies
└── README.md
```

The website (`webapp/`) is the polished, public-facing surface and has its own
detailed guide: **[`webapp/README.md`](webapp/README.md)**.

---

## Quick start

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/andenick/leontief.git
cd leontief

python -m venv .venv
# Windows:        .venv\Scripts\Activate
# Linux / macOS:  source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment (bring your own BEA key)

The data collectors read configuration from environment variables. Copy
`.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `BEA_API_KEY` | **Required to rebuild data.** A free BEA API key — register at <https://apps.bea.gov/API/signup/>. |
| `DATA_ROOT`   | Optional. Root directory the analysis scripts read/write under (defaults to the current directory). Point it at where you keep the raw/processed data tree. |

No key is needed merely to **serve** the website from a pre-built cache — see
`webapp/README.md`.

### 3. Rebuild the source data (optional)

```bash
export BEA_API_KEY=your-free-key-here      # PowerShell: $env:BEA_API_KEY="..."
export DATA_ROOT=/path/to/data             # PowerShell: $env:DATA_ROOT="..."

python "Technical/src/bea_api_collector.py"
# then the parsing / analysis scripts under Technical/src and Technical/scripts
```

### 4. Run the website

See **[`webapp/README.md`](webapp/README.md)** for the full build-and-serve guide.
In short, from `webapp/`:

```bash
pip install -r requirements.txt
python data_pipeline/build_sectors.py
python data_pipeline/build_cache.py
python -m uvicorn app.main:app --app-dir . --port 8080
```

---

## About the matrix dimensions

The canonical Use matrix is 71 × 71 (commodity-by-industry). The derived
technical-coefficient matrix **A** is non-square (one commodity row is dropped
during BEA's reconciliation); **A_square** restores a full 71 × 71 form so the
Leontief inverse **L** = (I − A)⁻¹ can be computed. This is an intentional
methodological choice, documented on the website's `/methodology` page.

---

## Data provenance & license

All I-O data is sourced from the U.S. Bureau of Economic Analysis (BEA) annual
input-output accounts, which are U.S. government public domain. The derived
matrices, documentation, and site content are intended for release under
**CC BY 4.0** (attribution required); study code bundles under **MIT**.

---

## About Wassily Leontief

Wassily Leontief developed input-output analysis to describe how the sectors of an
economy depend on one another. His framework turns the structure of production,
consumption, and trade into something measurable. This project continues that work
by making the full modern U.S. I-O series openly available and fully reproducible.
