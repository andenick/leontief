#!/usr/bin/env python3
"""
Test I-O Table Loader
Wassily Project

Quick test to load and inspect a downloaded I-O table.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from io_loader import IOTableLoader
import pandas as pd


def main():
    print("="*80)
    print("Testing I-O Table Loader")
    print("="*80)

    # Initialize loader
    loader = IOTableLoader()

    # List available tables
    print("\n[1] Listing available I-O tables...")
    available = loader.list_available_tables()

    if available.empty:
        print("No tables found!")
        return

    print(f"\nFound {len(available)} tables:")
    print(available.to_string(index=False))

    # Try loading the 2002 Use table
    print("\n" + "="*80)
    print("[2] Loading 2002 Use table...")
    print("="*80)

    use_2002 = available[
        (available['year'] == '2002') &
        (available['table_type'] == 'use')
    ]

    if not use_2002.empty:
        filepath = Path(use_2002.iloc[0]['filepath'])
        print(f"\nFile: {filepath.name}")

        try:
            # Load the table
            io_table = loader.load_bea_table(filepath, year=2002, table_type="use")

            print("\n[3] Table Metadata:")
            print("-" * 40)
            for key, value in io_table['metadata'].items():
                print(f"  {key}: {value}")

            print("\n[4] Raw DataFrame Info:")
            print("-" * 40)
            df = io_table['raw_dataframe']
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Rows: {len(df)}")

            print("\n[5] First few rows and columns:")
            print("-" * 40)
            print(df.iloc[:10, :5].to_string())

            print("\n[6] Sheet Names (if Excel):")
            print("-" * 40)
            xls = pd.ExcelFile(filepath, engine='openpyxl')
            for i, sheet in enumerate(xls.sheet_names, 1):
                print(f"  {i}. {sheet}")

            print("\n" + "="*80)
            print("[OK] Loading test successful!")
            print("="*80)
            print("\nNext steps:")
            print("1. Inspect the table structure in Excel")
            print("2. Identify where transactions matrix starts")
            print("3. Update io_loader.py to parse BEA format")
            print("4. Extract Z, x, VA, and F components")

        except Exception as e:
            print(f"\n[ERROR] Error loading table: {e}")
            import traceback
            traceback.print_exc()

    else:
        print("\n2002 Use table not found in downloaded files")


if __name__ == "__main__":
    main()
