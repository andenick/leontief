"""Multipliers Explained: Output multiplier distribution and trend 1997-2024.

Reads:
    ./data/L_2024.csv                  — 71x71 Leontief inverse, year 2024
    ./data/multiplier_timeseries.csv   — year + 71 sector columns (precomputed output multipliers)
    ./data/sector_names.csv            — code -> name mapping

Writes:
    ./outputs/multipliers_2024.csv
    ./outputs/fig_mult_rank_2024.json
    ./outputs/fig_mult_trend.json
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
names_df = pd.read_csv(DATA / "sector_names.csv")
names = dict(zip(names_df["code"], names_df["name"]))

# Leontief inverse 2024 — output multiplier = column sum
L24 = pd.read_csv(DATA / "L_2024.csv", index_col=0)
mult_2024 = L24.sum(axis=0).rename("multiplier")
mult_2024.index.name = "sector"
mult_2024 = mult_2024.reset_index()
mult_2024["name"] = mult_2024["sector"].map(names).fillna(mult_2024["sector"])
mult_2024 = mult_2024.sort_values("multiplier", ascending=False).reset_index(drop=True)
mult_2024["rank"] = mult_2024.index + 1

# Multiplier timeseries
ts = pd.read_csv(DATA / "multiplier_timeseries.csv")
ts["year"] = ts["year"].astype(int)
sector_cols = [c for c in ts.columns if c != "year"]
ts["mean_mult"] = ts[sector_cols].mean(axis=1)

# ---------------------------------------------------------------------------
# Save multipliers_2024.csv
# ---------------------------------------------------------------------------
out_df = mult_2024[["rank", "sector", "name", "multiplier"]].copy()
out_df.to_csv(OUT / "multipliers_2024.csv", index=False)

# ---------------------------------------------------------------------------
# Figure 1: Top & bottom 10 sectors by output multiplier, 2024
# ---------------------------------------------------------------------------
top10 = mult_2024.head(10).copy()
bot10 = mult_2024.tail(10).copy()
plot_df = pd.concat([top10, bot10]).drop_duplicates("sector")
# Sort for chart: top at top, bottom at bottom (ascending for horizontal bar)
plot_df = plot_df.sort_values("multiplier", ascending=True)

bar_colors = [
    "#e74c3c" if m >= mult_2024["multiplier"].mean() * 1.0 else "#3498db"
    for m in plot_df["multiplier"]
]
# Color by position: top 10 red, bottom 10 blue
color_list = ["#3498db"] * len(bot10) + ["#e74c3c"] * len(top10)

fig_rank = go.Figure(go.Bar(
    x=plot_df["multiplier"],
    y=plot_df["name"],
    orientation="h",
    marker_color=color_list,
    customdata=plot_df[["sector", "rank"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Output multiplier: %{x:.3f}<br>"
        "Rank: %{customdata[1]} of 71<extra></extra>"
    ),
))

mean_val = mult_2024["multiplier"].mean()
fig_rank.add_vline(
    x=mean_val,
    line_dash="dot", line_color="#555",
    annotation_text=f"Mean: {mean_val:.3f}",
    annotation_position="top",
)

fig_rank.update_layout(
    title="Output Multipliers, 2024: Top 10 and Bottom 10 Sectors<br><sup>Red = top 10 (high pull); Blue = bottom 10 (low pull)</sup>",
    xaxis_title="Output Multiplier $\\sum_i L_{ij}$",
    yaxis_title="",
    width=820, height=560,
    template="plotly_white",
)

fig_rank_path = OUT / "fig_mult_rank_2024.json"
with open(fig_rank_path, "w", encoding="utf-8") as f:
    json.dump(fig_rank.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Figure 2: Mean output multiplier per year, 1997-2024
# ---------------------------------------------------------------------------
fig_trend = go.Figure(go.Scatter(
    x=ts["year"],
    y=ts["mean_mult"],
    mode="lines+markers",
    marker=dict(size=5, color="#2980b9"),
    line=dict(width=2, color="#2980b9"),
    hovertemplate="<b>%{x}</b><br>Mean multiplier: %{y:.3f}<extra></extra>",
    name="Economy mean",
))

peak_yr = int(ts.loc[ts["mean_mult"].idxmax(), "year"])
peak_val = ts["mean_mult"].max()
fig_trend.add_annotation(
    x=peak_yr, y=peak_val,
    text=f"Peak: {peak_val:.3f} ({peak_yr})",
    showarrow=True, arrowhead=2, ay=-30, ax=20,
    font=dict(size=11),
)

latest_yr = int(ts["year"].max())
latest_val = float(ts.loc[ts["year"] == latest_yr, "mean_mult"].iloc[0])
fig_trend.add_annotation(
    x=latest_yr, y=latest_val,
    text=f"{latest_yr}: {latest_val:.3f}",
    showarrow=True, arrowhead=2, ay=-30, ax=-30,
    font=dict(size=11),
)

fig_trend.update_layout(
    title="Economy-wide Mean Output Multiplier, 1997–2024<br><sup>Average of 71 sector output multipliers each year</sup>",
    xaxis_title="Year",
    yaxis_title="Mean Output Multiplier",
    width=820, height=460,
    template="plotly_white",
    xaxis=dict(dtick=3),
)

fig_trend_path = OUT / "fig_mult_trend.json"
with open(fig_trend_path, "w", encoding="utf-8") as f:
    json.dump(fig_trend.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 60)
print("MULTIPLIERS EXPLAINED — Output Multiplier Analysis")
print("=" * 60)
print(f"\n2024 output multipliers (71 sectors):")
print(f"  Economy mean:    {mean_val:.3f}")
print(f"  Maximum:         {mult_2024['multiplier'].max():.3f}  ({mult_2024.iloc[0]['name']})")
print(f"  Minimum:         {mult_2024['multiplier'].min():.3f}  ({mult_2024.iloc[-1]['name']})")
print(f"\nHistorical trend (mean multiplier):")
print(f"  1997:  {ts.loc[ts['year']==1997, 'mean_mult'].iloc[0]:.3f}")
print(f"  Peak:  {peak_val:.3f}  (year {peak_yr})")
print(f"  2024:  {latest_val:.3f}")
print(f"\nOutputs written to: {OUT}")
print(f"  multipliers_2024.csv       — {len(out_df)} rows")
print(f"  fig_mult_rank_2024.json    — top/bottom 10 bar chart")
print(f"  fig_mult_trend.json        — mean trend 1997-2024")
