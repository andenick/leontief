"""Narrative service — Markdown rendering with Wassily-specific directives.

Public API
----------
parse_frontmatter(text)         -> (meta: dict, body: str)
render_markdown(text)           -> {"meta": ..., "html": ..., "citations": [...]}
render_doc(relpath)             -> same dict (loads from content/<relpath>)
list_docs(subdir)               -> [{"slug": ..., "meta": ...}, ...]

Directives processed (all replaced before markdown render with raw-HTML blocks):

  {{chart:KEY}}
      KEY may contain colons (e.g. heatmap:2002:L).
      -> <div class="chart-embed" data-chart="KEY"></div>

  {{table:YEAR/MATRIX}}  or  {{table:YEAR/MATRIX?agg=15}}
      -> <div class="table-embed" data-year="YEAR" data-matrix="MATRIX"
             data-agg="15|''"></div>

  {{code:RELPATH}}  or  {{code:RELPATH#L10-L40}}
      Server-side Pygments highlight.  RELPATH is relative to WEBAPP_ROOT and
      must not escape outside it (path-traversal guard).
      Raw code stored in a hidden <textarea data-raw-code> so the copy button
      can read it without an extra HTTP round-trip; the download link uses
      /api/file/RELPATH.
      -> <figure class="code-block">…</figure>

  [cite:KEY]
      -> <sup class="cite"><a href="#cite-KEY">[n]</a></sup>
      Appends a <section class="bibliography"> at the end of the document.
      Metadata loaded from content/citations.json (optional).

Math preservation
-----------------
  $$...$$  (display) and $...$  (inline) are LEFT INTACT for client-side KaTeX.
  Strategy: before handing text to markdown-it, we pull every math span/block
  out and replace it with a unique placeholder token (``MBLOCK_n_`` /
  ``MINLINE_n_``).  After markdown-it renders HTML, we put the originals back.
  This stops markdown-it from eating underscores, backslashes, and asterisks
  inside math.

Copy / download for code blocks
---------------------------------
  The raw source text is stored in a <textarea class="raw-code" hidden> inside
  the <figure>.  app.js reads it with:
      btn.closest('figure').querySelector('.raw-code').value
  The download link hits /api/file/<RELPATH> (endpoint expected in api.py).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, get_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound

from app import config as C

# ---------------------------------------------------------------------------
# Markdown engine (shared instance — thread-safe for reads)
# ---------------------------------------------------------------------------

_md = MarkdownIt("commonmark", {"html": True, "typographer": True}).enable(["table"])

# ---------------------------------------------------------------------------
# Compiled regexes
# ---------------------------------------------------------------------------

# Chart: KEY may include colons  e.g.  heatmap:2002:L
_CHART_RE = re.compile(r"\{\{chart:(.*?)\}\}")

# Table:  {{table:YEAR/MATRIX}}  or  {{table:YEAR/MATRIX?agg=NN}}
_TABLE_RE = re.compile(r"\{\{table:(\d{4})/([A-Za-z_]+)(?:\?agg=(\d+))?\}\}")

# Code:  {{code:some/path.py}}  or  {{code:some/path.py#L10-L40}}
_CODE_RE = re.compile(r"\{\{code:([^}#]+?)(?:#L(\d+)-L(\d+))?\}\}")

# Citation:  [cite:KEY]
_CITE_RE = re.compile(r"\[cite:([A-Za-z0-9_.\-]+)\]")

# ---------------------------------------------------------------------------
# Citations JSON (cached)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_citations() -> dict[str, Any]:
    p = C.CONTENT_DIR / "citations.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _bust_citations_cache() -> None:
    """Call after tests that modify citations.json."""
    _load_citations.cache_clear()


# ---------------------------------------------------------------------------
# Frontmatter parser (no PyYAML required)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse minimal YAML-like frontmatter from *text*.

    If *text* starts with a line ``---`` followed by key: value pairs and a
    closing ``---``, those pairs are parsed into a dict.  Values that look like
    plain integers are coerced to ``int``.  Everything after the closing fence
    is returned as the body.

    Returns (meta, body).  If no frontmatter is found meta is {} and body is
    the full text.
    """
    if not text.lstrip("﻿").startswith("---"):
        return {}, text

    # Strip optional BOM then require "---" on the very first line
    stripped = text.lstrip("﻿")
    first_newline = stripped.find("\n")
    if first_newline == -1:
        return {}, text
    first_line = stripped[:first_newline].rstrip("\r")
    if first_line != "---":
        return {}, text

    rest = stripped[first_newline + 1:]
    # Find the closing ---
    close_re = re.compile(r"^---\s*$", re.MULTILINE)
    m = close_re.search(rest)
    if not m:
        return {}, text

    fm_raw = rest[: m.start()]
    body = rest[m.end():].lstrip("\n")

    meta: dict[str, Any] = {}
    for line in fm_raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # Coerce to int if purely numeric
        if re.fullmatch(r"-?\d+", val):
            meta[key] = int(val)
        else:
            meta[key] = val

    return meta, body


