"""Chart service — CHART_REGISTRY and Plotly figure builders.

Every builder returns a JSON-safe dict::

    {
        "figure":    <Plotly figure dict, NaN/Inf sanitized to None>,
        "caption":   str,
        "download":  {"csv": str, "xlsx": str, "json": str, "parquet": str} | None,
        "citations": [str]
    }

Dispatch
--------
build_chart(key, **params) -> dict

``key`` may be:
  - A plain registry name:  "matrix_heatmap"
  - A compound name:        "heatmap:2024:L" or "heatmap:2024:L:15"
      format  <alias>:<arg1>:<arg2>:...
      aliases: "heatmap" -> matrix_heatmap(year, matrix[, agg])
               "mult_bar" -> multiplier_bar(year[, n])
  - Any registered CHART_REGISTRY key.

Unknown key raises ValueError listing available builders.

THEME
-----
Module-level THEME dict applied to every figure's layout.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import plotly.graph_objects as go

from app.services.data_service import (
    get_series_meta,
    get_table_meta,
    read_matrix,
    read_series,
    sector_names_map,
)
from app.services.table_service import matrix_payload

# ---------------------------------------------------------------------------
# Cache dir — resolved relative to this file to avoid circular imports
# ---------------------------------------------------------------------------

_WEBAPP_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR: Path = _WEBAPP_ROOT / "site_data" / "cache"


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

THEME: dict[str, Any] = {
    "font": {
        "family": "Inter, Arial, sans-serif",
        "size": 12,
        "color": "#1a1a2e",
    },
    "paper_bgcolor": "#fafafa",
    "plot_bgcolor": "#ffffff",
    "margin": {"l": 80, "r": 40, "t": 60, "b": 80},
    "colorway": [
        "#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51",
        "#457b9d", "#a8dadc", "#e63946", "#06d6a0", "#118ab2",
    ],
    # Diverging colorscale for heatmaps (blue-white-red)
    "heatmap_colorscale": [
        [0.0, "#1d3557"],
        [0.25, "#457b9d"],
        [0.5, "#f1faee"],
        [0.75, "#e63946"],
        [1.0, "#9b2226"],
    ],
}


# ---------------------------------------------------------------------------
# JSON sanitization
# ---------------------------------------------------------------------------

def _sanitize(obj: Any) -> Any:
    """Recursively replace NaN/Inf with None for JSON safety."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _fig_dict(fig: go.Figure) -> dict:
    """Return a JSON-safe Plotly figure dict."""
    return _sanitize(fig.to_dict())


# ---------------------------------------------------------------------------
# Shared layout helper
# ---------------------------------------------------------------------------

def _base_layout(**overrides: Any) -> dict:
    """Return a layout dict starting from THEME defaults, with overrides merged."""
    layout = {
        "font": THEME["font"],
        "paper_bgcolor": THEME["paper_bgcolor"],
        "plot_bgcolor": THEME["plot_bgcolor"],
        "margin": THEME["margin"],
        "colorway": THEME["colorway"],
    }
    layout.update(overrides)
    return layout


# ---------------------------------------------------------------------------
# Builder 1: matrix_heatmap
# ---------------------------------------------------------------------------

