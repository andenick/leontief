"""Ghosh supply-side (allocation) model — dual of Leontief demand-side.

The Ghosh model traces forward linkages: how a supply-side shock in one
sector propagates through downstream industries.

B = x̂⁻¹Z  (allocation coefficients — share of output sold to each buyer)
G = (I - B)⁻¹  (Ghosh inverse)

Reference: Miller & Blair (2009), Ch. 12 — from Wynne KB.
"""

import numpy as np
import pandas as pd
from scipy import linalg
import logging

logger = logging.getLogger(__name__)


def allocation_coefficients(
    use_table: pd.DataFrame,
    total_output: pd.Series,
    L_matrix: pd.DataFrame = None,
) -> pd.DataFrame:
    """Calculate allocation coefficient matrix B = x̂⁻¹Z.

    Each element B_ij = z_ij / x_i — share of sector i's output
    allocated to sector j as intermediate input.

    Args:
        use_table: Full Use table.
        total_output: Total industry output.
        L_matrix: If provided, use its index as the definitive sector list.
    """
    # Use L_matrix sectors as ground truth (guaranteed to be square and clean)
    if L_matrix is not None:
        sectors = sorted(L_matrix.index.tolist())
    else:
        sectors = sorted(set(total_output.index))

    # Filter to sectors present in both rows and columns of Use table
    valid_rows = [r for r in use_table.index if r in sectors]
    valid_cols = [c for c in use_table.columns if c in sectors]
    common = sorted(set(valid_rows) & set(valid_cols))

    Z = use_table.loc[common, common].fillna(0)
    x = total_output.reindex(common).fillna(0)

    x_safe = x.replace(0, np.nan)
    B = Z.div(x_safe, axis=0).fillna(0)
    return B


def ghosh_inverse(B: pd.DataFrame) -> pd.DataFrame:
    """Calculate Ghosh inverse G = (I - B)⁻¹."""
    n = B.shape[0]
    G_vals = linalg.inv(np.eye(n) - B.values)
    return pd.DataFrame(G_vals, index=B.index, columns=B.columns)


def forward_multipliers(G: pd.DataFrame) -> pd.Series:
    """Forward (supply-side) multipliers — row sums of Ghosh inverse.

    Interpretation: total output generated across all downstream sectors
    per unit of primary input (value added) in sector i.
    """
    fm = G.sum(axis=1)
    fm.name = "forward_multiplier"
    return fm


def supply_shock_impact(G: pd.DataFrame, shock: pd.Series) -> pd.Series:
    """Calculate forward impact of a supply-side shock.

    Args:
        G: Ghosh inverse matrix.
        shock: Change in value-added by sector (e.g., from disruption).

    Returns:
        Series of output changes across all sectors.
    """
    aligned = shock.reindex(G.index).fillna(0)
    impact = aligned.values @ G.values
    return pd.Series(impact, index=G.columns, name="supply_impact")


def validate_ghosh(B: pd.DataFrame) -> pd.DataFrame:
    """Validate the Ghosh allocation coefficient matrix.

    Checks for row sums exceeding 1 (inconsistent data) and negative entries.

    Args:
        B: Allocation coefficient matrix.

    Returns:
        DataFrame with diagnostics per sector: row_sum, valid, issues.
    """
    row_sums = B.sum(axis=1)
    has_negative = (B < 0).any(axis=1)

    issues = []
    for sector in B.index:
        sector_issues = []
        if row_sums[sector] > 1.0:
            sector_issues.append(f"row_sum={row_sums[sector]:.4f}>1")
        if has_negative[sector]:
            n_neg = (B.loc[sector] < 0).sum()
            sector_issues.append(f"{n_neg}_negative_entries")
        issues.append("; ".join(sector_issues) if sector_issues else "OK")

    result = pd.DataFrame({
        "row_sum": row_sums,
        "valid": (row_sums <= 1.0) & ~has_negative,
        "issues": issues,
    }, index=B.index)

    n_invalid = (~result["valid"]).sum()
    if n_invalid > 0:
        logger.warning(f"Ghosh validation: {n_invalid}/{len(B)} sectors have issues")
    return result


def hypothetical_extraction_forward(
    G: pd.DataFrame,
    B: pd.DataFrame,
    shock_sector: str,
    value_added: pd.Series,
) -> pd.Series:
    """Forward (supply-side) hypothetical extraction.

    Extract a sector from the Ghosh system and measure downstream
    output loss — the supply-side dual of the backward HEM.

    Args:
        G: Ghosh inverse matrix.
        B: Allocation coefficient matrix.
        shock_sector: Sector to extract.
        value_added: Value added (primary input) vector.

    Returns:
        Series of output changes across all downstream sectors.
    """
    if shock_sector not in B.index:
        raise ValueError(f"Sector '{shock_sector}' not in B matrix")

    n = B.shape[0]
    k = B.index.get_loc(shock_sector)

    va = value_added.reindex(B.index).fillna(0)

    # Baseline output
    x_baseline = va.values @ G.values

    # Extract: zero out row k and column k of B
    B_mod = B.values.copy()
    B_mod[k, :] = 0
    B_mod[:, k] = 0

    G_mod = linalg.inv(np.eye(n) - B_mod)
    x_mod = va.values @ G_mod

    impact = x_baseline - x_mod
    result = pd.Series(impact, index=B.columns, name=f"forward_extraction_{shock_sector}")

    logger.info(
        f"Forward extraction of {shock_sector}: "
        f"total impact = {impact.sum():.1f} ({impact.sum()/max(x_baseline.sum(),1e-10)*100:.2f}%)"
    )
    return result