# ---------------------------------------------------------------------------
# Math protection helpers
# ---------------------------------------------------------------------------

def _extract_math(text: str) -> tuple[str, list[str]]:
    """Replace $$...$$ and $...$ with placeholder tokens.

    Handles display math first ($$), then inline ($).
    Stored originals returned as *bank*; restore with :func:`_restore_math`.

    Strategy: we tokenise greedily left-to-right to avoid overlap issues and
    to correctly handle nested/adjacent dollar signs.
    """
    bank: list[str] = []
    result: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        # Display math  $$ ... $$
        if text[i:i+2] == "$$":
            end = text.find("$$", i + 2)
            if end != -1:
                original = text[i : end + 2]
                idx = len(bank)
                bank.append(original)
                result.append(f"MBLOCK_{idx}_")
                i = end + 2
                continue

        # Inline math  $ ... $  (only if not $$, and not preceded by another $)
        if text[i] == "$":
            end = text.find("$", i + 1)
            if end != -1 and end != i + 1:   # avoid $$ being treated as empty inline
                original = text[i : end + 1]
                idx = len(bank)
                bank.append(original)
                result.append(f"MINLINE_{idx}_")
                i = end + 1
                continue

        result.append(text[i])
        i += 1

    return "".join(result), bank


def _restore_math(html: str, bank: list[str]) -> str:
    """Restore math placeholders in rendered *html*."""
    for idx, original in enumerate(bank):
        # Blocks
        html = html.replace(f"MBLOCK_{idx}_", original)
        # Inline — may be wrapped in <code> by markdown-it if backtick-adjacent
        html = html.replace(f"MINLINE_{idx}_", original)
    return html


# ---------------------------------------------------------------------------
# Directive handlers
# ---------------------------------------------------------------------------

def _chart_html(m: re.Match) -> str:
    key = m.group(1)
    return f'\n\n<div class="chart-embed" data-chart="{key}"></div>\n\n'


def _table_html(m: re.Match) -> str:
    year = m.group(1)
    matrix = m.group(2)
    agg = m.group(3) or ""
    return (
        f'\n\n<div class="table-embed" data-year="{year}" '
        f'data-matrix="{matrix}" data-agg="{agg}"></div>\n\n'
    )


