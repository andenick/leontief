#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_bundles.py -- build the Code-&-Data-First download bundles for Leontief.

Produces, under ``webapp/site_data/downloads/``:
  * ``leontief_all.zip``  + ``BUNDLE_MANIFEST.csv`` -- the per-table I-O DATA
    bundle (CSV + XLSX + Parquet for all 196 matrices + 12 series), with a
    generated LICENSE (CC-BY-4.0), data_dictionary.csv, PROVENANCE.csv and
    README.md. Built reproducibly via the Arcanum Site Kit make_bundles.py tool.
  * ``leontief_code.zip`` -- the matrix-build + study-analysis CODE bundle
    (data_pipeline/build_cache.py + every study's analysis.py/.ipynb/README/
    requirements), with a top-level README and an MIT LICENSE.

Run locally BEFORE deploy; the zips ship inside the image (Dockerfile COPYs
site_data/). The Data triad leg serves leontief_all.zip at /api/bulk/all.zip;
the Code leg serves leontief_code.zip at /api/code/bundle.zip.

Usage:  python data_pipeline/build_bundles.py
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

WEBAPP = Path(__file__).resolve().parent.parent          # …/leontief/webapp
SITE_DATA = WEBAPP / "site_data"
CACHE = SITE_DATA / "cache"
CONTENT = WEBAPP / "content"
DOWNLOADS = SITE_DATA / "downloads"
DATA_PIPELINE = WEBAPP / "data_pipeline"

# Arcanum Site Kit make_bundles.py (reproducible-zip + manifest tool)
# WEBAPP = …/deploy/leontief/webapp -> parents[1] = …/deploy
_KIT_MAKE_BUNDLES = (WEBAPP.parents[1] / "_shared" / "arcanum-site-kit" / "v1"
                     / "tools" / "make_bundles.py")

CC_BY_4 = """Creative Commons Attribution 4.0 International (CC BY 4.0)

The Leontief input-output DATA in this bundle is released under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt
it for any purpose, provided you give appropriate credit.

Attribution:
  Anderson, N. (2026). Leontief: U.S. Input-Output Tables, 1997-2024.
  https://leontief.heterodata.org.

The underlying figures are derived from the U.S. Bureau of Economic Analysis
(BEA) Input-Output Accounts, which are in the public domain as a work of the
United States federal government. This bundle is a reconstruction for research
and education; for authoritative figures defer to bea.gov.
"""

