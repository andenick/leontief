"""Functional income distribution analysis from I-O value-added data.

Tracks the wage share (labor's share of income) over time, decomposes
aggregate changes into within-sector and between-sector components.

Reference: Kalecki, post-Keynesian distribution theory — from Wynne KB.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def wage_share_by_sector(
    value_added: pd.DataFrame,
    comp_code: str = "V001",
) -> pd.Series:
    """Calculate labor share of value added by sector.

    w_j = compensation_j / total_VA_j

    Args:
        value_added: VA components (rows) × sectors (columns).
        comp_code: Row code for compensation (V001 or V00100 depending on data).

    Returns:
        Series of wage shares by sector.
    """
    # Find the compensation row (may be V001, V00100, or similar)
    comp_row = None
    for idx in value_added.index:
        if "V001" in str(idx) or "comp" in str(idx).lower():
            comp_row = idx
            break

    if comp_row is None:
        # Use first VA row as proxy
        comp_row = value_added.index[0]
        logger.warning(f"Compensation row not found; using {comp_row}")

    compensation = value_added.loc[comp_row]
    total_va = value_added.sum(axis=0)
    total_va_safe = total_va.replace(0, np.nan)

    ws = (compensation / total_va_safe).fillna(0)
    ws.name = "wage_share"
    return ws


def aggregate_wage_share(value_added: pd.DataFrame) -> float:
    """Economy-wide wage share: total compensation / total VA."""
    comp_row = None
    for idx in value_added.index:
        if "V001" in str(idx) or "comp" in str(idx).lower():
            comp_row = idx
            break
    if comp_row is None:
        comp_row = value_added.index[0]

    total_comp = value_added.loc[comp_row].sum()
    total_va = value_added.sum().sum()
    if total_va == 0:
        return 0.0
    return float(total_comp / total_va)


def wage_share_decomposition(
    ws_0: pd.Series, ws_1: pd.Series,
    weight_0: pd.Series, weight_1: pd.Series,
) -> dict:
    """Shift-share decomposition of aggregate wage share change.

    ΔW = Σ w̄ᵢ·Δsᵢ + Σ s̄ᵢ·Δwᵢ + Σ Δwᵢ·Δsᵢ

    Where w = sector wage share, s = sector weight in economy.
    First term: between-sector (composition effect)
    Second term: within-sector (wage bargaining effect)
    Third term: interaction

    Args:
        ws_0, ws_1: Wage shares by sector in periods 0 and 1.
        weight_0, weight_1: Sector weights (share of total VA) in periods 0 and 1.

    Returns:
        Dict with total_change, within_sector, between_sector, interaction.
    """
    common = ws_0.index.intersection(ws_1.index)
    w0 = ws_0.reindex(common).fillna(0)
    w1 = ws_1.reindex(common).fillna(0)
    s0 = weight_0.reindex(common).fillna(0)
    s1 = weight_1.reindex(common).fillna(0)

    dw = w1 - w0
    ds = s1 - s0
    w_bar = (w0 + w1) / 2
    s_bar = (s0 + s1) / 2

    between = (w_bar * ds).sum()
    within = (s_bar * dw).sum()
    interaction = (dw * ds).sum()
    total = between + within + interaction

    return {
        "total_change": float(total),
        "within_sector": float(within),
        "between_sector": float(between),
        "interaction": float(interaction),
        "aggregate_ws_0": float((w0 * s0).sum()),
        "aggregate_ws_1": float((w1 * s1).sum()),
    }