def _build_code_html(relpath: str, line_start: int | None, line_end: int | None) -> str:
    """Build the Pygments-highlighted figure HTML for a code directive.

    Called during the *post-render* substitution pass so that the multi-line
    Pygments output never passes through markdown-it (which would corrupt it by
    interpreting blank lines inside <pre> as paragraph breaks).
    """
    # Path-traversal guard: resolve and ensure it stays under WEBAPP_ROOT
    try:
        target = (C.WEBAPP_ROOT / relpath).resolve()
        target.relative_to(C.WEBAPP_ROOT.resolve())  # raises ValueError if outside
    except (ValueError, OSError):
        return (
            f'<span class="code-error">path escape blocked: {relpath}</span>'
        )

    if not target.exists():
        return (
            f'<span class="code-error">file not found: {relpath}</span>'
        )

    try:
        raw_full = target.read_text(encoding="utf-8")
    except OSError as exc:
        return f'<span class="code-error">cannot read {relpath}: {exc}</span>'

    # Apply optional line range (1-based inclusive)
    if line_start is not None and line_end is not None:
        lines = raw_full.splitlines(keepends=True)
        raw_code = "".join(lines[line_start - 1 : line_end])
    else:
        raw_code = raw_full

    # Pygments highlight
    try:
        lexer = get_lexer_for_filename(target.name)
    except ClassNotFound:
        try:
            lexer = guess_lexer(raw_code)
        except ClassNotFound:
            lexer = PythonLexer()

    formatter = HtmlFormatter(cssclass="highlight")
    highlighted = highlight(raw_code, lexer, formatter)

    # Store raw code in a hidden textarea so copy-btn works without a network
    # round-trip.  app.js reads:
    #   btn.closest('figure').querySelector('.raw-code').value
    # Forward slashes for download href (POSIX-style URL path)
    url_path = relpath.replace("\\", "/")
    raw_escaped = raw_code.replace("</textarea", "<\\/textarea")

    range_label = f"#L{line_start}-L{line_end}" if line_start else ""
    return (
        f'<figure class="code-block">'
        f'<figcaption>{relpath}{range_label} '
        f'<button class="copy-btn">copy</button> '
        f'<a class="dl-code" href="/api/file/{url_path}" download>download</a>'
        f'</figcaption>'
        f'{highlighted}'
        f'<textarea class="raw-code" hidden>{raw_escaped}</textarea>'
        f'</figure>'
    )


def _extract_code_directives(body: str) -> tuple[str, list[str]]:
    """Replace {{code:...}} directives with single-line placeholder tokens.

    Returns the modified body and a bank of rendered HTML strings.
    This is the first pass of a two-pass approach:
      Pass 1 (pre-render):  {{code:...}}  ->  CODEBLOCK_n_
      Pass 2 (post-render): CODEBLOCK_n_  ->  actual <figure>…</figure> HTML

    Why two passes?  The Pygments HTML output contains blank lines inside
    <pre> blocks.  If it were present during markdown-it rendering, those blank
    lines would be interpreted as paragraph separators, inserting spurious <p>
    tags inside the <pre>.  Placeholder tokens are single opaque words that
    markdown-it leaves untouched.
    """
    bank: list[str] = []

    def replacer(m: re.Match) -> str:
        relpath = m.group(1).strip()
        line_start = int(m.group(2)) if m.group(2) else None
        line_end = int(m.group(3)) if m.group(3) else None
        idx = len(bank)
        bank.append(_build_code_html(relpath, line_start, line_end))
        # Surround with blank lines so markdown-it treats the token as a block,
        # then the placeholder itself sits on its own paragraph line.
        return f"\n\nCODEBLOCK_{idx}_\n\n"

    body = _CODE_RE.sub(replacer, body)
    return body, bank


def _restore_code_blocks(html: str, bank: list[str]) -> str:
    """Replace CODEBLOCK_n_ tokens in rendered HTML with actual figure HTML."""
    for idx, figure_html in enumerate(bank):
        # markdown-it wraps bare paragraph text in <p>…</p> — strip that wrapper
        html = html.replace(
            f"<p>CODEBLOCK_{idx}_</p>", figure_html
        )
        # Fallback: token without paragraph wrapper (shouldn't happen, but safe)
        html = html.replace(f"CODEBLOCK_{idx}_", figure_html)
    return html


# ---------------------------------------------------------------------------
# Citation handler
# ---------------------------------------------------------------------------

def _process_citations(body: str) -> tuple[str, list[dict]]:
    """Replace [cite:KEY] with superscript refs; return (body, ordered_list)."""
    cites = _load_citations()
    used: list[dict] = []
    idx: dict[str, int] = {}

    def cite_sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in idx:
            n = len(used) + 1
            idx[key] = n
            entry = {"n": n, "key": key}
            entry.update(cites.get(key, {}))   # merge citation metadata if present
            used.append(entry)
        n = idx[key]
        return f'<sup class="cite"><a href="#cite-{key}">[{n}]</a></sup>'

    body = _CITE_RE.sub(cite_sub, body)
    return body, used


