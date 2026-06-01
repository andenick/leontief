"""Structural Decomposition Analysis (SDA): Technology vs Demand, 1997->2024.

Three-term SDA following Dietzenbacher & Los (1998):
    Dx = L1*Df  +  DL*f0  +  DL*Df
         demand    tech      interaction

Clean inputs: square 71x71 L matrices from BEA pipeline; final-demand
vectors aggregated as row-sums of the FD matrix, aligned to L's 71-sector
index by intersection (3 sectors in L absent from FD: 441, 445, 452 — retail
trade detail rows not present in BEA FD table; their f is set to 0).

Reads:
    ./data/L_1997.csv       — 71x71 Leontief inverse, 1997
    ./data/L_2024.csv       — 71x71 Leontief inverse, 2024
    ./data/fd_1997.csv      — aggregated final-demand vector, 1997 (sector, final_demand)
    ./data/fd_2024.csv      — aggregated final-demand vector, 2024 (sector, final_demand)
    ./data/sector_names.csv — code -> name

Writes:
    ./outputs/sda.csv
    ./outputs/fig_sda_contributions.json
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

L0 = pd.read_csv(DATA / "L_1997.csv", index_col=0)
L1 = pd.read_csv(DATA / "L_2024.csv", index_col=0)

fd0_raw = pd.read_csv(DATA / "fd_1997.csv").set_index("sector")["final_demand"]
fd1_raw = pd.read_csv(DATA / "fd_2024.csv").set_index("sector")["final_demand"]

# ---------------------------------------------------------------------------
# Alignment: L has 71 sectors; FD was pre-aligned to L's index with zeros
# for the 3 sectors (441, 445, 452) absent from the BEA final-demand table.
# ---------------------------------------------------------------------------
L_idx = list(L0.index)
assert list(L1.index) == L_idx, "L_1997 and L_2024 must share the same index"
assert len(L_idx) == 71, f"Expected 71 sectors, got {len(L_idx)}"

f0 = fd0_raw.reindex(L_idx).fillna(0)
f1 = fd1_raw.reindex(L_idx).fillna(0)

n_zero_f0 = (f0 == 0).sum()
n_zero_f1 = (f1 == 0).sum()
# Expect 3 zeros (441, 445, 452)
assert n_zero_f0 == 3, f"Unexpected zero-FD count for 1997: {n_zero_f0}"
assert n_zero_f1 == 3, f"Unexpected zero-FD count for 2024: {n_zero_f1}"

# ---------------------------------------------------------------------------
# SDA — three-term decomposition
# Dx = L1*Df  (demand effect)
#    + DL*f0  (technology effect)
#    + DL*Df  (interaction effect)
# where DL = L1 - L0,  Df = f1 - f0
# ---------------------------------------------------------------------------
L0_arr = L0.values.astype(float)
L1_arr = L1.values.astype(float)
f0_arr = f0.values.astype(float)
f1_arr = f1.values.astype(float)

Df = f1_arr - f0_arr
DL = L1_arr - L0_arr

demand_effect = L1_arr @ Df          # shape (71,)
tech_effect   = DL @ f0_arr          # shape (71,)
interact_eff  = DL @ Df              # shape (71,)
total_change  = demand_effect + tech_effect + interact_eff

# Aggregate scalars
tot   = total_change.sum()
d_sum = demand_effect.sum()
t_sum = tech_effect.sum()
i_sum = interact_eff.sum()

# ---------------------------------------------------------------------------
# Results DataFrame
# ---------------------------------------------------------------------------
results = pd.DataFrame({
    "sector": L_idx,
    "name": [names.get(c, c) for c in L_idx],
    "total_change":         total_change,
    "demand_effect":        demand_effect,
    "technology_effect":    tech_effect,
    "interaction_effect":   interact_eff,
    "demand_pct":           demand_effect / np.where(total_change != 0, total_change, np.nan) * 100,
    "tech_pct":             tech_effect   / np.where(total_change != 0, total_change, np.nan) * 100,
})

results = results.sort_values("total_change", ascending=False).reset_index(drop=True)
results.to_csv(OUT / "sda.csv", index=False)

# ---------------------------------------------------------------------------
# Figure: aggregate technology vs demand bar + top-sector technology bars
# ---------------------------------------------------------------------------

# Panel A: aggregate split (3 bars: demand, technology, interaction)
agg_labels = ["Final Demand Effect", "Technology Effect", "Interaction Effect"]
agg_values = [d_sum, t_sum, i_sum]
agg_colors = ["#2980b9", "#e74c3c", "#f39c12"]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=agg_labels,
    y=[v / 1e6 for v in agg_values],
    marker_color=agg_colors,
    text=[f"${v/1e6:+.2f}T" for v in agg_values],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>%{y:,.3f} $trillion<extra></extra>",
    name="Aggregate contribution",
))

fig.update_layout(
    title=(
        "SDA: Decomposition of U.S. Output Change, 1997–2024<br>"
        "<sup>Three-term: Δx = L¹·Δf  +  ΔL·f⁰  +  ΔL·Δf  ($ millions of output)</sup>"
    ),
    yaxis_title="Contribution to output change ($trillion)",
    xaxis_title="",
    template="plotly_white",
    width=820,
    height=500,
    showlegend=False,
)

fig.add_annotation(
    x=0.5, y=1.12, xref="paper", yref="paper",
    text=f"Total output change: ${tot/1e6:+.2f}T  |  "
         f"Demand: {d_sum/tot*100:.1f}%  |  "
         f"Technology: {t_sum/tot*100:.1f}%  |  "
         f"Interaction: {i_sum/tot*100:.1f}%",
    showarrow=False,
    font=dict(size=11, color="#555"),
    align="center",
)

# Save figure
fig_path = OUT / "fig_sda_contributions.json"
with open(fig_path, "w", encoding="utf-8") as fh:
    json.dump(fig.to_dict(), fh, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("STRUCTURAL DECOMPOSITION ANALYSIS — 1997 to 2024")
print("=" * 65)
print(f"\nTotal output change:    ${tot/1e6:>10.2f} trillion")
print(f"  Demand effect:        ${d_sum/1e6:>10.2f} trillion  ({d_sum/tot*100:+.1f}%)")
print(f"  Technology effect:    ${t_sum/1e6:>10.2f} trillion  ({t_sum/tot*100:+.1f}%)")
print(f"  Interaction effect:   ${i_sum/1e6:>10.2f} trillion  ({i_sum/tot*100:+.1f}%)")

print("\nTop 10 sectors by |technology effect|:")
top_tech = results.reindex(results["technology_effect"].abs().sort_values(ascending=False).index)
for _, row in top_tech.head(10).iterrows():
    print(f"  {row['name']:<50s}  tech={row['technology_effect']/1e3:>+8.1f}k")

print("\nTop 5 sectors by demand effect:")
top_dem = results.sort_values("demand_effect", ascending=False)
for _, row in top_dem.head(5).iterrows():
    print(f"  {row['name']:<50s}  demand={row['demand_effect']/1e3:>+8.1f}k")

print(f"\nOutputs written to: {OUT}")
print(f"  sda.csv              — {len(results)} rows")
print(f"  fig_sda_contributions.json")
