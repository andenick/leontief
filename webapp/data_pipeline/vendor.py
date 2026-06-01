"""Vendor front-end assets so the site has zero runtime CDN dependency.

Assets vendored:
  - plotly.min.js  (from installed plotly package)
  - katex/          (katex.min.js, katex.min.css, auto-render.min.js, fonts/)
                    downloaded from jsDelivr
  - pygments.css    (generated from Pygments HtmlFormatter)

Run with the webapp venv python:
    .venv/Scripts/python.exe data_pipeline/vendor.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Make `from app import config` work when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config as C  # noqa: E402

VENDOR = C.STATIC_DIR / "vendor"
KATEX_VERSION = "0.16.11"
JSDELIVR = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist"

# KaTeX font files to vendor (subset sufficient for math)
KATEX_FONTS = [
    "KaTeX_AMS-Regular.woff2",
    "KaTeX_Caligraphic-Bold.woff2",
    "KaTeX_Caligraphic-Regular.woff2",
    "KaTeX_Fraktur-Bold.woff2",
    "KaTeX_Fraktur-Regular.woff2",
    "KaTeX_Main-Bold.woff2",
    "KaTeX_Main-BoldItalic.woff2",
    "KaTeX_Main-Italic.woff2",
    "KaTeX_Main-Regular.woff2",
    "KaTeX_Math-BoldItalic.woff2",
    "KaTeX_Math-Italic.woff2",
    "KaTeX_SansSerif-Bold.woff2",
    "KaTeX_SansSerif-Italic.woff2",
    "KaTeX_SansSerif-Regular.woff2",
    "KaTeX_Script-Regular.woff2",
    "KaTeX_Size1-Regular.woff2",
    "KaTeX_Size2-Regular.woff2",
    "KaTeX_Size3-Regular.woff2",
    "KaTeX_Size4-Regular.woff2",
    "KaTeX_Typewriter-Regular.woff2",
]


def _get(url: str, timeout: int = 30) -> bytes:
    import requests
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content


def vendor_plotly() -> bool:
    """Copy plotly.min.js out of the installed plotly package."""
    try:
        import plotly
    except ImportError:
        print("plotly not installed — skipping")
        return False
    pkg = Path(plotly.__file__).parent
    candidates = [
        pkg / "package_data" / "plotly.min.js",
        pkg / "offline" / "plotly.min.js",
    ]
    for cand in candidates:
        if cand.exists():
            VENDOR.mkdir(parents=True, exist_ok=True)
            dest = VENDOR / "plotly.min.js"
            shutil.copy(cand, dest)
            size_kb = dest.stat().st_size // 1024
            print(f"  plotly.min.js  {size_kb:,} KB  <- {cand}")
            return True
    print("  could not locate plotly.min.js in plotly package — searched:")
    for c in candidates:
        print(f"    {c}")
    return False


def vendor_katex() -> bool:
    """Download KaTeX js, css, auto-render, and fonts from jsDelivr."""
    katex_dir = VENDOR / "katex"
    fonts_dir = katex_dir / "fonts"
    katex_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "katex.min.js":       f"{JSDELIVR}/katex.min.js",
        "katex.min.css":      f"{JSDELIVR}/katex.min.css",
        "auto-render.min.js": f"{JSDELIVR}/contrib/auto-render.min.js",
    }

    ok = True
    for fname, url in files.items():
        dest = katex_dir / fname
        try:
            data = _get(url)
            dest.write_bytes(data)
            print(f"  katex/{fname}  {len(data) // 1024:,} KB")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED katex/{fname}: {exc}")
            ok = False

    # Fonts
    failed_fonts = 0
    for font in KATEX_FONTS:
        dest = fonts_dir / font
        url = f"{JSDELIVR}/fonts/{font}"
        try:
            data = _get(url)
            dest.write_bytes(data)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED katex/fonts/{font}: {exc}")
            failed_fonts += 1
    print(f"  katex/fonts/  {len(KATEX_FONTS) - failed_fonts}/{len(KATEX_FONTS)} woff2 files OK")

    # Patch katex.min.css to use relative font paths (remove absolute URL prefix)
    css_path = katex_dir / "katex.min.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        # jsDelivr CSS ships with relative paths already; confirm no absolute hrefs leaked
        if JSDELIVR in css:
            css = css.replace(JSDELIVR + "/fonts/", "fonts/")
            css_path.write_text(css, encoding="utf-8")
            print("  katex.min.css patched: absolute font URLs -> relative")
    return ok


def vendor_pygments() -> bool:
    """Write a Pygments default dark stylesheet for code highlighting."""
    try:
        from pygments.formatters import HtmlFormatter
    except ImportError:
        print("Pygments not installed — skipping")
        return False
    VENDOR.mkdir(parents=True, exist_ok=True)
    dest = VENDOR / "pygments.css"
    css = HtmlFormatter(style="default").get_style_defs(".highlight")
    dest.write_text(css, encoding="utf-8")
    print(f"  pygments.css  {dest.stat().st_size} bytes  (style=default)")
    return True


if __name__ == "__main__":
    print(f"Vendoring front-end assets into {VENDOR}\n")

    print("[1/3] plotly.min.js")
    vendor_plotly()

    print("\n[2/3] KaTeX")
    vendor_katex()

    print("\n[3/3] Pygments CSS")
    vendor_pygments()

    print("\nDone.")