def matrix_heatmap(year: int, matrix: str = "L", agg: str | None = None) -> dict:
    """Build a Plotly Heatmap for a matrix at the given year.

    Uses table_service.matrix_payload to get labeled data and applies
    the diverging THEME colorscale. Hovertemplate shows row name, col name,
    and value.

    Args:
        year:   Table year (1997-2024).
        matrix: Matrix key, e.g. "L", "Use", "A", "A_square", "Supply", "VA", "FD".
        agg:    Pass "15" to aggregate to 15 broad sectors.

    Returns:
        Chart payload dict.
    """
    payload = matrix_payload(year, matrix, agg=agg)
    meta = get_table_meta(year, matrix)

    z = payload["values"]            # list[list[float|None]]
    x_labels = payload["column_names"]
    y_labels = payload["index_names"]
    x_codes = payload["columns"]
    y_codes = payload["index"]

    # Custom hover: use codes for brevity in template; names via customdata
    customdata_rows = [
        [[y_codes[r], x_codes[c]] for c in range(len(x_labels))]
        for r in range(len(y_labels))
    ]

    trace = go.Heatmap(
        z=z,
        x=x_codes,
        y=y_codes,
        colorscale=THEME["heatmap_colorscale"],
        hovertemplate=(
            "<b>Row:</b> %{meta[0]}<br>"
            "<b>Col:</b> %{meta[1]}<br>"
            "<b>Value:</b> %{z:.4f}<extra></extra>"
        ),
        meta=[[f"{y_labels[r]} ({y_codes[r]})" + "||" + f"{x_labels[c]} ({x_codes[c]})"
               for c in range(len(x_codes))]
              for r in range(len(y_codes))],
    )

    # Rebuild with proper meta structure for hovertemplate
    trace2 = go.Heatmap(
        z=z,
        x=x_codes,
        y=y_codes,
        colorscale=THEME["heatmap_colorscale"],
        customdata=customdata_rows,
        hovertemplate=(
            "<b>Row:</b> %{customdata[0]}<br>"
            "<b>Col:</b> %{customdata[1]}<br>"
            "<b>Value:</b> %{z:.4f}<extra></extra>"
        ),
    )

    n = payload["rows"]
    agg_label = f" (aggregated to {payload['cols']} groups)" if agg == "15" else ""
    title_text = f"{meta['label']}{agg_label}"

    fig = go.Figure(
        data=[trace2],
        layout=go.Layout(
            **_base_layout(
                title={"text": title_text, "x": 0.5, "xanchor": "center"},
                xaxis={"title": "Sector (column)", "tickangle": -45, "tickfont": {"size": 9}},
                yaxis={"title": "Sector (row)", "autorange": "reversed", "tickfont": {"size": 9}},
                height=650,
            )
        ),
    )

    caption = (
        f"Leontief {matrix} matrix for {year}, {n}×{n} sectors"
        + agg_label
        + ". Values show inter-industry technical or total requirements."
    )

    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["bea_iouse", "leontief_1941"],
    }


# ---------------------------------------------------------------------------
# Builder 2: multiplier_bar
# ---------------------------------------------------------------------------

def multiplier_bar(year: int, n: int = 15) -> dict:
    """Horizontal bar chart of the top-N output multipliers for a given year.

    Output multiplier of sector j = column sum of the Leontief inverse L
    (sum over i of L[i,j]). Shows the sectors with the highest economy-wide
    demand stimulus per dollar of final demand.

    Args:
        year: Table year (1997-2024).
        n:    Number of top sectors to show (default 15).

    Returns:
        Chart payload dict.
    """
    names_map = sector_names_map()
    df = read_matrix(year, "L")

    multipliers = df.sum(axis=0).rename("multiplier")
    top = multipliers.nlargest(n).sort_values(ascending=True)  # ascending for horiz bar

    sector_names_list = [names_map.get(code, code) for code in top.index]
    values = top.tolist()

    trace = go.Bar(
        x=values,
        y=sector_names_list,
        orientation="h",
        marker_color=THEME["colorway"][0],
        hovertemplate="<b>%{y}</b><br>Multiplier: %{x:.3f}<extra></extra>",
    )

    fig = go.Figure(
        data=[trace],
        layout=go.Layout(
            **_base_layout(
                title={
                    "text": f"Top {n} Output Multipliers, {year}",
                    "x": 0.5,
                    "xanchor": "center",
                },
                xaxis={"title": "Output Multiplier (column sum of L)"},
                yaxis={"title": "Sector", "automargin": True},
                height=max(350, n * 28 + 120),
            )
        ),
    )

    caption = (
        f"Top {n} sectors by output multiplier in {year}. "
        "Each bar shows the total dollar increase in output across all sectors "
        "generated by one dollar of final demand for that sector's output "
        "(column sum of the Leontief inverse, L)."
    )

    meta = get_table_meta(year, "L")
    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["bea_iouse", "miller_blair_2009"],
    }


# ---------------------------------------------------------------------------
# Builder 3: multiplier_trend
# ---------------------------------------------------------------------------

