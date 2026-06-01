"""Cost-push prices and the wage share.

Implements the price dual of the Leontief quantity model:
    p = v @ (I - A)^{-1}

Where v = unit value added (compensation + gross operating surplus per unit
gross output) — the 'primary factor' cost per dollar of output.

Demonstrates:
1. A +10% wage-shock and its sectoral price pass-through effects (Delta p).
2. Economy-wide labor share trend, 1997-2024.

Reads (from ./data/):
    A_square_2024.csv   — 68x68 technical-coefficients matrix (A_square)
    value_added_2024.csv — rows V001/V003/VABAS/VAPRO x 68 sectors
    total_output_2024.csv — gross output by sector, 2024
    labor_share.csv      — economy-wide labor share 1997-2024
    sector_names.csv     — code → name mapping

Writes (to ./outputs/):
    prices.csv                  — baseline prices, shocked prices, Delta p per sector
    fig_price_passthrough.json  — bar chart: top-15 sectors by price increase
    fig_labor_share_trend.json  — line chart: labor share 1997-2024
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

A = pd.read_csv(DATA / "A_square_2024.csv", index_col=0)
sectors = list(A.index)
n = len(sectors)

VA_raw = pd.read_csv(DATA / "value_added_2024.csv", index_col=0)
VA = VA_raw[sectors]  # align columns

x_df = pd.read_csv(DATA / "total_output_2024.csv", index_col=0)
x = x_df["total_output"].reindex(sectors).fillna(0)

ls_df = pd.read_csv(DATA / "labor_share.csv")

# ---------------------------------------------------------------------------
# Build per-unit value-added vector v
# v_j = (VA_j) / x_j   — total unit value added per sector
# where VA_j = V001_j + V003_j  (compensation + gross op surplus)
# Using VABAS (basic-price value added) = V001 + V003 + T00SUB - T00TOP
# We use V001 + V003 directly for transparency.
# ---------------------------------------------------------------------------
v001 = VA.loc["V001"]   # compensation (million $)
v003 = VA.loc["V003"]   # gross operating surplus (million $)

# Per-unit: divide by gross output
x_safe = x.replace(0, np.nan)
comp_coeff = (v001 / x_safe).fillna(0)   # compensation per dollar output
gos_coeff = (v003 / x_safe).fillna(0)    # GOS per dollar output

# Total unit value added
v = comp_coeff + gos_coeff   # shape (n,)

# Sanity: v @ (I - A)^{-1} should give prices close to 1 if accounting holds
# (In practice they won't be exactly 1 because BEA VA also includes taxes/subsidies
# not captured in V001+V003, but the ratio across sectors is economically meaningful.)

# ---------------------------------------------------------------------------
# Leontief inverse (no scipy: use numpy.linalg)
# ---------------------------------------------------------------------------
I_n = np.eye(n)
L = np.linalg.inv(I_n - A.values.astype(float))   # (I - A)^{-1}

# ---------------------------------------------------------------------------
# Baseline price vector: p = v @ L
# ---------------------------------------------------------------------------
v_arr = v.values
p_base = v_arr @ L   # shape (n,)

# ---------------------------------------------------------------------------
# Wage shock: +10% on compensation component
# Delta_v = 0.10 * comp_coeff   (only the compensation row shocked)
# Delta_p = Delta_v @ L
# ---------------------------------------------------------------------------
delta_v = 0.10 * comp_coeff.values
delta_p = delta_v @ L   # absolute change in price (same units as p_base)

# Percentage change: delta_p / p_base * 100
p_base_safe = np.where(p_base != 0, p_base, np.nan)
delta_p_pct = delta_p / p_base_safe * 100

p_shocked = p_base + delta_p

# ---------------------------------------------------------------------------
# Assemble results table
# ---------------------------------------------------------------------------
sector_name_list = [names.get(s, s) for s in sectors]

prices_df = pd.DataFrame({
    "sector": sectors,
    "name": sector_name_list,
    "comp_coeff": comp_coeff.values,
    "gos_coeff": gos_coeff.values,
    "v_total": v_arr,
    "price_base": p_base,
    "price_shocked": p_shocked,
    "delta_p": delta_p,
    "delta_p_pct": np.where(np.isnan(delta_p_pct), 0.0, delta_p_pct),
})
prices_df = prices_df.sort_values("delta_p_pct", ascending=False).reset_index(drop=True)
prices_df.to_csv(OUT / "prices.csv", index=False)

# ---------------------------------------------------------------------------
# Figure 1: fig_price_passthrough — top-15 sectors by price increase (%)
# ---------------------------------------------------------------------------
top15 = prices_df.head(15).sort_values("delta_p_pct", ascending=True)

# Color gradient: higher = deeper red
max_pct = top15["delta_p_pct"].max()
min_pct = top15["delta_p_pct"].min()

fig_pt = go.Figure(go.Bar(
    x=top15["delta_p_pct"],
    y=top15["name"],
    orientation="h",
    marker=dict(
        color=top15["delta_p_pct"],
        colorscale="Reds",
        cmin=min_pct * 0.9,
        cmax=max_pct * 1.05,
        colorbar=dict(title="Price change (%)"),
    ),
    customdata=top15[["comp_coeff", "gos_coeff", "delta_p_pct"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Comp. coeff: %{customdata[0]:.4f}<br>"
        "GOS coeff: %{customdata[1]:.4f}<br>"
        "Price change: +%{x:.3f}%<extra></extra>"
    ),
))

fig_pt.update_layout(
    title=(
        "Top 15 Sectors by Cost-Push Price Increase<br>"
        "<sup>+10% wage shock on compensation component of unit value added, 2024</sup>"
    ),
    xaxis_title="Price change (%) from +10% wage shock",
    yaxis_title="",
    template="plotly_white",
    width=820,
    height=520,
    margin=dict(l=240),
)

fig_pt_path = OUT / "fig_price_passthrough.json"
with open(fig_pt_path, "w", encoding="utf-8") as f:
    json.dump(fig_pt.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Figure 2: fig_labor_share_trend — economy-wide labor share 1997-2024
# ---------------------------------------------------------------------------
ls_df = ls_df.sort_values("year")

fig_ls = go.Figure()
fig_ls.add_trace(go.Scatter(
    x=ls_df["year"],
    y=ls_df["labor_share"] * 100,
    mode="lines+markers",
    line=dict(color="#2c7bb6", width=2.5),
    marker=dict(size=6, color="#2c7bb6"),
    name="Labor share (%)",
    hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra></extra>",
))

# Shade 2008-2009 recession
fig_ls.add_vrect(
    x0=2007.5, x1=2009.5,
    fillcolor="#f0a500", opacity=0.12,
    layer="below", line_width=0,
    annotation_text="GFC", annotation_position="top left",
)
# Shade 2020 COVID
fig_ls.add_vrect(
    x0=2019.5, x1=2020.5,
    fillcolor="#e74c3c", opacity=0.12,
    layer="below", line_width=0,
    annotation_text="COVID", annotation_position="top left",
)

fig_ls.update_layout(
    title=(
        "Economy-Wide Labor Share of Value Added, 1997–2024<br>"
        "<sup>V001 (compensation) / (V001 + V003), BEA I-O tables</sup>"
    ),
    xaxis_title="Year",
    yaxis_title="Labor share of VA (%)",
    template="plotly_white",
    width=820,
    height=440,
    yaxis=dict(range=[50, 70]),
)

fig_ls_path = OUT / "fig_labor_share_trend.json"
with open(fig_ls_path, "w", encoding="utf-8") as f:
    json.dump(fig_ls.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("PRICES AND DISTRIBUTION — Cost-push price model")
print("=" * 65)
print(f"\nSectors (A_square): {n}")
print(f"Wage shock: +10% on compensation component of unit value added")
print()
print("Top 10 sectors by price increase (% change):")
for _, row in prices_df.head(10).iterrows():
    print(f"  {row['name'][:40]:40s}  +{row['delta_p_pct']:.4f}%")

print()
print(f"Economy-wide mean price change: +{delta_p_pct[~np.isnan(delta_p_pct)].mean():.4f}%")
print(f"Max price change: +{prices_df['delta_p_pct'].max():.4f}% ({prices_df.iloc[0]['name']})")

# Labor share at end-points
yr_1997 = ls_df[ls_df["year"] == 1997]["labor_share"].values
yr_2024 = ls_df[ls_df["year"] == 2024]["labor_share"].values
if len(yr_1997) and len(yr_2024):
    print(f"\nLabor share: {yr_1997[0]*100:.1f}% (1997) → {yr_2024[0]*100:.1f}% (2024)")

print(f"\nOutputs written to: {OUT}")
print(f"  prices.csv — {len(prices_df)} rows")
print(f"  fig_price_passthrough.json — top-15 bar chart")
print(f"  fig_labor_share_trend.json — labor share trend 1997-2024")
