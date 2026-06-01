#!/usr/bin/env python3
"""
Simple BEA Text Parser
Wassily Project - I-O Tables Analysis Tool

Parse BEA Use tables from space-delimited text format.
Simple, robust line-by-line approach.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_bea_use_table(filepath: Path, year: int) -> Dict:
    """
    Parse BEA Use table from space-delimited text file.

    Format: 16 fields per line (space-delimited)
    1. Commodity code
    2. Commodity description (may have spaces)
    3. Industry code
    4. Industry description (may have spaces)
    5-14. Numeric margin/transport values
    15. PurVal (Purchaser's Value) - what we need
    16. IOYear

    Args:
        filepath: Path to BEA Use table text file
        year: Year of the table

    Returns:
        Dictionary with parsed I-O table
    """
    logger.info(f"Parsing BEA Use table: {filepath.name}")
    logger.info(f"Year: {year}")

    transactions = []
    line_count = 0
    skip_count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        # Skip header line
        header = next(f)

        for line_num, line in enumerate(f, start=2):
            line_count += 1

            # Strip whitespace and check if line has content
            line = line.strip()
            if not line or line.startswith('/') or line.startswith('#'):
                skip_count += 1
                continue

            # Split on whitespace
            parts = line.split()

            # Need at least 16 fields (4 text + 12 numeric)
            if len(parts) < 16:
                skip_count += 1
                continue

            # Parse fields
            # Strategy: Last 12 elements are numeric fields (5-16)
            # Everything before that is: commodity_code, commodity_desc, industry_code, industry_desc

            numeric_fields = parts[-12:]  # Last 12 elements
            text_parts = parts[:-12]  # Everything before numeric fields

            # Extract commodity code (first element)
            commodity_code = text_parts[0]

            # Extract industry code by finding the second element that looks like a code
            # Codes are alphanumeric without spaces (e.g., 1111A0, F04000, V00100)
            industry_code = None
            industry_idx = None

            # Look for industry code (should be after commodity description)
            for i in range(1, len(text_parts)):
                # Industry codes match pattern: digits + optional letter + digits, or F/V/S codes
                if re.match(r'^[0-9A-Z]+$', text_parts[i]):
                    industry_code = text_parts[i]
                    industry_idx = i
                    break

            if industry_code is None:
                skip_count += 1
                continue

            # Commodity description: everything between commodity code and industry code
            commodity_desc = ' '.join(text_parts[1:industry_idx])

            # Industry description: everything after industry code
            industry_desc = ' '.join(text_parts[industry_idx+1:])

            # Extract numeric values
            try:
                purval = float(numeric_fields[-2])  # PurVal is 2nd from last
                ioyear = numeric_fields[-1]  # Year is last

                transactions.append({
                    'Commodity': commodity_code,
                    'CommodityDescription': commodity_desc,
                    'Industry': industry_code,
                    'IndustryDescription': industry_desc,
                    'PurVal': purval,
                    'IOYear': ioyear
                })
            except (ValueError, IndexError) as e:
                skip_count += 1
                continue

    logger.info(f"Total lines processed: {line_count:,}")
    logger.info(f"Lines skipped: {skip_count:,}")
    logger.info(f"Valid transactions: {len(transactions):,}")

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Separate components
    logger.info("\nSeparating table components...")

    # Intermediate transactions: regular commodity → regular industry
    intermediate = df[
        ~df['Commodity'].str.startswith(('F', 'V', 'S')) &
        ~df['Industry'].str.startswith(('F', 'V', 'S'))
    ].copy()

    # Final demand: commodity → F***** or S*****
    final_demand = df[
        ~df['Commodity'].str.startswith(('F', 'V', 'S')) &
        df['Industry'].str.startswith(('F', 'S'))
    ].copy()

    # Value added: V***** → industry
    value_added = df[
        df['Commodity'].str.startswith('V')
    ].copy()

    logger.info(f"  Intermediate transactions: {len(intermediate):,}")
    logger.info(f"  Final demand transactions: {len(final_demand):,}")
    logger.info(f"  Value added transactions: {len(value_added):,}")

    # Build transaction matrix Z (commodities × industries)
    logger.info("\nBuilding transactions matrix (Z)...")
    Z = intermediate.pivot_table(
        values='PurVal',
        index='Commodity',
        columns='Industry',
        aggfunc='sum',
        fill_value=0.0
    )
    Z = Z.sort_index(axis=0).sort_index(axis=1)

    logger.info(f"  Z shape: {Z.shape}")
    logger.info(f"  Z total: ${Z.sum().sum()/1e6:,.1f} billion")

    # Build final demand matrix F
    logger.info("\nBuilding final demand matrix (F)...")
    if len(final_demand) > 0:
        F = final_demand.pivot_table(
            values='PurVal',
            index='Commodity',  # Commodities as rows (same as Z)
            columns='Industry',  # Final demand categories as columns
            aggfunc='sum',
            fill_value=0.0
        )
        F = F.sort_index(axis=0).sort_index(axis=1)

        # Ensure F has same commodities as Z (reindex to match)
        F = F.reindex(index=Z.index, fill_value=0.0)

        logger.info(f"  F shape: {F.shape}")
        logger.info(f"  F categories: {list(F.columns)}")
        logger.info(f"  F total: ${F.sum().sum()/1e6:,.1f} billion")
    else:
        F = pd.DataFrame()
        logger.warning("  No final demand data found")

    # Build value added matrix VA
    logger.info("\nBuilding value added matrix (VA)...")
    if len(value_added) > 0:
        VA = value_added.pivot_table(
            values='PurVal',
            index='Commodity',  # VA components as rows
            columns='Industry',  # Industries as columns (should match Z columns)
            aggfunc='sum',
            fill_value=0.0
        )
        VA = VA.sort_index(axis=0).sort_index(axis=1)

        # Ensure VA has same industries as Z (reindex to match)
        VA = VA.reindex(columns=Z.columns, fill_value=0.0)

        logger.info(f"  VA shape: {VA.shape}")
        logger.info(f"  VA components: {list(VA.index)}")
        logger.info(f"  VA total: ${VA.sum().sum()/1e6:,.1f} billion")
    else:
        VA = pd.DataFrame()
        logger.warning("  No value added data found")

    # Calculate total commodity output (sum across all uses: intermediate + final demand)
    logger.info("\nCalculating total commodity output...")
    # Total for each commodity = intermediate uses + final demand uses
    x_commodity = Z.sum(axis=1) + F.sum(axis=1)
    logger.info(f"  Total commodity output: ${x_commodity.sum()/1e6:,.1f} billion")

    # Calculate total industry output (column sums of Z + value added)
    logger.info("\nCalculating total industry output...")
    x_industry = Z.sum(axis=0) + VA.sum(axis=0)
    logger.info(f"  Total industry output: ${x_industry.sum()/1e6:,.1f} billion")

    # Build IO table dictionary
    io_table = {
        "metadata": {
            "country": "USA",
            "year": year,
            "source": "BEA",
            "table_type": "use",
            "classification": "NAICS",
            "num_industries": Z.shape[1],
            "num_commodities": Z.shape[0],
            "vintage": f"{year} Benchmark",
            "format": "space-delimited text",
            "units": "millions of dollars"
        },
        "transactions_matrix": Z,
        "final_demand": F,
        "value_added": VA,
        "total_commodity_output": x_commodity,
        "total_industry_output": x_industry,
        "industry_names": list(Z.columns),
        "commodity_names": list(Z.index),
        "parsed": True
    }

    logger.info("\n" + "="*80)
    logger.info("Table Summary:")
    logger.info(f"  Industries: {io_table['metadata']['num_industries']}")
    logger.info(f"  Commodities: {io_table['metadata']['num_commodities']}")
    logger.info(f"  Transactions matrix (Z): ${Z.sum().sum()/1e6:,.1f} billion")
    logger.info(f"  Final demand (F): ${F.sum().sum()/1e6:,.1f} billion")
    logger.info(f"  Value added (VA): ${VA.sum().sum()/1e6:,.1f} billion")
    logger.info(f"  Total commodity output: ${x_commodity.sum()/1e6:,.1f} billion")
    logger.info(f"  Total industry output: ${x_industry.sum()/1e6:,.1f} billion")
    logger.info("="*80 + "\n")

    return io_table


def main():
    """Test the simple BEA parser."""
    print("="*80)
    print("Simple BEA Parser - Test")
    print("="*80)

    filepath = Path("D:/Arcanum/Projects/Wassily/Technical/data/raw/bea/2002_benchmark/REV_NAICSUseDetail 4-24-08.txt")

    if not filepath.exists():
        print(f"\n[ERROR] File not found: {filepath}")
        return

    print(f"\nParsing: {filepath.name}\n")

    try:
        io_table = parse_bea_use_table(filepath, year=2002)

        print("\n[OK] Successfully parsed!")
        print("\n" + "="*80)
        print("Results Summary")
        print("="*80)
        print(f"\nMetadata:")
        for key, val in io_table['metadata'].items():
            print(f"  {key}: {val}")

        print(f"\nMatrix Dimensions:")
        print(f"  Transactions (Z): {io_table['transactions_matrix'].shape}")
        print(f"  Final Demand (F): {io_table['final_demand'].shape}")
        print(f"  Value Added (VA): {io_table['value_added'].shape}")

        print(f"\nFirst 10 Industries:")
        for i, ind in enumerate(io_table['industry_names'][:10], 1):
            output = io_table['total_industry_output'].get(ind, 0)
            print(f"  {i}. {ind}: ${output/1e3:,.1f} billion")

        print(f"\nTop 10 Industries by Total Output:")
        top_industries = io_table['total_industry_output'].nlargest(10)
        for i, (ind, val) in enumerate(top_industries.items(), 1):
            print(f"  {i}. {ind}: ${val/1e3:,.1f} billion")

        # Save for next step
        print(f"\n[INFO] Saving parsed table...")
        import pickle
        output_path = Path("D:/Arcanum/Projects/Wassily/Technical/data/processed/io_table_2002.pkl")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(io_table, f)
        print(f"[OK] Saved to: {output_path}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