def multiplier_trend() -> dict:
    """Line chart of the economy-wide mean output multiplier, 1997-2024.

    Source: multiplier_timeseries series.  The mean is taken across all
    71 sector columns for each year, summarising how the average dollar of
    final demand ripples through the economy over time.

    Returns:
        Chart payload dict.
    """
    df = read_series("multiplier_timeseries")
    meta = get_series_meta("multiplier_timeseries")

    # Sector columns = everything except 'year'
    sector_cols = [c for c in df.columns if c != "year"]
    year_col = df["year"].astype(int)
    mean_mult = df[sector_cols].mean(axis=1)

    trace = go.Scatter(
        x=year_col.tolist(),
        y=mean_mult.tolist(),
        mode="lines+markers",
        line={"color": THEME["colorway"][0], "width": 2},
        marker={"size": 6},
        hovertemplate="<b>%{x}</b><br>Mean multiplier: %{y:.3f}<extra></extra>",
        name="Mean output multiplier",
    )

    fig = go.Figure(
        data=[trace],
        layout=go.Layout(
            **_base_layout(
                title={
                    "text": "Economy-Wide Mean Output Multiplier, 1997–2024",
                    "x": 0.5,
                    "xanchor": "center",
                },
                xaxis={"title": "Year", "dtick": 2},
                yaxis={"title": "Mean Output Multiplier"},
                height=420,
            )
        ),
    )

    caption = (
        "Economy-wide mean output multiplier (average of column sums of L across "
        "71 BEA sectors) from 1997 to 2024. A rising trend indicates growing "
        "inter-industry interdependence; a falling trend reflects structural "
        "simplification or import substitution."
    )

    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["bea_iouse", "miller_blair_2009"],
    }


# ---------------------------------------------------------------------------
# Builder 4: linkage_scatter
# ---------------------------------------------------------------------------

def linkage_scatter(year: int) -> dict:
    """Scatter of backward vs forward linkage for all sectors in a given year.

    Backward linkage (BL) = normalised column sum of L (demand-pull).
    Forward linkage (FL)  = normalised row sum of L (supply-push).

    Both are normalised by dividing by the grand mean so that 1.0 is average.
    Sectors with BL > 1 and FL > 1 are "key sectors" in the Rasmussen sense.

    Args:
        year: Table year (1997-2024).

    Returns:
        Chart payload dict.
    """
    names_map = sector_names_map()
    df = read_matrix(year, "L")

    n = df.shape[0]
    col_sums = df.sum(axis=0)   # backward linkage (un-normalised)
    row_sums = df.sum(axis=1)   # forward linkage (un-normalised)

    # Normalise by overall mean (Miller & Blair normalisation)
    grand_mean = df.values.sum() / (n * n)
    bl = col_sums / (n * grand_mean)
    fl = row_sums / (n * grand_mean)

    sector_names_list = [names_map.get(code, code) for code in df.columns]

    # Colour by quadrant
    colors = []
    for b, f in zip(bl, fl):
        if b >= 1.0 and f >= 1.0:
            colors.append(THEME["colorway"][4])   # red = key
        elif b >= 1.0:
            colors.append(THEME["colorway"][0])   # dark = backward-dominant
        elif f >= 1.0:
            colors.append(THEME["colorway"][1])   # teal = forward-dominant
        else:
            colors.append(THEME["colorway"][6])   # light = weak

    trace = go.Scatter(
        x=bl.tolist(),
        y=fl.tolist(),
        mode="markers",
        marker={"color": colors, "size": 8, "opacity": 0.8},
        text=sector_names_list,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Backward linkage: %{x:.3f}<br>"
            "Forward linkage: %{y:.3f}<extra></extra>"
        ),
    )

    # Quadrant reference lines at 1.0
    shapes = [
        {"type": "line", "x0": 1, "x1": 1,
         "y0": 0, "y1": 1, "yref": "paper",
         "line": {"dash": "dash", "color": "#888", "width": 1}},
        {"type": "line", "y0": 1, "y1": 1,
         "x0": 0, "x1": 1, "xref": "paper",
         "line": {"dash": "dash", "color": "#888", "width": 1}},
    ]

    annotations = [
        {"x": 1.02, "y": 1.02, "xref": "x", "yref": "y",
         "text": "Key sectors", "showarrow": False,
         "font": {"size": 10, "color": THEME["colorway"][4]}},
    ]

    fig = go.Figure(
        data=[trace],
        layout=go.Layout(
            **_base_layout(
                title={
                    "text": f"Backward vs Forward Linkage, {year}",
                    "x": 0.5,
                    "xanchor": "center",
                },
                xaxis={"title": "Backward Linkage (normalised column sum of L)"},
                yaxis={"title": "Forward Linkage (normalised row sum of L)"},
                shapes=shapes,
                annotations=annotations,
                height=550,
            )
        ),
    )

    caption = (
        f"Rasmussen ({year}) linkage diagram. Backward linkage measures how strongly "
        "a sector pulls demand from its suppliers; forward linkage measures how "
        "strongly it stimulates downstream sectors. Both are normalised to the "
        "economy-wide mean (= 1.0). Sectors in the upper-right quadrant "
        "(BL > 1, FL > 1) are Rasmussen 'key sectors'."
    )

    meta = get_table_meta(year, "L")
    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["rasmussen_1956", "miller_blair_2009"],
    }


