"""COVID Structural Shift: how the pandemic bent the input-output structure.

Reads:
    ./data/structural_change.csv   — year-pair metrics (cosine_similarity,
                                     absolute_change, lilien_index) 1997-2024
    ./data/covid_sector_shift.csv  — sector-level 2019->2020 displacement

Writes:
    ./outputs/structural_change.csv   — annotated metrics with structural_distance
    ./outputs/fig_covid_shift.json    — Plotly line chart: structural distance by year-pair
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
sc = pd.read_csv(DATA / "structural_change.csv")
sector_shift = pd.read_csv(DATA / "covid_sector_shift.csv")

# ---------------------------------------------------------------------------
# Derived metric: structural distance = 1 - cosine_similarity
# ---------------------------------------------------------------------------
sc["structural_distance"] = 1.0 - sc["cosine_similarity"]

# Label for x-axis: "1997-98", "1998-99", …
sc["label"] = sc["year_from"].astype(str) + "–" + sc["year_to"].astype(str).str[-2:]

# Flag the pandemic biennium and GFC
sc["is_covid"] = sc["year_from"].isin([2019, 2020])
sc["is_gfc"] = sc["year_from"] == 2008

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
typical = sc[~sc["year_from"].isin([2008, 2019, 2020])]
typical_mean_dist = typical["structural_distance"].mean()
typical_mean_lilien = typical["lilien_index"].mean()
typical_mean_abs = typical["absolute_change"].mean()

covid_row = sc[sc["year_from"] == 2019].iloc[0]
rebound_row = sc[sc["year_from"] == 2020].iloc[0]
gfc_row = sc[sc["year_from"] == 2008].iloc[0]

# ---------------------------------------------------------------------------
# Save annotated CSV
# ---------------------------------------------------------------------------
sc_out = sc[["year_from", "year_to", "cosine_similarity", "structural_distance",
             "absolute_change", "lilien_index"]].copy()
sc_out.to_csv(OUT / "structural_change.csv", index=False)

# ---------------------------------------------------------------------------
# Figure: structural distance by year-pair (line + highlighted bars)
# ---------------------------------------------------------------------------

# Colour each bar: COVID years orange, GFC red, normal grey
bar_colors = []
for _, row in sc.iterrows():
    if row["is_covid"]:
        bar_colors.append("#e67e22")   # orange — COVID
    elif row["is_gfc"]:
        bar_colors.append("#c0392b")   # red — GFC
    else:
        bar_colors.append("#aab7c4")   # grey — normal

# Hover text
hover_texts = []
for _, row in sc.iterrows():
    tag = ""
    if row["is_covid"]:
        tag = " [COVID]"
    elif row["is_gfc"]:
        tag = " [GFC]"
    hover_texts.append(
        f"<b>{row['label']}{tag}</b><br>"
        f"Structural distance: {row['structural_distance']:.5f}<br>"
        f"Lilien index: {row['lilien_index']:.4f}<br>"
        f"Mean |Δa|: {row['absolute_change']:.6f}"
    )

fig = go.Figure()

# Bar trace — structural distance
fig.add_trace(go.Bar(
    x=sc["label"],
    y=sc["structural_distance"],
    marker_color=bar_colors,
    hovertext=hover_texts,
    hoverinfo="text",
    name="Structural distance (1 − cosine)",
))

# Lilien index as a secondary line (right y-axis)
fig.add_trace(go.Scatter(
    x=sc["label"],
    y=sc["lilien_index"],
    mode="lines+markers",
    name="Lilien index",
    line=dict(color="#2980b9", width=1.5, dash="dot"),
    marker=dict(size=4),
    yaxis="y2",
    hoverinfo="skip",
))

# Average structural distance line (typical years)
fig.add_hline(
    y=typical_mean_dist,
    line_dash="dash",
    line_color="#555",
    annotation_text=f"Typical-year mean ({typical_mean_dist:.4f})",
    annotation_position="top left",
    annotation_font_size=11,
)

# Annotations for COVID and GFC bars
fig.add_annotation(
    x="2019–20",
    y=covid_row["structural_distance"] + 0.0003,
    text="COVID<br>2019→20",
    showarrow=False,
    font=dict(size=10, color="#e67e22"),
    align="center",
)
fig.add_annotation(
    x="2020–21",
    y=rebound_row["structural_distance"] + 0.0003,
    text="Rebound<br>2020→21",
    showarrow=False,
    font=dict(size=10, color="#e67e22"),
    align="center",
)
fig.add_annotation(
    x="2008–09",
    y=gfc_row["structural_distance"] + 0.0003,
    text="GFC<br>2008→09",
    showarrow=False,
    font=dict(size=10, color="#c0392b"),
    align="center",
)

fig.update_layout(
    title=(
        "Structural Change in the U.S. Input-Output Table, 1997–2024<br>"
        "<sup>Bars = 1 − cosine similarity of consecutive A-matrices; "
        "orange = COVID biennium, red = GFC; dotted = Lilien index (right axis)</sup>"
    ),
    xaxis=dict(
        title="Year pair",
        tickangle=-45,
        tickfont=dict(size=10),
    ),
    yaxis=dict(
        title="Structural distance (1 − cosine similarity)",
        rangemode="tozero",
    ),
    yaxis2=dict(
        title="Lilien index",
        overlaying="y",
        side="right",
        rangemode="tozero",
        showgrid=False,
    ),
    legend=dict(x=0.01, y=0.99),
    template="plotly_white",
    width=900,
    height=520,
    bargap=0.15,
)

fig_path = OUT / "fig_covid_shift.json"
with open(fig_path, "w", encoding="utf-8") as f:
    json.dump(fig.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("COVID STRUCTURAL SHIFT — Summary")
print("=" * 65)
print(f"\nTypical-year mean structural distance : {typical_mean_dist:.5f}")
print(f"2019→2020 structural distance          : {covid_row['structural_distance']:.5f}")
print(f"  Ratio vs typical                     : {covid_row['structural_distance']/typical_mean_dist:.2f}×")
print(f"2020→2021 structural distance          : {rebound_row['structural_distance']:.5f}")
print(f"  Ratio vs typical                     : {rebound_row['structural_distance']/typical_mean_dist:.2f}×")
print(f"\nGFC 2008→2009 structural distance      : {gfc_row['structural_distance']:.5f}")
print(f"  Ratio vs typical                     : {gfc_row['structural_distance']/typical_mean_dist:.2f}×")

print(f"\nLilien index — typical mean            : {typical_mean_lilien:.4f}")
print(f"Lilien index — 2019→2020               : {covid_row['lilien_index']:.4f}")
print(f"  Ratio                                : {covid_row['lilien_index']/typical_mean_lilien:.2f}×")

print(f"\nTop 5 sectors by total COVID displacement:")
top5 = sector_shift.nlargest(5, "total_change")[
    ["sector_code", "name", "change_as_buyer", "change_as_seller", "total_change"]
].reset_index(drop=True)
print(top5.to_string(index=False))

print(f"\nOutputs written to: {OUT}")
print(f"  structural_change.csv      — {len(sc_out)} rows")
print(f"  fig_covid_shift.json       — bar+line chart: structural distance by year-pair")
