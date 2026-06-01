"""Run all study analysis.py scripts and cache their Plotly figure JSONs.

For each of the 10 study slugs:
  1. Run its analysis.py headless with the venv python, CWD = study dir.
  2. Copy every produced outputs/fig_<figname>.json to
     site_data/cache/study__<slug>__<figname>.json.
  3. Collect outputs/*.csv table names.
  4. Read the study narrative frontmatter for title/difficulty/summary.
  5. Update site_manifest.json studies[] with a full entry for each study.

Idempotent: safe to re-run.  Prints a summary table at the end.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_WEBAPP_ROOT = _HERE.parent
_CONTENT_DIR = _WEBAPP_ROOT / "content"
_STUDIES_CODE = _CONTENT_DIR / "studies" / "code"
_STUDIES_MD = _CONTENT_DIR / "studies"
_SITE_DATA = _WEBAPP_ROOT / "site_data"
_CACHE_DIR = _SITE_DATA / "cache"
_MANIFEST_PATH = _SITE_DATA / "site_manifest.json"

SLUGS: list[str] = [
    "key-sectors",
    "multipliers-explained",
    "shock-propagation-hem",
    "deindustrialization",
    "covid-structural-shift",
    "supply-chains-network",
    "structural-decomposition",
    "fiscal-multipliers",
    "prices-and-distribution",
    "profit-rate-marx",
]

# Path to the venv python that should be used to run analysis.py scripts.
# Prefer the interpreter that is running this script (assumed to be the same venv).
_VENV_PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Parse minimal YAML-like frontmatter enclosed in --- fences.

    Returns the parsed meta dict (empty dict if no frontmatter found).
    """
    stripped = text.lstrip("﻿")
    if not stripped.startswith("---"):
        return {}
    first_nl = stripped.find("\n")
    if first_nl == -1:
        return {}
    if stripped[:first_nl].rstrip("\r") != "---":
        return {}
    rest = stripped[first_nl + 1:]
    close_m = re.search(r"^---\s*$", rest, re.MULTILINE)
    if not close_m:
        return {}
    fm_raw = rest[: close_m.start()]
    meta: dict = {}
    for line in fm_raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if re.fullmatch(r"-?\d+", val):
            meta[key] = int(val)
        else:
            meta[key] = val
    return meta


def _load_manifest() -> dict:
    if not _MANIFEST_PATH.exists():
        return {}
    with _MANIFEST_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _save_manifest(manifest: dict) -> None:
    _MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _MANIFEST_PATH.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)


def _run_analysis(slug: str) -> tuple[int, str, str]:
    """Run analysis.py for *slug* with CWD = study dir.

    Returns (exit_code, stdout, stderr).
    """
    study_dir = _STUDIES_CODE / slug
    analysis_py = study_dir / "analysis.py"
    if not analysis_py.exists():
        return -1, "", f"analysis.py not found at {analysis_py}"

    result = subprocess.run(
        [_VENV_PYTHON, str(analysis_py)],
        cwd=str(study_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    return result.returncode, result.stdout, result.stderr


def _cache_figs(slug: str) -> list[str]:
    """Copy outputs/fig_*.json -> cache/study__<slug>__<figname>.json.

    Returns list of figname strings (without fig_ prefix, without .json suffix).
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    outputs_dir = _STUDIES_CODE / slug / "outputs"
    figs: list[str] = []
    if not outputs_dir.exists():
        return figs
    for src in sorted(outputs_dir.glob("fig_*.json")):
        # figname = stem after stripping "fig_"
        figname = src.stem[4:]  # strip "fig_"
        dst = _CACHE_DIR / f"study__{slug}__{figname}.json"
        shutil.copy2(src, dst)
        figs.append(figname)
    return figs


def _collect_tables(slug: str) -> list[str]:
    """Return list of CSV base-names (without .csv extension) in outputs/."""
    outputs_dir = _STUDIES_CODE / slug / "outputs"
    if not outputs_dir.exists():
        return []
    return sorted(p.stem for p in outputs_dir.glob("*.csv"))


def _study_meta(slug: str) -> dict:
    """Return {title, difficulty, summary} from the narrative .md frontmatter."""
    md_path = _STUDIES_MD / f"{slug}.md"
    if not md_path.exists():
        return {"title": slug, "difficulty": "", "summary": ""}
    text = md_path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    return {
        "title": fm.get("title", slug),
        "difficulty": fm.get("difficulty", ""),
        "summary": fm.get("summary", ""),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    manifest = _load_manifest()

    # Build a lookup of existing non-study manifest keys to preserve them
    results: list[dict] = []

    print(f"\n{'Slug':<35}  {'Exit':>4}  {'#Figs':>5}  Notes")
    print("-" * 70)

    new_studies: list[dict] = []

    for slug in SLUGS:
        exit_code, stdout, stderr = _run_analysis(slug)

        notes = ""
        if exit_code != 0:
            notes = f"FAILED (rc={exit_code})"
            if stderr:
                # Show first line of error
                first_err = stderr.strip().splitlines()[-1][:60]
                notes += f": {first_err}"
        else:
            notes = "ok"

        figs = _cache_figs(slug)
        tables = _collect_tables(slug)
        meta = _study_meta(slug)

        entry: dict = {
            "slug": slug,
            "title": meta["title"],
            "difficulty": meta["difficulty"],
            "summary": meta["summary"],
            "figs": figs,
            "tables": tables,
            "bundle": f"/api/study/{slug}/bundle.zip",
        }
        new_studies.append(entry)

        print(f"{slug:<35}  {exit_code:>4}  {len(figs):>5}  {notes}")

        results.append({
            "slug": slug,
            "exit": exit_code,
            "figs": figs,
            "notes": notes,
        })

    print("-" * 70)
    total_figs = sum(len(r["figs"]) for r in results)
    failed = [r["slug"] for r in results if r["exit"] != 0]
    print(f"\nTotal figs cached: {total_figs}")
    if failed:
        print(f"FAILED slugs: {failed}")
    else:
        print("All 10 studies ran successfully.")

    # Update manifest
    manifest["studies"] = new_studies
    if "generated" not in manifest:
        manifest["generated"] = datetime.now(timezone.utc).isoformat()
    _save_manifest(manifest)
    print(f"\nManifest updated: {_MANIFEST_PATH}")
    print(f"Studies entries: {len(new_studies)}")


if __name__ == "__main__":
    main()
