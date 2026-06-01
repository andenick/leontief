"""Hypothetical Extraction Method (HEM): sector importance by output loss.

Reads:
    ./data/A_square_2024.csv  — 71x71 direct requirements matrix, 2024
                                (derived from the BEA Leontief inverse: A = I - L^{-1})
    ./data/fd_agg_2024.csv    — aggregated final demand per sector, 2024
    ./data/sector_names.csv   — sector code -> name mapping

Method:
    For each sector k, zero out row k and column k of A_square, recompute
    L' = (I - A')^{-1}, and compute the output loss:
        impact_k = total(L * f) - total(L' * f)
    where f is the aggregated final-demand vector. This measures how much
    total economy-wide gross output sector k supports.

    This is the *complete* extraction variant (Miller & Blair 2022, Ch. 12):
    both backward linkages (the sector's purchases of inputs, column k) and
    forward linkages (the sector's supply to other sectors, row k) are
    simultaneously removed. The result is an upper-bound estimate of each
    sector's structural importance.

    NOTE: uses the clean square A_square (71x71), NOT the raw asymmetric
    BEA A matrix (70x71). A_square is derived from the Leontief inverse
    published on the Wassily site: A = I - L^{-1}.

Writes:
    ./outputs/hem_2024.csv
    ./outputs/fig_hem_ranking.json
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

# A_square: 71x71 clean technical-coefficient matrix
A = pd.read_csv(DATA / "A_square_2024.csv", index_col=0)
A_arr = A.values.astype(float)
n = len(A_arr)
I_mat = np.eye(n)
sectors = list(A.index)

# Final demand: align to A's sector index (already done in export, fill_value=0)
fd_df = pd.read_csv(DATA / "fd_agg_2024.csv", index_col=0)
f = fd_df.reindex(A.index, fill_value=0)["final_demand"].values.astype(float)

# ---------------------------------------------------------------------------
# Baseline Leontief inverse and output
# ---------------------------------------------------------------------------
L_baseline = np.linalg.inv(I_mat - A_arr)
x_baseline = L_baseline @ f
total_baseline = float(x_baseline.sum())

# ---------------------------------------------------------------------------
# HEM: complete extraction for every sector
# ---------------------------------------------------------------------------
results = []
for k, code in enumerate(sectors):
    A_mod = A_arr.copy()
    A_mod[k, :] = 0.0   # zero row k  -> sector stops supplying intermediates
    A_mod[:, k] = 0.0   # zero col k  -> sector stops purchasing inputs
    L_mod = np.linalg.inv(I_mat - A_mod)
    x_mod = L_mod @ f
    loss = total_baseline - float(x_mod.sum())
    results.append({
        "sector": code,
        "name": names.get(code, code),
        "extraction_impact": loss,
        "pct_of_total": loss / total_baseline * 100 if total_baseline > 0 else 0.0,
    })

hem_df = pd.DataFrame(results).sort_values("extraction_impact", ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------------------
# Save output table
# ---------------------------------------------------------------------------
hem_df.to_csv(OUT / "hem_2024.csv", index=False)

# ---------------------------------------------------------------------------
# Figure: top-15 sectors by extraction impact (horizontal bar)
# ---------------------------------------------------------------------------
top15 = hem_df.head(15).sort_values("extraction_impact", ascending=True)

fig = go.Figure(go.Bar(
    x=top15["extraction_impact"] / 1e6,   # billions USD
    y=top15["name"],
    orientation="h",
    marker=dict(
        color=top15["extraction_impact"],
        colorscale="Blues",
        showscale=False,
    ),
    customdata=top15[["pct_of_total"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Output supported: $%{x:.1f}B<br>"
        "Share of total: %{customdata[0]:.2f}%"
        "<extra></extra>"
    ),
))

fig.update_layout(
    title=(
        "Hypothetical Extraction: Output Supported by Each Sector, 2024"
        "<br><sup>If the sector vanished — both as buyer and supplier — "
        "how much gross output would the economy lose?</sup>"
    ),
    xaxis_title="Output Supported ($ billions)",
    yaxis_title="",
    template="plotly_white",
    width=820,
    height=540,
    margin=dict(l=260, r=40, t=80, b=60),
)

fig_path = OUT / "fig_hem_ranking.json"
with open(fig_path, "w", encoding="utf-8") as f_out:
    json.dump(fig.to_dict(), f_out, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
top_sector = hem_df.iloc[0]
print("=" * 65)
print("HYPOTHETICAL EXTRACTION METHOD (HEM) — 2024")
print("=" * 65)
print(f"\nBaseline total output:  ${total_baseline / 1e6:,.0f}B")
print(f"\nTop sector by extraction impact:")
print(f"  {top_sector['name']} ({top_sector['sector']})")
print(f"  Output supported: ${top_sector['extraction_impact'] / 1e6:,.1f}B")
print(f"  Share of total:   {top_sector['pct_of_total']:.2f}%")
print(f"\nTop 10 sectors by extraction impact:")
top10_print = hem_df.head(10)[["sector", "name", "pct_of_total"]].copy()
top10_print["pct_of_total"] = top10_print["pct_of_total"].map("{:.2f}%".format)
print(top10_print.to_string(index=False))
print(f"\nOutputs written to: {OUT}")
print(f"  hem_2024.csv — {len(hem_df)} rows")
print(f"  fig_hem_ranking.json — horizontal bar, top-15 sectors")
