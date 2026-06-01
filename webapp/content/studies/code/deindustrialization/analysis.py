"""Deindustrialization: The long decline of U.S. manufacturing, 1997-2024.

Reads:
    ./data/deindustrialization.csv  — year, manufacturing_va_share,
                                      manufacturing_output_share (1997-2024)
                                      (exported from BEA-verified pipeline)

Writes:
    ./outputs/deindustrialization.csv
    ./outputs/fig_deindustrialization_trend.json
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
df = pd.read_csv(DATA / "deindustrialization.csv")
df["year"] = df["year"].astype(int)
df = df.sort_values("year").reset_index(drop=True)

# Convenience aliases in percentage-point form
df["va_share_pct"] = df["manufacturing_va_share"] * 100
df["out_share_pct"] = df["manufacturing_output_share"] * 100

# ---------------------------------------------------------------------------
# Key statistics
# ---------------------------------------------------------------------------
start = df.iloc[0]
end = df.iloc[-1]

va_drop = start["va_share_pct"] - end["va_share_pct"]
out_drop = start["out_share_pct"] - end["out_share_pct"]
va_pct_decline = va_drop / start["va_share_pct"] * 100
out_pct_decline = out_drop / start["out_share_pct"] * 100

# Trough values
va_trough = df.loc[df["va_share_pct"].idxmin()]
out_trough = df.loc[df["out_share_pct"].idxmin()]

# ---------------------------------------------------------------------------
# Save output table
# ---------------------------------------------------------------------------
df[["year", "manufacturing_va_share", "manufacturing_output_share"]].to_csv(
    OUT / "deindustrialization.csv", index=False
)

# ---------------------------------------------------------------------------
# Figure: VA share and output share vs year, dual-series line chart
# ---------------------------------------------------------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["year"],
    y=df["va_share_pct"],
    name="Value-added share of GDP (%)",
    mode="lines+markers",
    line=dict(color="#2563EB", width=2.5),
    marker=dict(size=5),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "VA share: %{y:.1f}%"
        "<extra></extra>"
    ),
))

fig.add_trace(go.Scatter(
    x=df["year"],
    y=df["out_share_pct"],
    name="Gross output share (%)",
    mode="lines+markers",
    line=dict(color="#DC2626", width=2.5, dash="dot"),
    marker=dict(size=5),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Output share: %{y:.1f}%"
        "<extra></extra>"
    ),
))

# Annotate the 2009 crisis dip and 2020 COVID shock
for crisis_year, crisis_label in [(2009, "GFC trough"), (2020, "COVID")]:
    fig.add_vline(
        x=crisis_year,
        line=dict(color="#6B7280", width=1, dash="dot"),
        annotation_text=crisis_label,
        annotation_position="top right",
        annotation_font_size=11,
    )

fig.update_layout(
    title=(
        "U.S. Manufacturing Decline, 1997–2024"
        "<br><sup>Both value-added share of GDP and gross output share "
        "have fallen sharply over 28 years</sup>"
    ),
    xaxis_title="Year",
    yaxis_title="Share of total economy (%)",
    legend=dict(x=0.55, y=0.95, bgcolor="rgba(255,255,255,0.8)"),
    template="plotly_white",
    width=820,
    height=480,
    margin=dict(l=70, r=40, t=90, b=60),
)

fig_path = OUT / "fig_deindustrialization_trend.json"
with open(fig_path, "w", encoding="utf-8") as f_out:
    json.dump(fig.to_dict(), f_out, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("DEINDUSTRIALIZATION — U.S. Manufacturing, 1997-2024")
print("=" * 65)
print(f"\n{'Metric':<40} {'1997':>8} {'2024':>8} {'Drop':>8}")
print("-" * 65)
print(
    f"{'Manufacturing VA share of GDP':<40} "
    f"{start['va_share_pct']:>7.1f}% "
    f"{end['va_share_pct']:>7.1f}% "
    f"{va_drop:>6.1f}pp"
)
print(
    f"{'Manufacturing gross output share':<40} "
    f"{start['out_share_pct']:>7.1f}% "
    f"{end['out_share_pct']:>7.1f}% "
    f"{out_drop:>6.1f}pp"
)
print()
print(f"VA share decline:     {va_drop:.1f} percentage points ({va_pct_decline:.0f}% relative drop)")
print(f"Output share decline: {out_drop:.1f} percentage points ({out_pct_decline:.0f}% relative drop)")
print(f"\nVA share trough:     {va_trough['va_share_pct']:.1f}% in {int(va_trough['year'])}")
print(f"Output share trough: {out_trough['out_share_pct']:.1f}% in {int(out_trough['year'])}")
print(f"\nOutputs written to: {OUT}")
print(f"  deindustrialization.csv — {len(df)} rows")
print(f"  fig_deindustrialization_trend.json — dual-series line chart")