# ---------------------------------------------------------------------------
# Builder 5: structural_trend
# ---------------------------------------------------------------------------

def structural_trend(key: str) -> dict:
    """Line chart for a single-value-per-year structural series.

    Supported keys: deindustrialization, financialization, labor_share.
    The value column is auto-detected as the first non-year numeric column.
    Multiple value columns are each plotted as a separate line.

    Args:
        key: Series key, one of {deindustrialization, financialization, labor_share}.

    Returns:
        Chart payload dict.
    """
    _ALLOWED = {"deindustrialization", "financialization", "labor_share"}
    if key not in _ALLOWED:
        raise ValueError(
            f"structural_trend key must be one of {_ALLOWED}, got {key!r}"
        )

    df = read_series(key)
    meta = get_series_meta(key)

    year_col = df["year"].astype(int).tolist()
    # Value columns = numeric non-year columns
    value_cols = [c for c in df.columns if c != "year" and
                  str(df[c].dtype).startswith("float")]

    if not value_cols:
        # Fallback: all non-year columns
        value_cols = [c for c in df.columns if c != "year"]

    # Use only the first value column as the primary (others as secondary traces)
    primary_col = value_cols[0]

    traces = []
    for i, col in enumerate(value_cols):
        traces.append(
            go.Scatter(
                x=year_col,
                y=df[col].tolist(),
                mode="lines+markers",
                name=col.replace("_", " ").title(),
                line={"color": THEME["colorway"][i % len(THEME["colorway"])], "width": 2},
                marker={"size": 6},
                hovertemplate=f"<b>%{{x}}</b><br>{col}: %{{y:.4f}}<extra></extra>",
            )
        )

    label = meta.get("label", key.replace("_", " ").title())

    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            **_base_layout(
                title={"text": label, "x": 0.5, "xanchor": "center"},
                xaxis={"title": "Year", "dtick": 2},
                yaxis={"title": primary_col.replace("_", " ").title()},
                legend={"orientation": "h", "y": -0.2},
                height=420,
            )
        ),
    )

    caption = (
        f"{label}. Source: BEA I-O accounts, 1997–2024. "
        "Values are shares of total value-added unless noted otherwise."
    )

    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["bea_iouse"],
    }


# ---------------------------------------------------------------------------
# Builder 6: generic_series
# ---------------------------------------------------------------------------

