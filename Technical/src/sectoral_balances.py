"""Godley Sectoral Financial Balances from I-O tables.

Maps I-O value-added flows to Wynne Godley's three-sector identity:
    (G - T) = (S - I) - NX

Where:
- (G - T) = Government sector balance (deficit = positive)
- (S - I) = Private sector balance (net saving = positive)
- NX = Net exports (surplus = positive)

Reference: Godley & Lavoie (2007) — Monetary Economics
           Lavoie & Zezza (2012) — Selected Writings of Wynne Godley
           Both from Wynne Knowledge Base.
"""

import numpy as np
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def map_io_to_sectoral_balances(
    value_added: pd.DataFrame,
    final_demand: pd.DataFrame,
    column_mapping: Dict[str, list[str]] | None = None,
) -> Dict[str, float]:
    """Map I-O table flows to Godley's three-sector balances.

    Uses the value-added rows and final demand columns of the I-O table
    to compute the sectoral balances identity.

    Args:
        value_added: Value-added DataFrame with components as rows
            (compensation, taxes, gross operating surplus, imports).
        final_demand: Final demand DataFrame with categories as columns
            (personal consumption, investment, government, exports, imports).
        column_mapping: Optional mapping of final demand column names to
            categories. If None, attempts auto-detection from BEA names.

    Returns:
        Dict with government_balance, private_balance, external_balance,
        and identity_check (should be ~0).
    """
    if column_mapping is None:
        column_mapping = _detect_bea_columns(final_demand.columns)

    fd = final_demand

    # Government: G - T
    gov_spending = fd[column_mapping.get("government", [])].sum().sum()
    # Taxes come from value-added rows
    if "taxes" in column_mapping:
        taxes = value_added.loc[column_mapping["taxes"]].sum().sum() if column_mapping["taxes"] else 0
    else:
        taxes = 0
    gov_balance = gov_spending - taxes

    # External: Exports - Imports (NX)
    exports = fd[column_mapping.get("exports", [])].sum().sum()
    imports = fd[column_mapping.get("imports", [])].sum().sum()
    net_exports = exports - imports

    # Private: by identity, (S - I) = (G - T) + NX
    # Or directly: private income - private spending
    consumption = fd[column_mapping.get("consumption", [])].sum().sum()
    investment = fd[column_mapping.get("investment", [])].sum().sum()

    # Total private income approximated from value-added
    total_va = value_added.sum().sum()
    private_income = total_va - taxes
    private_balance = private_income - consumption - investment

    # Identity check: (G-T) = (S-I) - NX should hold
    identity_check = gov_balance - private_balance + net_exports

    result = {
        "government_spending": gov_spending,
        "taxes": taxes,
        "government_balance": gov_balance,
        "consumption": consumption,
        "investment": investment,
        "private_balance": private_balance,
        "exports": exports,
        "imports": imports,
        "net_exports": net_exports,
        "identity_check": identity_check,
    }

    logger.info(
        f"Sectoral balances: Gov={gov_balance:.1f}, "
        f"Private={private_balance:.1f}, NX={net_exports:.1f}, "
        f"Identity check={identity_check:.1f}"
    )
    return result


def _detect_bea_columns(columns: pd.Index) -> Dict[str, list[str]]:
    """Auto-detect BEA final demand column categories.

    BEA I-O tables typically have columns like:
    - Personal Consumption Expenditures
    - Gross Private Fixed Investment
    - Federal Government / State & Local Government
    - Exports / Imports
    """
    mapping: Dict[str, list[str]] = {
        "consumption": [],
        "investment": [],
        "government": [],
        "exports": [],
        "imports": [],
    }

    for col in columns:
        col_lower = str(col).lower()
        if "consumption" in col_lower or "personal" in col_lower:
            mapping["consumption"].append(col)
        elif "invest" in col_lower or "capital formation" in col_lower:
            mapping["investment"].append(col)
        elif "government" in col_lower or "federal" in col_lower or "state" in col_lower:
            mapping["government"].append(col)
        elif "export" in col_lower:
            mapping["exports"].append(col)
        elif "import" in col_lower:
            mapping["imports"].append(col)

    return mapping


def sectoral_balances_timeseries(
    io_tables: list[Dict],
    years: list[int],
) -> pd.DataFrame:
    """Calculate sectoral balances across multiple I-O table years.

    Args:
        io_tables: List of I-O table dicts (each with value_added, final_demand).
        years: Corresponding years.

    Returns:
        DataFrame with years as index and balance components as columns.
    """
    rows = []
    for table, year in zip(io_tables, years):
        balances = map_io_to_sectoral_balances(
            table["value_added"],
            table["final_demand"],
        )
        balances["year"] = year
        rows.append(balances)

    return pd.DataFrame(rows).set_index("year")
