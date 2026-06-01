# Wassily (Leontief) website — production image
#
# DESIGN NOTES
# ─────────────
# * base image: python:3.12-slim (same as Gerhard)
# * vendor.py runs at build time (needs network); it downloads KaTeX from
#   jsDelivr and copies plotly.min.js out of the installed plotly wheel.
#   If you prefer fully offline builds, run vendor.py on the dev machine
#   first, then swap the RUN line below for:
#       RUN echo "vendor assets already present in image"
#   (vendor output lives in webapp/app/static/vendor/ and is copied in by
#   the COPY app/ step above).
# * build_cache.py / build_sectors.py are NOT run here — they read source
#   pkl data from Technical/data/ which lives outside the container.
#   PRE-BUILD on the dev machine before `docker build`:
#       python data_pipeline/build_sectors.py
#       python data_pipeline/build_cache.py
#   Then `docker build` copies the already-populated site_data/ into the image.
# * PYTHONPATH=/app/webapp so `from app import config` resolves correctly.
# * Gunicorn + UvicornWorker; 2 workers sufficient for a single mini-PC.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/webapp

WORKDIR /app

# ── 1. Install Python dependencies (pinned; from requirements.txt) ──────────
COPY webapp/requirements.txt /app/webapp/requirements.txt
RUN pip install --no-cache-dir -r /app/webapp/requirements.txt

# ── 2. Copy application source ───────────────────────────────────────────────
# app/      — FastAPI app + routers + templates + static
# content/  — Markdown/JSON content files read at runtime
# site_data/ — PRE-BUILT on dev machine (sectors.json, site_manifest.json,
#              cache/, downloads/); must exist before docker build.
COPY webapp/app      /app/webapp/app
COPY webapp/content  /app/webapp/content
COPY webapp/site_data /app/webapp/site_data

# ── 3. Copy data_pipeline (needed for vendor.py at build time) ───────────────
COPY webapp/data_pipeline /app/webapp/data_pipeline

# ── 4. Vendor front-end assets at build time (requires network) ──────────────
# vendors: plotly.min.js (from installed wheel), KaTeX (jsDelivr), pygments.css
RUN python /app/webapp/data_pipeline/vendor.py || true

# ── 5. Expose and run ────────────────────────────────────────────────────────
EXPOSE 8080

CMD ["gunicorn", "app.main:app", \
     "--chdir", "/app/webapp", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "2", \
     "-b", "0.0.0.0:8080", \
     "--timeout", "120"]