MIT = """MIT License

Copyright (c) 2026 Nick Anderson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

MATRIX_DEFS = {
    "Use":      ("millions of current USD", "Raw BEA Use table (commodity x industry intermediate use + final demand)"),
    "Supply":   ("millions of current USD", "Raw BEA Supply/Make table (commodity x industry production)"),
    "A":        ("dimensionless coefficient", "Direct-requirements coefficients A = Z/q (non-square 70x71)"),
    "A_square": ("dimensionless coefficient", "Direct-requirements coefficients squared to the row-col intersection"),
    "L":        ("dimensionless coefficient", "Total-requirements / Leontief inverse L = (I - A)^-1 (71x71)"),
    "VA":       ("millions of current USD", "Value-added rows (compensation, taxes, gross operating surplus, total)"),
    "FD":       ("millions of current USD", "Final-demand columns (PCE, investment, government, exports)"),
}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _read_matrix_labeled(parquet: Path) -> pd.DataFrame:
    df = pd.read_parquet(parquet)
    if "__index__" in df.columns:
        df = df.set_index("__index__")
        df.index.name = None
    return df


def build_data_bundle(stage: Path) -> Path:
    manifest = _load_json(SITE_DATA / "site_manifest.json")
    sectors = _load_json(SITE_DATA / "sectors.json")

    tables_dir = stage / "tables"
    series_dir = stage / "series"
    tables_dir.mkdir(parents=True, exist_ok=True)
    series_dir.mkdir(parents=True, exist_ok=True)

    files: list[dict] = []

    # --- matrices: CSV + XLSX + Parquet per (year, matrix) ---
    n_mat = 0
    for t in manifest.get("tables", []):
        key = t["key"]                      # e.g. 1997__Use
        parquet = CACHE / f"{key}.parquet"
        if not parquet.exists():
            continue
        df = _read_matrix_labeled(parquet)
        base = tables_dir / key
        df.to_csv(base.with_suffix(".csv"), index=True)
        with pd.ExcelWriter(base.with_suffix(".xlsx"), engine="openpyxl") as w:
            df.to_excel(w, sheet_name=t["matrix"][:31], index=True)
        df.to_parquet(base.with_suffix(".parquet"), index=True)
        for ext in ("csv", "xlsx", "parquet"):
            files.append({"src": str(base.with_suffix("." + ext)),
                          "arcname": f"tables/{key}.{ext}"})
        n_mat += 1

    # --- series: CSV + Parquet per key ---
    n_ser = 0
    for s in manifest.get("series", []):
        key = s["key"]
        parquet = CACHE / f"{key}.parquet"
        if not parquet.exists():
            continue
        df = pd.read_parquet(parquet)
        base = series_dir / key
        df.to_csv(base.with_suffix(".csv"), index=False)
        df.to_parquet(base.with_suffix(".parquet"), index=False)
        for ext in ("csv", "parquet"):
            files.append({"src": str(base.with_suffix("." + ext)),
                          "arcname": f"series/{key}.{ext}"})
        n_ser += 1

    # --- data_dictionary.csv (from catalog metadata) ---
    dict_path = stage / "data_dictionary.csv"
    with dict_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["entry_type", "code_or_key", "name_or_label", "detail", "units"])
        for m in ("Use", "Supply", "A", "A_square", "L", "VA", "FD"):
            units, desc = MATRIX_DEFS[m]
            w.writerow(["matrix", m, m, desc, units])
        for sec in sectors.get("sectors", []):
            w.writerow(["sector", sec.get("code", ""), sec.get("name", ""),
                        f"agg15 group: {sec.get('agg15', '')}", "n/a"])
        for s in manifest.get("series", []):
            w.writerow(["series", s.get("key", ""), s.get("label", ""),
                        "derived time series", "see label"])

    # --- PROVENANCE.csv (per-table provenance from the manifest) ---
    prov_path = stage / "PROVENANCE.csv"
    with prov_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arcname", "year", "matrix", "provenance"])
        for t in manifest.get("tables", []):
            w.writerow([f"tables/{t['key']}", t.get("year", ""), t.get("matrix", ""),
                        t.get("provenance", "")])
        for s in manifest.get("series", []):
            w.writerow([f"series/{s['key']}", "1997-2024", s.get("key", ""),
                        s.get("source", "derived from BEA I-O cache")])

    # --- LICENSE + README ---
    lic_path = stage / "LICENSE"
    lic_path.write_text(CC_BY_4, encoding="utf-8")
    readme = stage / "README.md"
    readme.write_text(
        f"""# Leontief -- U.S. Input-Output Data Bundle (all years)

**Source:** U.S. Bureau of Economic Analysis (BEA) Input-Output Accounts,
Summary level (71 sectors), 1997-2024 (28 annual vintages).
**Cache generated:** {manifest.get('generated', 'unknown')}
**Bundle built:** {date.today().isoformat()}
**Site:** https://leontief.heterodata.org

## Contents
- `tables/<year>__<matrix>.{{csv,xlsx,parquet}}` -- {n_mat} matrices
  (Use, Supply, A, A_square, L, VA, FD per year), each in three formats.
- `series/<key>.{{csv,parquet}}` -- {n_ser} derived time series.
- `data_dictionary.csv` -- sector codes/names, matrix definitions, units.
- `PROVENANCE.csv` -- per-table BEA provenance.
- `LICENSE` -- CC-BY-4.0 (data).

