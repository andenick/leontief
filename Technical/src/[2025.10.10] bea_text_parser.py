#!/usr/bin/env python3
"""
BEA Text Format Parser
Leontief Project - I-O Tables Analysis Tool

Parse BEA Input-Output tables from tab-delimited text format.
Specifically handles the detailed benchmark tables (e.g., 2002 Use table).
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BEATextParser:
    """Parse BEA I-O tables from tab-delimited text format."""

    def __init__(self):
        """Initialize parser."""
        logger.info("BEATextParser initialized")

    def parse_use_table(self, filepath: Path, year: int) -> Dict:
        """
        Parse BEA Use table from tab-delimited text format.

        BEA Use table structure (tab-delimited):
        - Columns: Commodity, CommodityDescription, Industry, IndustryDescription,
                  ProVal, StripMar, RailVal, TruckVal, WaterVal, AirVal,
                  PipeVal, GasPipeVal, WhsVal, RetVal, PurVal, IOYear
        - Rows are in "long format": one row per transaction
        - Need to pivot to matrix format

        Transaction types:
        - Intermediate: Commodity (e.g., 1111A0) → Industry (e.g., 311221)
        - Final Demand: Commodity → F***** (F01000, F02000, F03000, F04000, F05000)
        - Value Added: V***** (V00100, V00200, V00300) → Industry
        - Government: S***** codes

        Args:
            filepath: Path to tab-delimited text file
            year: Year of the table

        Returns:
            Dictionary with parsed I-O table components
        """
        logger.info(f"Parsing BEA Use table: {filepath.name}")
        logger.info(f"Year: {year}")

        # Read the fixed-width file
        # BEA files are space-padded with fixed-width columns
        try:
            # Let pandas automatically detect column widths from first few rows
            df = pd.read_fwf(
                filepath,
                encoding='utf-8',
                dtype=str
            )

            logger.info(f"Columns detected: {list(df.columns)}")
            logger.info(f"Total rows: {len(df)}")

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise

        # Identify the correct column names (in case they have variations)
        commodity_col = [c for c in df.columns if 'Commodity' in c and 'Description' not in c][0]
        industry_col = [c for c in df.columns if 'Industry' in c and 'Description' not in c][0]

        # Rename to standard names for easier access
        df = df.rename(columns={commodity_col: 'Commodity', industry_col: 'Industry'})

        # Check if PurVal column exists, if not, extract from merged columns
        if 'PurVal' not in df.columns:
            logger.info("PurVal not found as separate column, extracting from data...")
            # Find the merged column that contains all the transport/margin data
            merged_cols = [c for c in df.columns if 'TruckVal' in c or 'PurVal' in c]
            if merged_cols:
                merged_col = merged_cols[0]
                logger.info(f"Found merged column: {merged_col[:80]}...")

                # Split the merged column by whitespace and extract the last numeric value before IOYear
                # This should be PurVal
                df['PurVal'] = df[merged_col].str.strip().str.split().str[-2]
                df['IOYear'] = df[merged_col].str.strip().str.split().str[-1]
                logger.info("Extracted PurVal and IOYear from merged column")

        # Remove rows with missing Commodity or Industry (footnotes)
        df = df.dropna(subset=['Commodity', 'Industry'])

        logger.info(f"Total transactions read: {len(df):,}")
        logger.info(f"Columns: {list(df.columns)}")

        # Separate different table components
        components = self._separate_components(df)

        # Build the transactions matrix (Z)
        logger.info("Building transactions matrix (Z)...")
        Z = self._build_transactions_matrix(components['intermediate'])

        # Build final demand matrix (F)
        logger.info("Building final demand matrix (F)...")
        F = self._build_final_demand_matrix(components['final_demand'])

        # Build value added vector (VA)
        logger.info("Building value added matrix (VA)...")
        VA = self._build_value_added_matrix(components['value_added'])

        # Calculate total output
        logger.info("Calculating total output...")
        # Total output = sum of intermediate + sum of final demand
        x = Z.sum(axis=0) + F.sum(axis=0)

        # Get sector names
        industry_names = Z.columns.to_list()
        commodity_names = Z.index.to_list()

        logger.info(f"\n{'='*80}")
        logger.info(f"Table Summary:")
        logger.info(f"  Industries: {len(industry_names)}")
        logger.info(f"  Commodities: {len(commodity_names)}")
        logger.info(f"  Transactions matrix shape: {Z.shape}")
        logger.info(f"  Final demand columns: {len(F.columns)}")
        logger.info(f"  Value added rows: {len(VA.index)}")
        logger.info(f"  Total output sum: ${x.sum()/1e6:,.0f} billion")
        logger.info(f"{'='*80}\n")

        # Build IO table dictionary
        io_table = {
            "metadata": {
                "country": "USA",
                "year": year,
                "source": "BEA",
                "table_type": "use",
                "classification": "NAICS",
                "num_industries": len(industry_names),
                "num_commodities": len(commodity_names),
                "vintage": f"{year} Benchmark",
                "format": "tab-delimited text",
                "units": "millions of dollars"
            },
            "transactions_matrix": Z,
            "final_demand": F,
            "value_added": VA,
            "total_output": x,
            "industry_names": industry_names,
            "commodity_names": commodity_names,
            "parsed": True
        }

        return io_table

    def _separate_components(self, df: pd.DataFrame) -> Dict:
        """
        Separate dataframe into intermediate, final demand, and value added components.

        Args:
            df: Full dataframe with all transactions

        Returns:
            Dictionary with separated components
        """
        logger.info("Separating table components...")

        # Intermediate transactions: both Commodity and Industry are regular codes
        # (not starting with F, V, or S)
        intermediate = df[
            ~df['Commodity'].str.startswith(('F', 'V', 'S')) &
            ~df['Industry'].str.startswith(('F', 'V', 'S'))
        ].copy()

        # Final demand: Commodity is regular, Industry starts with F
        final_demand = df[
            ~df['Commodity'].str.startswith(('F', 'V', 'S')) &
            df['Industry'].str.startswith('F')
        ].copy()

        # Value added: Commodity starts with V
        value_added = df[
            df['Commodity'].str.startswith('V')
        ].copy()

        # Government: codes starting with S (we'll include these in industries)
        government = df[
            ~df['Commodity'].str.startswith(('F', 'V', 'S')) &
            df['Industry'].str.startswith('S')
        ].copy()

        # Add government to final demand
        final_demand = pd.concat([final_demand, government], ignore_index=True)

        logger.info(f"  Intermediate transactions: {len(intermediate):,}")
        logger.info(f"  Final demand transactions: {len(final_demand):,}")
        logger.info(f"  Value added transactions: {len(value_added):,}")

        return {
            'intermediate': intermediate,
            'final_demand': final_demand,
            'value_added': value_added
        }

    def _build_transactions_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build transactions matrix (Z) from intermediate transactions.

        Z[i, j] = amount of commodity i used by industry j

        Args:
            df: DataFrame with intermediate transactions

        Returns:
            Transactions matrix Z (commodities × industries)
        """
        # Convert PurVal to numeric
        df_copy = df.copy()
        df_copy['PurVal'] = pd.to_numeric(df_copy['PurVal'], errors='coerce')

        # Use PurVal (Purchaser's value) as the transaction amount
        Z = df_copy.pivot_table(
            values='PurVal',
            index='Commodity',
            columns='Industry',
            aggfunc='sum',
            fill_value=0.0
        )

        # Sort by codes
        Z = Z.sort_index(axis=0).sort_index(axis=1)

        logger.info(f"  Z matrix shape: {Z.shape}")
        logger.info(f"  Z total: ${Z.sum().sum()/1e6:,.0f} billion")

        return Z

    def _build_final_demand_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build final demand matrix (F) from final demand transactions.

        F[i, category] = final demand for commodity i in category

        Args:
            df: DataFrame with final demand transactions

        Returns:
            Final demand matrix F (commodities × final demand categories)
        """
        if len(df) == 0:
            logger.warning("  No final demand data found")
            return pd.DataFrame()

        # Convert PurVal to numeric
        df_copy = df.copy()
        df_copy['PurVal'] = pd.to_numeric(df_copy['PurVal'], errors='coerce')

        F = df_copy.pivot_table(
            values='PurVal',
            index='Commodity',
            columns='Industry',
            aggfunc='sum',
            fill_value=0.0
        )

        # Sort by codes
        F = F.sort_index(axis=0).sort_index(axis=1)

        logger.info(f"  F matrix shape: {F.shape}")
        logger.info(f"  F categories: {list(F.columns)}")
        logger.info(f"  F total: ${F.sum().sum()/1e6:,.0f} billion")

        return F

    def _build_value_added_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build value added matrix (VA) from value added transactions.

        VA[component, j] = value added component for industry j

        Args:
            df: DataFrame with value added transactions

        Returns:
            Value added matrix VA (value added components × industries)
        """
        if len(df) == 0:
            logger.warning("  No value added data found")
            return pd.DataFrame()

        # Convert PurVal to numeric
        df_copy = df.copy()
        df_copy['PurVal'] = pd.to_numeric(df_copy['PurVal'], errors='coerce')

        VA = df_copy.pivot_table(
            values='PurVal',
            index='Commodity',
            columns='Industry',
            aggfunc='sum',
            fill_value=0.0
        )

        # Sort by codes
        VA = VA.sort_index(axis=0).sort_index(axis=1)

        logger.info(f"  VA matrix shape: {VA.shape}")
        logger.info(f"  VA components: {list(VA.index)}")
        logger.info(f"  VA total: ${VA.sum().sum()/1e6:,.0f} billion")

        return VA


