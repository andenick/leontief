#!/usr/bin/env python3
"""
BEA Make Table Parser
Leontief Project - I-O Tables Analysis Tool

Parse BEA Make tables from space-delimited text format.
Make table: Industries produce Commodities (industries × commodities)
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_bea_make_table(filepath: Path, year: int) -> Dict:
    """
    Parse BEA Make table from space-delimited text file.

    Make table structure: Industries (rows) produce Commodities (columns)

    Format: Similar to Use table but transposed relationship
    1. Industry code
    2. Industry description (may have spaces)
    3. Commodity code
    4. Commodity description (may have spaces)
    5. ProVal (Producer's Value) - what we need
    6. IOYear

    Args:
        filepath: Path to BEA Make table text file
        year: Year of the table

    Returns:
        Dictionary with parsed Make table
    """
    logger.info(f"Parsing BEA Make table: {filepath.name}")
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

            # Need at least 4 fields (2 codes + value + year)
            if len(parts) < 4:
                skip_count += 1
                continue

            # Last field is year
            ioyear = parts[-1]

            # Second to last is value (ProVal)
            try:
                proval = float(parts[-2])
            except (ValueError, IndexError):
                skip_count += 1
                continue

            # Everything before value is: industry_code, industry_desc, commodity_code, commodity_desc
            # Strategy: Find first two elements that look like codes (alphanumeric patterns)

            text_parts = parts[:-2]  # Exclude value and year

            # Find codes using regex
            codes = []
            for part in text_parts:
                # Codes match pattern: digits + optional letters (e.g., 1111A0, 336111, F04000)
                if re.match(r'^[0-9A-Z]+$', part) and len(part) >= 4:
                    codes.append(part)
                    if len(codes) == 2:
                        break

            if len(codes) < 2:
                skip_count += 1
                continue

            industry_code = codes[0]
            commodity_code = codes[1]

            transactions.append({
                'Industry': industry_code,
                'Commodity': commodity_code,
                'ProVal': proval,
                'IOYear': ioyear
            })

    logger.info(f"Total lines processed: {line_count:,}")
    logger.info(f"Lines skipped: {skip_count:,}")
    logger.info(f"Valid transactions: {len(transactions):,}")

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    logger.info(f"\nBuilding Make matrix (V)...")
    logger.info(f"  Industries (rows): {df['Industry'].nunique()}")
    logger.info(f"  Commodities (columns): {df['Commodity'].nunique()}")

    # Build Make matrix V (industries × commodities)
    # V[i,j] = value of commodity j produced by industry i
    V = df.pivot_table(
        values='ProVal',
        index='Industry',
        columns='Commodity',
        aggfunc='sum',
        fill_value=0.0
    )
    V = V.sort_index(axis=0).sort_index(axis=1)

    logger.info(f"  V shape: {V.shape}")
    logger.info(f"  V total: ${V.sum().sum()/1e6:,.1f} billion")

    # Calculate total industry output (row sums)
    q = V.sum(axis=1)  # Total output by industry
    logger.info(f"  Total industry output: ${q.sum()/1e6:,.1f} billion")

    # Calculate total commodity output (column sums)
    g = V.sum(axis=0)  # Total output by commodity
    logger.info(f"  Total commodity output: ${g.sum()/1e6:,.1f} billion")

    # Build Make table dictionary
    make_table = {
        "metadata": {
            "country": "USA",
            "year": year,
            "source": "BEA",
            "table_type": "make",
            "classification": "NAICS",
            "num_industries": V.shape[0],
            "num_commodities": V.shape[1],
            "vintage": f"{year} Benchmark",
            "format": "space-delimited text",
            "units": "millions of dollars"
        },
        "make_matrix": V,
        "total_industry_output": q,
        "total_commodity_output": g,
        "industry_names": list(V.index),
        "commodity_names": list(V.columns),
        "parsed": True
    }

    logger.info("\n" + "="*80)
    logger.info("Make Table Summary:")
    logger.info(f"  Industries: {make_table['metadata']['num_industries']}")
    logger.info(f"  Commodities: {make_table['metadata']['num_commodities']}")
    logger.info(f"  Make matrix (V): ${V.sum().sum()/1e6:,.1f} billion")
    logger.info(f"  Total industry output: ${q.sum()/1e6:,.1f} billion")
    logger.info(f"  Total commodity output: ${g.sum()/1e6:,.1f} billion")
    logger.info("="*80 + "\n")

    return make_table


def main():
    """Test the Make table parser."""
    print("="*80)
    print("BEA Make Table Parser - Test")
    print("="*80)

    filepath = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/raw/bea/2002_benchmark/REV_NAICSMakeDetail 4-24-08.txt")

    if not filepath.exists():
        print(f"\n[ERROR] File not found: {filepath}")
        return

    print(f"\nParsing: {filepath.name}\n")

    try:
        make_table = parse_bea_make_table(filepath, year=2002)

        print("\n[OK] Successfully parsed!")
        print("\n" + "="*80)
        print("Results Summary")
        print("="*80)
        print(f"\nMetadata:")
        for key, val in make_table['metadata'].items():
            print(f"  {key}: {val}")

        print(f"\nMatrix Dimensions:")
        print(f"  Make matrix (V): {make_table['make_matrix'].shape}")

        print(f"\nTop 10 Industries by Total Output:")
        top_industries = make_table['total_industry_output'].nlargest(10)
        for i, (ind, val) in enumerate(top_industries.items(), 1):
            print(f"  {i}. {ind}: ${val/1e3:,.1f} billion")

        print(f"\nTop 10 Commodities by Total Output:")
        top_commodities = make_table['total_commodity_output'].nlargest(10)
        for i, (comm, val) in enumerate(top_commodities.items(), 1):
            print(f"  {i}. {comm}: ${val/1e3:,.1f} billion")

        # Save for next step
        print(f"\n[INFO] Saving parsed Make table...")
        import pickle
        output_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/processed/make_table_2002.pkl")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(make_table, f)
        print(f"[OK] Saved to: {output_path}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
