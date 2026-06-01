"""Fiscal Multipliers: Government Spending and Economy-Wide Output, 2024.

For each government final-demand category identified in the BEA FD matrix,
normalizes its spending vector to $1 total and computes:
    output_multiplier = sum(L @ f_unit)

Government F-codes (from site_data/sectors.json fd_cols):
    F06C — Federal defense consumption
    F06E — Federal defense equipment
    F06N — Federal defense structures
    F06S — Federal defense software/IP
    F07C — Federal nondefense consumption
    F07E — Federal nondefense equipment
    F07N — Federal nondefense structures
    F07S — Federal nondefense software/IP
    F10C — State & local consumption
    F10E — State & local equipment
    F10N — State & local structures
    F10S — State & local software/IP

Also reports three aggregate categories:
    Federal Defense     = F06C + F06E + F06N + F06S
    Federal Nondefense  = F07C + F07E + F07N + F07S
    State & Local Gov   = F10C + F10E + F10N + F10S

Alignment: FD rows are aligned to L's 71-sector index by intersection.
Three sectors in L (441, 445, 452: retail detail) are absent from BEA FD
rows — their fd is set to 0. Two FD rows ('Other', 'Used') are absent from
L and dropped.  Net intersection: 68 sectors common to both.
The 3 missing retail sectors receive f=0, which is correct (these sectors
receive no direct government final demand).

Reads:
    ./data/L_2024.csv        — 71x71 Leontief inverse, 2024
    ./data/fd_2024.csv       — full BEA FD matrix (sector x fd_col)
    ./data/fd_cols.csv       — code -> label from sectors.json
    ./data/sector_names.csv  — sector code -> name

Writes:
    ./outputs/fiscal.csv
    ./outputs/fig_fiscal_mult.json
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

fd_cols_df = pd.read_csv(DATA / "fd_cols.csv")
col_labels = dict(zip(fd_cols_df["code"], fd_cols_df["label"]))

L = pd.read_csv(DATA / "L_2024.csv", index_col=0)
FD = pd.read_csv(DATA / "fd_2024.csv", index_col=0)

# ---------------------------------------------------------------------------
# Alignment: intersect L's 71-sector index with FD's row index
# L has 71 sectors; FD has 70 (missing: 441, 445, 452; extra: 'Other', 'Used')
# ---------------------------------------------------------------------------
L_idx = list(L.index)
fd_idx = set(FD.index)
l_idx_set = set(L_idx)

in_l_not_fd = l_idx_set - fd_idx   # {441, 445, 452}
in_fd_not_l = fd_idx - l_idx_set   # {'Other', 'Used'}

# Reindex FD to L's full 71-sector index; missing sectors get 0
FD_aligned = FD.reindex(L_idx).fillna(0)

# Verify
assert FD_aligned.shape[0] == 71, f"Expected 71 rows after alignment, got {FD_aligned.shape[0]}"
assert len(in_l_not_fd) == 3, f"Unexpected missing FD sectors: {in_l_not_fd}"

# Government column codes
GOV_CODES = [c for c in FD_aligned.columns if c.startswith(("F06", "F07", "F10"))]

# ---------------------------------------------------------------------------
# Aggregate categories: group F06*, F07*, F10*
# ---------------------------------------------------------------------------
AGGREGATE_GROUPS = {
    "Federal Defense":    [c for c in GOV_CODES if c.startswith("F06")],
    "Federal Nondefense": [c for c in GOV_CODES if c.startswith("F07")],
    "State & Local Gov":  [c for c in GOV_CODES if c.startswith("F10")],
}

# Individual category mapping: code -> human label
INDIVIDUAL_CATS = {
    code: col_labels.get(code, code)
    for code in GOV_CODES
}

L_arr = L.loc[L_idx, L_idx].values.astype(float)


def compute_multiplier(f_vec: np.ndarray) -> dict:
    """Output multiplier for a spending vector f_vec (already aligned to L_idx)."""
    total = float(f_vec.sum())
    if total <= 0:
        return {"multiplier": 0.0, "total_spending_M": 0.0}
    f_unit = f_vec / total
    output = (L_arr @ f_unit).sum()
    return {"multiplier": float(output), "total_spending_M": float(total)}


# ---------------------------------------------------------------------------
# Compute multipliers
# ---------------------------------------------------------------------------
rows = []

# Aggregate groups
for grp_name, cols in AGGREGATE_GROUPS.items():
    f = FD_aligned[cols].sum(axis=1).values.astype(float)
    res = compute_multiplier(f)
    rows.append({
        "category":      grp_name,
        "type":          "aggregate",
        "multiplier":    res["multiplier"],
        "spending_M":    res["total_spending_M"],
    })

# Individual sub-categories
for code, label in INDIVIDUAL_CATS.items():
    f = FD_aligned[code].values.astype(float)
    res = compute_multiplier(f)
    # Use label as-is (already a str from csv)
    clean_label = str(label)
    rows.append({
        "category":      clean_label,
        "type":          "individual",
        "multiplier":    res["multiplier"],
        "spending_M":    res["total_spending_M"],
    })

fiscal_df = pd.DataFrame(rows).sort_values("multiplier", ascending=False).reset_index(drop=True)
fiscal_df.to_csv(OUT / "fiscal.csv", index=False)

# ---------------------------------------------------------------------------
# Figure: output multiplier by government spending category (bar)
# Show individual sub-categories only (9 non-zero ones + software where nonzero)
# ---------------------------------------------------------------------------
# Filter to individual with positive spending
plot_df = fiscal_df[fiscal_df["type"] == "individual"].copy()
plot_df = plot_df[plot_df["spending_M"] > 0].copy()
plot_df = plot_df.sort_values("multiplier", ascending=True).reset_index(drop=True)

# Color by agency group
def bar_color(cat_label: str) -> str:
    lab = cat_label.lower()
    if "defense" in lab and "non" not in lab and "federal" not in lab.replace("federal", ""):
        return "#c0392b"
    if "nondefense" in lab or "non-defense" in lab:
        return "#e67e22"
    if "state" in lab or "local" in lab:
        return "#2980b9"
    # fallback by code prefix
    return "#7f8c8d"


def agency_color(label: str) -> str:
    """Assign color by spending agency."""
    l = label.lower()
    if "defense" in l and "nondefense" not in l and "non-defense" not in l:
        return "#c0392b"
    elif "nondefense" in l or "non-defense" in l:
        return "#e67e22"
    elif "state" in l or "local" in l:
        return "#2980b9"
    return "#7f8c8d"


colors = [agency_color(c) for c in plot_df["category"]]

fig = go.Figure(go.Bar(
    x=plot_df["multiplier"],
    y=plot_df["category"],
    orientation="h",
    marker_color=colors,
    customdata=plot_df[["spending_M"]].values,
    text=[f"{m:.3f}" for m in plot_df["multiplier"]],
    textposition="outside",
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Output multiplier: %{x:.4f}<br>"
        "Total spending: $%{customdata[0]:,.0f}M<extra></extra>"
    ),
))

fig.update_layout(
    title=(
        "Fiscal Output Multipliers by Government Spending Category, 2024<br>"
        "<sup>$1 of normalized spending → economy-wide gross output ($); "
        "red=defense, orange=nondefense, blue=state&local</sup>"
    ),
    xaxis_title="Output multiplier ($ output per $ spending)",
    yaxis_title="",
    template="plotly_white",
    width=860,
    height=520,
    margin=dict(l=320),
)

fig.add_vline(
    x=1.0,
    line_dash="dot",
    line_color="#555",
    annotation_text="m=1 (no amplification)",
    annotation_position="top",
)

fig_path = OUT / "fig_fiscal_mult.json"
with open(fig_path, "w", encoding="utf-8") as fh:
    json.dump(fig.to_dict(), fh, cls=PlotlyJSONEncoder)

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print("=" * 65)
print("FISCAL MULTIPLIERS — Government Spending Categories, 2024")
print("=" * 65)
print("\nAlignment:")
print(f"  L index: 71 sectors")
print(f"  FD rows: 70 sectors")
print(f"  Intersection: {len(l_idx_set & fd_idx)} sectors")
print(f"  In L, not FD (set to 0): {sorted(in_l_not_fd)}")
print(f"  In FD, not L (dropped):  {sorted(in_fd_not_l)}")

print("\nAggregate category multipliers:")
agg_rows = fiscal_df[fiscal_df["type"] == "aggregate"].sort_values("multiplier", ascending=False)
for _, r in agg_rows.iterrows():
    print(f"  {r['category']:<25s}  mult={r['multiplier']:.4f}  spending=${r['spending_M']/1e3:.1f}B")

print("\nIndividual sub-category multipliers (non-zero spending):")
ind_rows = fiscal_df[(fiscal_df["type"] == "individual") & (fiscal_df["spending_M"] > 0)]
ind_rows = ind_rows.sort_values("multiplier", ascending=False)
for _, r in ind_rows.iterrows():
    print(f"  {r['category']:<55s}  mult={r['multiplier']:.4f}")

print(f"\nOutputs written to: {OUT}")
print(f"  fiscal.csv         — {len(fiscal_df)} rows")
print(f"  fig_fiscal_mult.json")