def main():
    """Test BEA text parser with 2002 Use table."""
    print("="*80)
    print("BEA Text Format Parser - Test")
    print("="*80)

    parser = BEATextParser()

    # Parse 2002 Use table
    filepath = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/raw/bea/2002_benchmark/REV_NAICSUseDetail 4-24-08.txt")

    if not filepath.exists():
        print(f"\n[ERROR] File not found: {filepath}")
        return

    print(f"\nParsing: {filepath.name}")
    print()

    try:
        io_table = parser.parse_use_table(filepath, year=2002)

        print("\n[OK] Successfully parsed!")
        print("\nTable Components:")
        print(f"  Metadata: {io_table['metadata']}")
        print(f"\n  Transactions matrix (Z):")
        print(f"    Shape: {io_table['transactions_matrix'].shape}")
        print(f"    Total: ${io_table['transactions_matrix'].sum().sum()/1e6:,.0f} billion")

        print(f"\n  Final demand (F):")
        print(f"    Shape: {io_table['final_demand'].shape}")
        print(f"    Categories: {list(io_table['final_demand'].columns)}")

        print(f"\n  Value added (VA):")
        print(f"    Shape: {io_table['value_added'].shape}")
        print(f"    Components: {list(io_table['value_added'].index)}")

        print(f"\n  Total output (x):")
        print(f"    Length: {len(io_table['total_output'])}")
        print(f"    Sum: ${io_table['total_output'].sum()/1e6:,.0f} billion")

        # Show first few industries
        print(f"\n  First 10 industries:")
        for i, ind in enumerate(io_table['industry_names'][:10]):
            print(f"    {i+1}. {ind}")

        # Show key sectors by total output
        print(f"\n  Top 10 industries by total output:")
        top_industries = io_table['total_output'].nlargest(10)
        for ind, val in top_industries.items():
            print(f"    {ind}: ${val/1e3:,.0f} billion")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