Matrices carry BEA sector codes as row/column labels. A, A_square and L are
dimensionless coefficients; Use/Supply/VA/FD are in millions of current USD.
Derived per the Anu data-construction pipeline; see /methodology.
""", encoding="utf-8")

    # --- build reproducible zip + BUNDLE_MANIFEST.csv via kit make_bundles.py ---
    spec = importlib.util.spec_from_file_location("make_bundles", _KIT_MAKE_BUNDLES)
    mb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mb)

    bundle_manifest = {
        "name": "leontief-data",
        "license": str(lic_path),
        "dictionary": str(dict_path),
        "provenance": str(prov_path),
        "files": files + [{"src": str(readme), "arcname": "README.md"}],
    }
    bm_path = stage / "bundle_manifest.json"
    bm_path.write_text(json.dumps(bundle_manifest, indent=2), encoding="utf-8")

    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    out_zip = DOWNLOADS / "leontief_all.zip"
    rc = mb.main(["--manifest", str(bm_path), "--out", str(out_zip)])
    if rc != 0:
        raise SystemExit(f"make_bundles failed rc={rc}")
    print(f"[data] {n_mat} matrices x3 + {n_ser} series x2 -> {out_zip}")
    return out_zip


def build_code_bundle() -> Path:
    """Reproducible code zip: matrix-build pipeline + all study analysis code."""
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    out_zip = DOWNLOADS / "leontief_code.zip"
    members: list[tuple[str, bytes]] = []

    def add(arc: str, data: bytes):
        members.append((arc, data))

    # matrix-build pipeline
    bc = DATA_PIPELINE / "build_cache.py"
    if bc.exists():
        add("data_pipeline/build_cache.py", bc.read_bytes())
    for extra in ("build_sectors.py", "vendor.py"):
        p = DATA_PIPELINE / extra
        if p.exists():
            add(f"data_pipeline/{extra}", p.read_bytes())

    # study analysis code
    code_root = CONTENT / "studies" / "code"
    n_study = 0
    if code_root.exists():
        for slug_dir in sorted(code_root.iterdir()):
            if not slug_dir.is_dir():
                continue
            got = False
            for fname in ("analysis.py", "analysis.ipynb", "README.md", "requirements.txt"):
                fp = slug_dir / fname
                if fp.exists():
                    add(f"studies/{slug_dir.name}/{fname}", fp.read_bytes())
                    got = True
            if got:
                n_study += 1

    add("LICENSE", MIT.encode("utf-8"))
    add("README.md", (
        "# Leontief -- Analysis & Build Code\n\n"
        "Python + R code that builds the BEA input-output matrix cache and the\n"
        "reproducible example studies behind https://leontief.heterodata.org.\n\n"
        "- `data_pipeline/build_cache.py` -- BEA ingest -> A, A_square, "
        "L = (I - A)^-1, VA, FD.\n"
        f"- `studies/<slug>/analysis.py` (+ notebook) -- {n_study} study analyses "
        "(R and Python where provided).\n\n"
        "Full history + website source: https://github.com/andenick/leontief\n"
        "License: MIT (code). Data is CC-BY-4.0 (see the data bundle).\n"
    ).encode("utf-8"))

    # reproducible: fixed timestamp, sorted order, DEFLATE
    fixed = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arc, data in sorted(members, key=lambda m: m[0]):
            info = zipfile.ZipInfo(filename=arc, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.create_system = 3
            zf.writestr(info, data)
    print(f"[code] pipeline + {n_study} studies -> {out_zip} "
          f"({out_zip.stat().st_size} bytes)")
    return out_zip


def main() -> int:
    stage = DOWNLOADS / "_stage_data"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    try:
        data_zip = build_data_bundle(stage)
        code_zip = build_code_bundle()
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    print(f"DATA  {data_zip} = {data_zip.stat().st_size} bytes")
    print(f"CODE  {code_zip} = {code_zip.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