def _bibliography_html(citations_list: list[dict]) -> str:
    """Render a <section class="bibliography"> from the collected citation list."""
    if not citations_list:
        return ""
    items = []
    for entry in citations_list:
        key = entry["key"]
        n = entry["n"]
        # If we have metadata fields use them; otherwise show raw key
        if len(entry) > 2:   # has fields beyond n and key
            label = entry.get("label") or entry.get("title") or key
            ref = entry.get("ref") or entry.get("url") or ""
            ref_html = f' <a href="{ref}" target="_blank">{ref}</a>' if ref else ""
            items.append(
                f'<li id="cite-{key}">[{n}] {label}{ref_html}</li>'
            )
        else:
            items.append(f'<li id="cite-{key}">[{n}] {key}</li>')

    return (
        '\n<section class="bibliography">\n'
        "<h2>References</h2>\n"
        "<ol>\n"
        + "\n".join(items)
        + "\n</ol>\n</section>\n"
    )


# ---------------------------------------------------------------------------
# Main rendering pipeline
# ---------------------------------------------------------------------------

def render_markdown(text: str) -> dict[str, Any]:
    """Full pipeline: frontmatter → directives → math-protect → markdown → restore.

    Returns::

        {
            "meta":       dict,
            "html":       str,
            "citations":  list[dict],   # ordered citation entries for this page
        }
    """
    meta, body = parse_frontmatter(text)

    # 1. Process citations (before markdown so refs are inline HTML)
    body, citations_list = _process_citations(body)

    # 2. Expand simple directives (chart, table) — single-line HTML blocks safe
    #    for markdown-it's html passthrough.
    body = _CHART_RE.sub(_chart_html, body)
    body = _TABLE_RE.sub(_table_html, body)

    # 3. Extract code directives into a post-render bank (two-pass).
    #    Pygments output contains blank lines inside <pre> that would be
    #    misinterpreted as paragraph breaks if left for markdown-it to see.
    body, code_bank = _extract_code_directives(body)

    # 4. Protect math spans from markdown-it mangling
    body, math_bank = _extract_math(body)

    # 5. Render markdown
    html = _md.render(body)

    # 6. Restore math (before code, so math inside figcaptions is safe)
    html = _restore_math(html, math_bank)

    # 7. Restore code blocks (replaces CODEBLOCK_n_ tokens with <figure> HTML)
    html = _restore_code_blocks(html, code_bank)

    # 8. Append bibliography
    html += _bibliography_html(citations_list)

    return {
        "meta": meta,
        "html": html,
        "citations": citations_list,
    }


# ---------------------------------------------------------------------------
# File-based helpers
# ---------------------------------------------------------------------------

def render_doc(relpath: str) -> dict[str, Any]:
    """Load ``content/<relpath>`` and run the full render pipeline.

    Raises :class:`FileNotFoundError` if the file does not exist.
    """
    p = C.CONTENT_DIR / relpath
    if not p.exists():
        raise FileNotFoundError(
            f"Content file not found: {p}  (relpath={relpath!r})"
        )
    return render_markdown(p.read_text(encoding="utf-8"))


def list_docs(subdir: str) -> list[dict[str, Any]]:
    """Scan ``content/<subdir>/*.md`` and return sorted index entries.

    Each entry is ``{"slug": str, "meta": dict}``.  Sorted by
    ``meta.get("order", 9999)`` then filename.

    Returns ``[]`` if the directory does not exist or contains no ``.md`` files.
    """
    d = C.CONTENT_DIR / subdir
    if not d.is_dir():
        return []

    entries = []
    for p in d.glob("*.md"):
        try:
            meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        except OSError:
            meta = {}
        entries.append({"slug": p.stem, "meta": meta})

    entries.sort(key=lambda e: (e["meta"].get("order", 9999), e["slug"]))
    return entries