def generic_series(key: str, columns: list[str] | None = None) -> dict:
    """Parameterized line chart for any series vs year.

    Plots selected columns of any series against the 'year' column.
    If year column is absent (e.g. structural_change uses year_from),
    falls back to a best-effort x-axis.

    If columns is None, plots:
      - Up to 5 columns if the series has ≤ 10 non-year columns, or
      - The mean of all sector columns as a single line otherwise.

    Args:
        key:     Any series key in the manifest.
        columns: Optional list of column names to plot. None = auto-select.

    Returns:
        Chart payload dict.
    """
    df = read_series(key)
    meta = get_series_meta(key)

    # Determine x-axis column
    if "year" in df.columns:
        x_col = "year"
    elif "year_from" in df.columns:
        x_col = "year_from"
    else:
        x_col = df.columns[0]

    non_x_cols = [c for c in df.columns if c != x_col]

    if columns is not None:
        plot_cols = [c for c in columns if c in df.columns]
        if not plot_cols:
            raise ValueError(
                f"None of the requested columns {columns!r} found in series {key!r}. "
                f"Available: {list(df.columns)}"
            )
        use_mean = False
    else:
        numeric_cols = [c for c in non_x_cols
                        if str(df[c].dtype).startswith(("float", "int"))]
        if len(numeric_cols) <= 10:
            plot_cols = numeric_cols[:5]
            use_mean = False
        else:
            # Too many sector cols — plot mean
            plot_cols = numeric_cols
            use_mean = True

    x_vals = df[x_col].astype(int).tolist()
    label = meta.get("label", key.replace("_", " ").title())

    traces = []
    if use_mean:
        mean_vals = df[plot_cols].mean(axis=1).tolist()
        traces.append(
            go.Scatter(
                x=x_vals,
                y=mean_vals,
                mode="lines+markers",
                name="Cross-sector mean",
                line={"color": THEME["colorway"][0], "width": 2},
                marker={"size": 6},
                hovertemplate="<b>%{x}</b><br>Mean: %{y:.4f}<extra></extra>",
            )
        )
        y_title = f"Mean of {len(plot_cols)} sector values"
    else:
        for i, col in enumerate(plot_cols):
            traces.append(
                go.Scatter(
                    x=x_vals,
                    y=df[col].tolist(),
                    mode="lines+markers",
                    name=col.replace("_", " ").title(),
                    line={
                        "color": THEME["colorway"][i % len(THEME["colorway"])],
                        "width": 2,
                    },
                    marker={"size": 5},
                    hovertemplate=f"<b>%{{x}}</b><br>{col}: %{{y:.4f}}<extra></extra>",
                )
            )
        y_title = "Value"

    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            **_base_layout(
                title={"text": label, "x": 0.5, "xanchor": "center"},
                xaxis={"title": x_col.replace("_", " ").title(), "dtick": 2},
                yaxis={"title": y_title},
                legend={"orientation": "h", "y": -0.25},
                height=430,
            )
        ),
    )

    caption = (
        f"{label}. Plotted columns: "
        f"{'cross-sector mean' if use_mean else ', '.join(plot_cols)}."
    )

    return {
        "figure": _fig_dict(fig),
        "caption": caption,
        "download": meta.get("downloads"),
        "citations": ["bea_iouse"],
    }


# ---------------------------------------------------------------------------
# CHART_REGISTRY
# ---------------------------------------------------------------------------

CHART_REGISTRY: dict[str, Any] = {
    "matrix_heatmap": matrix_heatmap,
    "multiplier_bar": multiplier_bar,
    "multiplier_trend": multiplier_trend,
    "linkage_scatter": linkage_scatter,
    "structural_trend": structural_trend,
    "generic_series": generic_series,
}

# Compound-key aliases  alias -> (builder_name, positional_arg_names)
_COMPOUND_ALIASES: dict[str, tuple[str, list[str]]] = {
    "heatmap":   ("matrix_heatmap", ["year", "matrix", "agg"]),
    "mult_bar":  ("multiplier_bar", ["year", "n"]),
    "linkage":   ("linkage_scatter", ["year"]),
    "struct":    ("structural_trend", ["key"]),
}


# ---------------------------------------------------------------------------
# Study chart builder — loads a pre-computed Plotly JSON from cache
# ---------------------------------------------------------------------------

