"""Supply Chains as Networks: eigenvector centrality and strength in the 2024 A-matrix.

Treats A_square (2024) as a directed weighted adjacency matrix.
  A[i,j] = input from sector i per dollar of sector j's output
  => edge from i to j with weight A[i,j]

Computes (numpy only — no networkx/scipy):
  - Eigenvector centrality via power iteration on A (dominant right eigenvector)
  - In-strength  = column sums of A  (how much each sector buys from others)
  - Out-strength = row sums of A     (how much each sector sells to others)

Reads:
    ./data/A_square_2024.csv   — 68x68 commodity-by-commodity A matrix
    ./data/sector_agg15.csv    — code, name, agg15 group
    ./data/sector_names.csv    — code, name (backup)

Writes:
    ./outputs/centrality_2024.csv         — per-sector centrality + strength
    ./outputs/fig_centrality.json         — top-15 by eigenvector centrality (bar)
    ./outputs/fig_strength_scatter.json   — in-strength vs out-strength scatter, colored by agg15
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
A = pd.read_csv(DATA / "A_square_2024.csv", index_col=0)
sectors = pd.read_csv(DATA / "sector_agg15.csv")

codes = list(A.index)
n = len(codes)
Arr = A.values.astype(float)

code2name = dict(zip(sectors["code"], sectors["name"]))
code2agg15 = dict(zip(sectors["code"], sectors["agg15"]))

# ---------------------------------------------------------------------------
# In-strength and out-strength
# ---------------------------------------------------------------------------
# A[i,j] = fraction of sector j's output purchased from sector i as intermediate input.
# In-strength of j  = col_sum(A[:, j]) = share of j's output that is intermediate inputs
# Out-strength of i = row_sum(A[i, :]) = total intermediate demand i supplies across all sectors
in_strength = Arr.sum(axis=0)    # shape (n,)  — one per buying sector (column)
out_strength = Arr.sum(axis=1)   # shape (n,)  — one per selling sector (row)

# ---------------------------------------------------------------------------
# Eigenvector centrality via power iteration on A
# ---------------------------------------------------------------------------
# The dominant right eigenvector of A satisfies A v = lambda_max v.
# In an adjacency interpretation where A[i,j] is an edge from i to j,
# the right eigenvector assigns high centrality to sectors that receive
# large flows from other highly-central sectors — the "downstream hub" perspective.
# This corresponds to the Acemoglu et al. (2012) influence vector when
# the matrix is column-stochastic (here A is not exactly, but the leading
# eigenvector still captures the network's principal flow direction).

# Power iteration: v <- A v / ||A v||, until convergence
v = np.ones(n, dtype=float) / n
for iteration in range(2000):
    v_new = Arr @ v
    norm = np.linalg.norm(v_new)
    if norm < 1e-14:
        break
    v_new /= norm
    if np.linalg.norm(v_new - v) < 1e-12:
        break
    v = v_new

# Normalise to [0, 1] for readability
centrality = np.abs(v)
centrality = centrality / centrality.max()

# Dominant eigenvalue estimate (Rayleigh quotient)
lambda_est = float((Arr @ v) @ v / (v @ v))

# ---------------------------------------------------------------------------
# Assemble results DataFrame
# ---------------------------------------------------------------------------
df = pd.DataFrame({
    "sector_code": codes,
    "name": [code2name.get(c, c) for c in codes],
    "agg15": [code2agg15.get(c, "Other") for c in codes],
    "eigenvector_centrality": centrality,
    "in_strength": in_strength,
    "out_strength": out_strength,
})
df = df.sort_values("eigenvector_centrality", ascending=False).reset_index(drop=True)
df.to_csv(OUT / "centrality_2024.csv", index=False)

# ---------------------------------------------------------------------------
# Figure 1: Top-15 by eigenvector centrality (horizontal bar)
# ---------------------------------------------------------------------------
top15 = df.head(15).sort_values("eigenvector_centrality", ascending=True)

# Colour bars by agg15 group (consistent palette)
agg15_palette = {
    "Agriculture":                    "#27ae60",
    "Mining":                         "#8e44ad",
    "Utilities":                      "#f39c12",
    "Construction":                   "#e67e22",
    "Manufacturing":                  "#2980b9",
    "Wholesale Trade":                "#16a085",
    "Retail Trade":                   "#1abc9c",
    "Transportation & Warehousing":   "#d35400",
    "Information":                    "#9b59b6",
    "Finance, Insurance & Real Estate": "#c0392b",
    "Professional & Business Services": "#2c3e50",
    "Education & Health":             "#27ae60",
    "Arts, Accommodation & Food":     "#f1c40f",
    "Other Services":                 "#95a5a6",
    "Government":                     "#7f8c8d",
}

bar_colors_c = [agg15_palette.get(g, "#aab7c4") for g in top15["agg15"]]

fig_centrality = go.Figure(go.Bar(
    x=top15["eigenvector_centrality"],
    y=top15["name"],
    orientation="h",
    marker_color=bar_colors_c,
    customdata=top15[["agg15", "in_strength", "out_strength"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Group: %{customdata[0]}<br>"
        "Eigenvector centrality: %{x:.4f}<br>"
        "In-strength: %{customdata[1]:.4f}<br>"
        "Out-strength: %{customdata[2]:.4f}<extra></extra>"
    ),
))

fig_centrality.update_layout(
    title=(
        "Top 15 Sectors by Eigenvector Centrality, 2024<br>"
        "<sup>Power iteration on 68×68 A-matrix; "
        "colour = broad sector group (agg15)</sup>"
    ),
    xaxis_title="Eigenvector centrality (normalised to 1)",
    yaxis_title="",
    template="plotly_white",
    width=820,
    height=500,
    margin=dict(l=320),
)

with open(OUT / "fig_centrality.json", "w", encoding="utf-8") as f:
    json.dump(fig_centrality.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Figure 2: In-strength vs Out-strength scatter (colored by agg15)
# ---------------------------------------------------------------------------
agg15_groups = df["agg15"].unique().tolist()

fig_scatter = go.Figure()

for group in sorted(agg15_groups):
    mask = df["agg15"] == group
    sub = df[mask]
    fig_scatter.add_trace(go.Scatter(
        x=sub["in_strength"],
        y=sub["out_strength"],
        mode="markers",
        name=group,
        marker=dict(
            size=10,
            color=agg15_palette.get(group, "#aab7c4"),
            opacity=0.85,
        ),
        text=sub["name"],
        customdata=sub[["sector_code", "eigenvector_centrality"]].values,
        hovertemplate=(
            "<b>%{text}</b> (%{customdata[0]})<br>"
            "In-strength (buyer): %{x:.4f}<br>"
            "Out-strength (seller): %{y:.4f}<br>"
            "Centrality: %{customdata[1]:.4f}<extra></extra>"
        ),
    ))

# Diagonal reference line (in = out)
max_val = max(df["in_strength"].max(), df["out_strength"].max()) * 1.05
fig_scatter.add_shape(
    type="line", x0=0, y0=0, x1=max_val, y1=max_val,
    line=dict(color="#bbb", width=1, dash="dot"),
)
fig_scatter.add_annotation(
    x=max_val * 0.55, y=max_val * 0.55,
    text="in = out",
    showarrow=False,
    font=dict(size=10, color="#888"),
    textangle=-45,
)

fig_scatter.update_layout(
    title=(
        "Supply-Chain Position: In-Strength vs Out-Strength, 2024<br>"
        "<sup>In-strength = column sum of A (intermediate-input share of output); "
        "Out-strength = row sum (sales as intermediate to all sectors); "
        "colour = agg15 group</sup>"
    ),
    xaxis_title="In-strength (buys inputs from the economy)",
    yaxis_title="Out-strength (sells to the economy as intermediate)",
    legend=dict(x=1.01, y=1, xanchor="left", font=dict(size=10)),
    template="plotly_white",
    width=900,
    height=600,
)

with open(OUT / "fig_strength_scatter.json", "w", encoding="utf-8") as f:
    json.dump(fig_scatter.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("SUPPLY CHAINS NETWORK — Summary (2024)")
print("=" * 65)
print(f"\nA-matrix shape        : {Arr.shape}")
print(f"Dominant eigenvalue   : {lambda_est:.6f}")
print(f"\nTop 10 by eigenvector centrality:")
top10 = df.head(10)[["sector_code", "name", "eigenvector_centrality", "in_strength", "out_strength"]]
print(top10.to_string(index=False))
print(f"\nTop 5 by out-strength (biggest intermediate sellers):")
top5_out = df.sort_values("out_strength", ascending=False).head(5)[
    ["sector_code", "name", "out_strength"]
]
print(top5_out.to_string(index=False))
print(f"\nTop 5 by in-strength (biggest intermediate buyers, share of output):")
top5_in = df.sort_values("in_strength", ascending=False).head(5)[
    ["sector_code", "name", "in_strength"]
]
print(top5_in.to_string(index=False))
print(f"\nOutputs written to: {OUT}")
print(f"  centrality_2024.csv         — {len(df)} rows")
print(f"  fig_centrality.json         — top-15 eigenvector centrality bar")
print(f"  fig_strength_scatter.json   — in vs out strength scatter")
