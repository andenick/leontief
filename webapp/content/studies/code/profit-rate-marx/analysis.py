"""A Marxian profit rate from the input-output table.

Implements two classical-economics computations from BEA I-O data:

1. Labor values (vertically integrated labor coefficients), 2024:
       lambda = l @ (I - A)^{-1}
   where l = direct compensation per unit gross output (living-labor proxy).
   These give the total embodied labor content per sector.

2. Aggregate profit-rate proxy, 1997-2024:
       r = S / (C + V)
   where:
       V = total compensation (V001) — variable capital proxy
       S = gross operating surplus (V003) — surplus value proxy
       C = total intermediate inputs (Use T005) — constant capital FLOW proxy
   PROXY NOTE: C is a *flow* measure of intermediate inputs, NOT a fixed-capital
   stock. No capital-stock satellite data are available in the BEA I-O tables,
   so this is an approximation of Marx's C. The trend is informative; the level
   is not comparable to stock-based profit-rate estimates in the literature.

3. Value vs. market-price proxy scatter, 2024:
   Labor values (normalized) vs. market prices (VA-per-unit proxy, normalized).

Reads (from ./data/):
    A_square_2024.csv         — 68x68 A matrix
    value_added_2024.csv      — rows V001/V003/VABAS/VAPRO x 68 sectors
    total_output_2024.csv     — gross output by sector, 2024
    profit_rate_timeseries.csv — pre-computed V, S, C, r for 1997-2024
    sector_names.csv          — code → name mapping

Writes (to ./outputs/):
    marx.csv                     — per-sector: labor values, price proxy, 2024
    fig_profit_rate_trend.json   — line chart: aggregate profit-rate proxy 1997-2024
    fig_value_price_deviation.json — scatter: labor value vs price proxy (normalized)
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
# Load 2024 cross-section data
# ---------------------------------------------------------------------------
names_df = pd.read_csv(DATA / "sector_names.csv")
names = dict(zip(names_df["code"], names_df["name"]))

A = pd.read_csv(DATA / "A_square_2024.csv", index_col=0)
sectors = list(A.index)
n = len(sectors)

VA_raw = pd.read_csv(DATA / "value_added_2024.csv", index_col=0)
VA = VA_raw[sectors]

x_df = pd.read_csv(DATA / "total_output_2024.csv", index_col=0)
x = x_df["total_output"].reindex(sectors).fillna(0)

ts = pd.read_csv(DATA / "profit_rate_timeseries.csv")

# ---------------------------------------------------------------------------
# Labor coefficients: l_j = compensation_j / output_j
# (direct compensation per unit gross output — proxy for living labor per unit)
# ---------------------------------------------------------------------------
x_safe = x.replace(0, np.nan)
l = (VA.loc["V001"] / x_safe).fillna(0)   # vector of direct labor coefficients

# ---------------------------------------------------------------------------
# Leontief inverse (numpy only, no scipy)
# ---------------------------------------------------------------------------
I_n = np.eye(n)
L_inv = np.linalg.inv(I_n - A.values.astype(float))   # (I - A)^{-1}

# ---------------------------------------------------------------------------
# Labor values: lambda = l @ (I - A)^{-1}
# Each element lambda_j = total compensation embodied per unit of j's gross output.
# (Pasinetti's vertically integrated labor coefficients, interpreted as Marxian
# labor values when l proxies socially necessary labor time via compensation costs.)
# ---------------------------------------------------------------------------
lam = l.values @ L_inv   # shape (n,)

# ---------------------------------------------------------------------------
# Market price proxy: per-unit total value added
# p_j = (V001_j + V003_j) / x_j  — unit VA as price proxy
# This measures the 'primary factor cost' content of each dollar of output.
# ---------------------------------------------------------------------------
va_per_unit = ((VA.loc["V001"] + VA.loc["V003"]) / x_safe).fillna(0)

# ---------------------------------------------------------------------------
# Normalize both to mean = 1 for scatter comparison
# (Transformation problem: are sectors above/below their labor-value price?)
# ---------------------------------------------------------------------------
lam_safe = np.where(lam == 0, np.nan, lam)
lam_norm = lam / np.nanmean(lam_safe)

vap = va_per_unit.values
vap_safe = np.where(vap == 0, np.nan, vap)
vap_norm = vap / np.nanmean(vap_safe)

# Deviation: market price proxy relative to labor value
# Positive = sector's price > labor-value prediction (high profit-rate sector)
# Negative = sector's price < labor-value prediction (low profit-rate sector)
deviation_pct = np.where(
    lam_norm > 0,
    (vap_norm - lam_norm) / lam_norm * 100,
    np.nan,
)

# ---------------------------------------------------------------------------
# Assemble marx.csv
# ---------------------------------------------------------------------------
marx_df = pd.DataFrame({
    "sector": sectors,
    "name": [names.get(s, s) for s in sectors],
    "labor_coeff": l.values,
    "labor_value": lam,
    "labor_value_norm": lam_norm,
    "price_proxy_norm": vap_norm,
    "deviation_pct": np.nan_to_num(deviation_pct, nan=0.0),
})
marx_df = marx_df.sort_values("labor_value", ascending=False).reset_index(drop=True)
marx_df.to_csv(OUT / "marx.csv", index=False)

# ---------------------------------------------------------------------------
# Figure 1: fig_profit_rate_trend — aggregate profit-rate proxy 1997-2024
# ---------------------------------------------------------------------------
ts_valid = ts.dropna(subset=["r_flow_proxy"]).copy()

fig_pr = go.Figure()
fig_pr.add_trace(go.Scatter(
    x=ts_valid["year"],
    y=ts_valid["r_flow_proxy"],
    mode="lines+markers",
    line=dict(color="#c0392b", width=2.5),
    marker=dict(size=6, color="#c0392b"),
    name="r = S/(C+V) flow proxy",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "r (flow proxy): %{y:.4f}<extra></extra>"
    ),
))

# Add shading for major recessions
fig_pr.add_vrect(x0=2007.5, x1=2009.5, fillcolor="#f0a500", opacity=0.12,
                 layer="below", line_width=0,
                 annotation_text="GFC", annotation_position="top left")
fig_pr.add_vrect(x0=2019.5, x1=2020.5, fillcolor="#e74c3c", opacity=0.12,
                 layer="below", line_width=0,
                 annotation_text="COVID", annotation_position="top left")

fig_pr.update_layout(
    title=(
        "Aggregate Profit-Rate Proxy, 1997–2024<br>"
        "<sup>r = S/(C+V) — flow proxy; C = intermediate inputs (NOT capital stock). "
        "See study notes for caveats.</sup>"
    ),
    xaxis_title="Year",
    yaxis_title="r = S / (C + V)",
    template="plotly_white",
    width=820,
    height=460,
)

fig_pr_path = OUT / "fig_profit_rate_trend.json"
with open(fig_pr_path, "w", encoding="utf-8") as f:
    json.dump(fig_pr.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Figure 2: fig_value_price_deviation — scatter labor value vs price proxy
# ---------------------------------------------------------------------------
# Drop zeros/nans for cleaner scatter
valid_mask = (lam_norm > 0) & (vap_norm > 0) & ~np.isnan(lam_norm) & ~np.isnan(vap_norm)
sect_names_all = [names.get(s, s) for s in sectors]

# Color by deviation: red = price > value, blue = price < value
dev_arr = np.nan_to_num(deviation_pct, nan=0.0)

fig_vp = go.Figure()

# Reference line y=x (labor theory of value prediction)
vmin = min(lam_norm[valid_mask].min(), vap_norm[valid_mask].min()) * 0.9
vmax = max(lam_norm[valid_mask].max(), vap_norm[valid_mask].max()) * 1.1

fig_vp.add_shape(
    type="line", x0=vmin, x1=vmax, y0=vmin, y1=vmax,
    line=dict(color="#888", width=1, dash="dot"),
)

fig_vp.add_trace(go.Scatter(
    x=lam_norm[valid_mask],
    y=vap_norm[valid_mask],
    mode="markers",
    marker=dict(
        size=9,
        color=dev_arr[valid_mask],
        colorscale="RdBu_r",
        cmin=-60, cmax=60,
        colorbar=dict(title="Price – Value<br>deviation (%)"),
        opacity=0.8,
        line=dict(width=0.5, color="#333"),
    ),
    text=[sect_names_all[i] for i, v in enumerate(valid_mask) if v],
    customdata=[[marx_df.iloc[i]["labor_value"], dev_arr[i]]
                for i, v in enumerate(valid_mask) if v],
    hovertemplate=(
        "<b>%{text}</b><br>"
        "Labor value (norm.): %{x:.3f}<br>"
        "Price proxy (norm.): %{y:.3f}<br>"
        "Deviation: %{customdata[1]:.1f}%<extra></extra>"
    ),
    name="Sectors",
))

fig_vp.update_layout(
    title=(
        "Labor Value vs. Market-Price Proxy, 2024<br>"
        "<sup>Both normalized to mean=1. Dotted line = equality (LTV prediction). "
        "Color = % deviation of price proxy from labor value.</sup>"
    ),
    xaxis_title="Labor value (normalized, mean=1)",
    yaxis_title="Price proxy (VA per unit, normalized, mean=1)",
    template="plotly_white",
    width=820,
    height=560,
)

fig_vp_path = OUT / "fig_value_price_deviation.json"
with open(fig_vp_path, "w", encoding="utf-8") as f:
    json.dump(fig_vp.to_dict(), f, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("MARXIAN PROFIT RATE — I-O table analysis")
print("=" * 65)
print(f"\n2024 cross-section: {n} sectors from A_square")
print()
print("Labor values (top 10 by embodied labor, 2024):")
for _, row in marx_df.head(10).iterrows():
    print(f"  {row['name'][:40]:40s}  lambda={row['labor_value']:.6f}")

print()
r_1997 = ts[ts["year"] == 1997]["r_flow_proxy"].values
r_2024 = ts[ts["year"] == 2024]["r_flow_proxy"].values
r_peak = ts["r_flow_proxy"].max()
r_peak_yr = ts.loc[ts["r_flow_proxy"].idxmax(), "year"]
if len(r_1997) and len(r_2024):
    print(f"Profit rate proxy: {r_1997[0]:.4f} (1997) → {r_2024[0]:.4f} (2024)")
    print(f"  Peak: {r_peak:.4f} in {r_peak_yr}")
    print(f"  Change: {(r_2024[0] - r_1997[0]) * 100:+.2f} pp over 27 years")

print()
print("NOTE: C = intermediate-input FLOW (not fixed-capital stock).")
print("  This proxy overstates denominator relative to classical measures.")

print()
print(f"Outputs written to: {OUT}")
print(f"  marx.csv — {len(marx_df)} rows (labor values + price proxy, 2024)")
print(f"  fig_profit_rate_trend.json — trend 1997-2024")
print(f"  fig_value_price_deviation.json — value vs price scatter, 2024")
