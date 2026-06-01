"""Key Sectors: Rasmussen backward and forward linkage indices.

Reads:
    ./data/L_2024.csv   — 71x71 Leontief inverse, year 2024
    ./data/L_2002.csv   — 71x71 Leontief inverse, year 2002
    ./data/sector_names.csv — code -> name mapping

Writes:
    ./outputs/linkages_2024.csv
    ./outputs/fig_linkage_scatter.json
    ./outputs/fig_key_sectors_bar.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_L(path: Path) -> pd.DataFrame:
    """Load a Leontief inverse CSV (index in first column)."""
    df = pd.read_csv(path, index_col=0)
    return df


def rasmussen_indices(L: pd.DataFrame) -> pd.DataFrame:
    """Compute Rasmussen backward and forward linkage indices.

    Backward linkage (power of dispersion):
        BL_j = mean(L[:, j]) / grand_mean(L)
             = (column sum / n) / (total sum / n^2)
             = n * col_sum / total_sum

    Forward linkage (sensitivity of dispersion):
        FL_i = mean(L[i, :]) / grand_mean(L)
             = n * row_sum / total_sum

    By construction both sets have simple average = 1.
    """
    n = len(L)
    L_arr = L.values.astype(float)
    grand_mean = L_arr.mean()
    col_means = L_arr.mean(axis=0)   # one per sector j (backward)
    row_means = L_arr.mean(axis=1)   # one per sector i (forward)
    BL = col_means / grand_mean
    FL = row_means / grand_mean
    codes = list(L.columns)
    return pd.DataFrame({"code": codes, "BL": BL, "FL": FL})


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
names_df = pd.read_csv(DATA / "sector_names.csv")
names = dict(zip(names_df["code"], names_df["name"]))

L24 = load_L(DATA / "L_2024.csv")
L02 = load_L(DATA / "L_2002.csv")

idx24 = rasmussen_indices(L24)
idx02 = rasmussen_indices(L02)

# Merge names
idx24["name"] = idx24["code"].map(names).fillna(idx24["code"])
idx02["name"] = idx02["code"].map(names).fillna(idx02["code"])

# Key sector flag: both BL and FL > 1
idx24["is_key"] = (idx24["BL"] > 1) & (idx24["FL"] > 1)
idx02["is_key"] = (idx02["BL"] > 1) & (idx02["FL"] > 1)

# ---------------------------------------------------------------------------
# Save linkages_2024.csv
# ---------------------------------------------------------------------------
out_df = idx24[["code", "name", "BL", "FL", "is_key"]].copy()
out_df.columns = ["sector", "name", "backward", "forward", "is_key"]
out_df = out_df.sort_values("backward", ascending=False).reset_index(drop=True)
out_df.to_csv(OUT / "linkages_2024.csv", index=False)

# ---------------------------------------------------------------------------
# Summary stats (printed at end)
# ---------------------------------------------------------------------------
n_key_24 = idx24["is_key"].sum()
n_key_02 = idx02["is_key"].sum()

top5_bl = idx24.nlargest(5, "BL")[["name", "BL", "FL"]].to_string(index=False)

# ---------------------------------------------------------------------------
# Figure 1: Linkage scatter (2024) — BL vs FL, quadrant lines at 1.0
# ---------------------------------------------------------------------------
colors = ["#e74c3c" if k else "#aab7c4" for k in idx24["is_key"]]

fig_scatter = go.Figure()

# Non-key sectors
mask_nk = ~idx24["is_key"]
fig_scatter.add_trace(go.Scatter(
    x=idx24.loc[mask_nk, "BL"],
    y=idx24.loc[mask_nk, "FL"],
    mode="markers",
    marker=dict(size=8, color="#aab7c4", opacity=0.7),
    text=idx24.loc[mask_nk, "name"],
    customdata=idx24.loc[mask_nk, ["code", "BL", "FL"]].values,
    hovertemplate=(
        "<b>%{text}</b><br>"
        "Backward: %{x:.3f}<br>"
        "Forward: %{y:.3f}<extra></extra>"
    ),
    name="Other sectors",
))

# Key sectors
mask_k = idx24["is_key"]
fig_scatter.add_trace(go.Scatter(
    x=idx24.loc[mask_k, "BL"],
    y=idx24.loc[mask_k, "FL"],
    mode="markers+text",
    marker=dict(size=11, color="#e74c3c", opacity=0.9),
    text=idx24.loc[mask_k, "name"],
    textposition="top center",
    customdata=idx24.loc[mask_k, ["code", "BL", "FL"]].values,
    hovertemplate=(
        "<b>%{text}</b><br>"
        "Backward: %{x:.3f}<br>"
        "Forward: %{y:.3f}<extra></extra>"
    ),
    name="Key sector (BL>1 & FL>1)",
))

# Quadrant lines
fig_scatter.add_shape(type="line", x0=1, x1=1,
                      y0=idx24["FL"].min() - 0.05,
                      y1=idx24["FL"].max() + 0.05,
                      line=dict(color="#555", width=1, dash="dot"))
fig_scatter.add_shape(type="line", y0=1, y1=1,
                      x0=idx24["BL"].min() - 0.05,
                      x1=idx24["BL"].max() + 0.05,
                      line=dict(color="#555", width=1, dash="dot"))

fig_scatter.update_layout(
    title="Rasmussen Linkage Indices, 2024<br><sup>Red = key sectors (BL > 1 and FL > 1)</sup>",
    xaxis_title="Backward Linkage (Power of Dispersion)",
    yaxis_title="Forward Linkage (Sensitivity of Dispersion)",
    legend=dict(x=0.01, y=0.99),
    width=820, height=580,
    template="plotly_white",
)

fig_scatter_path = OUT / "fig_linkage_scatter.json"
with open(fig_scatter_path, "w", encoding="utf-8") as f:
    json.dump(fig_scatter.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Figure 2: Top-15 sectors by BL+FL, horizontal bar
# ---------------------------------------------------------------------------
idx24["combined"] = idx24["BL"] + idx24["FL"]
top15 = idx24.nlargest(15, "combined").sort_values("combined", ascending=True)

bar_colors = ["#e74c3c" if k else "#3498db" for k in top15["is_key"]]

fig_bar = go.Figure(go.Bar(
    x=top15["combined"],
    y=top15["name"],
    orientation="h",
    marker_color=bar_colors,
    customdata=top15[["BL", "FL"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Backward: %{customdata[0]:.3f}<br>"
        "Forward: %{customdata[1]:.3f}<br>"
        "Combined: %{x:.3f}<extra></extra>"
    ),
))

fig_bar.update_layout(
    title="Top 15 Sectors by Combined Linkage (BL + FL), 2024<br><sup>Red = key sectors; blue = above average on combined but not both indices</sup>",
    xaxis_title="Backward Linkage + Forward Linkage",
    yaxis_title="",
    width=820, height=520,
    template="plotly_white",
    xaxis=dict(range=[0, top15["combined"].max() * 1.1]),
)

# Add reference line at 2.0 (both = 1.0)
fig_bar.add_vline(x=2.0, line_dash="dot", line_color="#555",
                  annotation_text="avg=1 baseline (sum=2)", annotation_position="top")

fig_bar_path = OUT / "fig_key_sectors_bar.json"
with open(fig_bar_path, "w", encoding="utf-8") as f:
    json.dump(fig_bar.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 60)
print("KEY SECTORS — Rasmussen Linkage Indices")
print("=" * 60)
print(f"\n2024: {n_key_24} key sectors (BL>1 and FL>1)")
print(f"2002: {n_key_02} key sectors (BL>1 and FL>1)")
print(f"\nTop 5 by backward linkage (2024):")
print(top5_bl)
print(f"\nTop combined linkage sector (2024): {idx24.nlargest(1, 'combined').iloc[0]['name']}")
print(f"  BL={idx24.nlargest(1,'combined').iloc[0]['BL']:.3f}, FL={idx24.nlargest(1,'combined').iloc[0]['FL']:.3f}")
print(f"\nOutputs written to: {OUT}")
print(f"  linkages_2024.csv — {len(out_df)} rows")
print(f"  fig_linkage_scatter.json — scatter BL vs FL (2024)")
print(f"  fig_key_sectors_bar.json — top-15 combined bar")