def _build_study_chart(slug: str, figname: str) -> dict:
    """Load a cached study figure and return the standard chart envelope.

    Looks up ``site_data/cache/study__<slug>__<figname>.json``, which must be
    a JSON-serialised Plotly figure dict (produced by ``fig.to_dict()``).

    Args:
        slug:    Study slug, e.g. "key-sectors".
        figname: Figure name, e.g. "linkage_scatter".

    Returns:
        Standard chart payload dict::

            {
                "figure":   <sanitized Plotly figure dict>,
                "caption":  str,
                "download": {"bundle": str},
                "citations": [],
            }

    Raises:
        ValueError: if slug or figname is not found in the cache.
    """
    cache_path = _CACHE_DIR / f"study__{slug}__{figname}.json"
    if not cache_path.exists():
        # Provide a helpful error listing what IS available for this slug
        available = sorted(
            p.name for p in _CACHE_DIR.glob(f"study__{slug}__*.json")
        )
        if available:
            raise ValueError(
                f"Study figure not found: slug={slug!r}, figname={figname!r}. "
                f"Available for this slug: {available}. "
                f"Cache path checked: {cache_path}"
            )
        # No files at all for this slug
        all_slugs = sorted(
            set(
                p.name.split("__")[1]
                for p in _CACHE_DIR.glob("study__*__*.json")
            )
        )
        raise ValueError(
            f"Study slug {slug!r} not found in cache. "
            f"Available slugs: {all_slugs}. "
            f"Run data_pipeline/run_studies.py to populate the cache."
        )

    with cache_path.open(encoding="utf-8") as fh:
        fig_dict = json.load(fh)

    # Sanitize NaN/Inf -> None
    fig_dict = _sanitize(fig_dict)

    # Derive caption from study manifest (gracefully fall back to figname)
    caption = f"{slug.replace('-', ' ').title()} — {figname.replace('_', ' ')}"
    try:
        from app.services.data_service import list_studies
        for study in list_studies():
            if study.get("slug") == slug:
                title = study.get("title", "")
                if title:
                    caption = title
                break
    except Exception:  # noqa: BLE001
        pass

    return {
        "figure": fig_dict,
        "caption": caption,
        "download": {"bundle": f"/api/study/{slug}/bundle.zip"},
        "citations": [],
    }


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def build_chart(chart_key: str, **params: Any) -> dict:
    """Dispatch a chart build by key.

    Key formats
    -----------
    1. Plain registry name:
         build_chart("matrix_heatmap", year=2002, matrix="L")
         build_chart("structural_trend", key="deindustrialization")

    2. Compound name  "<alias>:<arg1>:<arg2>:...":
         build_chart("heatmap:2024:L")        -> matrix_heatmap(year=2024, matrix="L")
         build_chart("heatmap:2024:L:15")     -> matrix_heatmap(year=2024, matrix="L", agg="15")
         build_chart("mult_bar:2024")         -> multiplier_bar(year=2024)
         build_chart("mult_bar:2024:20")      -> multiplier_bar(year=2024, n=20)

       Args named "year" or "n" are cast to int; all others kept as strings.

    Raises
    ------
    ValueError if the key (or alias) is not found.
    """
    # Integer-cast arg names (year, n are always integers; everything else is str)
    _INT_ARG_NAMES = {"year", "n"}

    # 0. Study charts — key form "study:<slug>:<figname>"
    #    Handled BEFORE the generic compound parsing so that slugs containing
    #    hyphens (e.g. "key-sectors") are never misread as alias + args.
    if chart_key.startswith("study:"):
        parts = chart_key.split(":", 2)
        if len(parts) != 3:
            raise ValueError(
                f"Study chart key must have the form 'study:<slug>:<figname>', "
                f"got {chart_key!r}."
            )
        _, slug, figname = parts
        return _build_study_chart(slug, figname)

    # 1. Direct registry hit (plain name, no colon parsing)
    if chart_key in CHART_REGISTRY and not params:
        return CHART_REGISTRY[chart_key]()

    if ":" in chart_key:
        parts = chart_key.split(":")
        alias = parts[0]
        raw_args = parts[1:]

        # Resolve alias -> builder name
        if alias in _COMPOUND_ALIASES:
            builder_name, arg_names = _COMPOUND_ALIASES[alias]
        elif alias in CHART_REGISTRY:
            # Allow full builder name as alias with colon-args (best effort)
            # e.g. "matrix_heatmap:2024:L"
            builder_name = alias
            arg_names = ["year", "matrix", "agg", "n", "key", "columns"]
        else:
            raise ValueError(
                f"Unknown chart alias {alias!r}. "
                f"Available registry keys: {list(CHART_REGISTRY.keys())}. "
                f"Available compound aliases: {list(_COMPOUND_ALIASES.keys())}."
            )

        # Map positional args to parameter names.
        # Only cast to int for args in _INT_ARG_NAMES; everything else is a string.
        colon_params: dict[str, Any] = {}
        for name, raw in zip(arg_names, raw_args):
            if name in _INT_ARG_NAMES and raw.lstrip("-").isdigit():
                colon_params[name] = int(raw)
            else:
                colon_params[name] = raw

        # Merge: colon_params take precedence over **params
        merged = {**colon_params, **params}
        return CHART_REGISTRY[builder_name](**merged)

    # 2. Plain registry name with params
    if chart_key in CHART_REGISTRY:
        return CHART_REGISTRY[chart_key](**params)

    raise ValueError(
        f"Unknown chart key {chart_key!r}. "
        f"Available registry keys: {list(CHART_REGISTRY.keys())}. "
        f"Compound alias format: '<alias>:<arg1>:<arg2>...' "
        f"(aliases: {list(_COMPOUND_ALIASES.keys())})."
    )
