#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download BEA Input-Output Tables
Wassily Project - I-O Tables Analysis Tool

This script downloads historical BEA I-O tables from direct download links.
For 2012 and 2017 (in interactive apps), manual download or API access needed.
"""

import os
import sys
import requests
from pathlib import Path
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Technical" / "data" / "raw" / "bea"

# Historical benchmark tables with direct downloads
HISTORICAL_TABLES = {
    "2002": {
        "use_table": "https://apps.bea.gov/industry/xls/io-annual/Use_SUT_Framework_2002.xlsx",
        "make_table": "https://apps.bea.gov/industry/xls/io-annual/Make_SUT_Framework_2002.xlsx",
        "summary": "https://apps.bea.gov/industry/xls/io-annual/IxI_Summary_2002.xlsx"
    },
    "1997": {
        "use_table": "https://apps.bea.gov/industry/xls/io-annual/Use_SUT_Framework_1997.xlsx",
        "make_table": "https://apps.bea.gov/industry/xls/io-annual/Make_SUT_Framework_1997.xlsx",
        "summary": "https://apps.bea.gov/industry/xls/io-annual/IxI_Summary_1997.xlsx"
    }
}


def download_file(url, destination):
    """
    Download a file from URL to destination with progress indication.

    Args:
        url (str): URL to download from
        destination (Path): Local file path to save to

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Downloading: {url}")
        print(f"To: {destination}")

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        # Create parent directories if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[OK] Downloaded successfully: {destination.name}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error downloading {url}: {e}")
        return False


def download_benchmark_year(year, tables_dict):
    """
    Download all tables for a specific benchmark year.

    Args:
        year (str): Benchmark year (e.g., "2002")
        tables_dict (dict): Dictionary of table types and URLs

    Returns:
        int: Number of successfully downloaded files
    """
    print(f"\n{'='*60}")
    print(f"Downloading {year} Benchmark Tables")
    print(f"{'='*60}")

    year_dir = DATA_DIR / f"{year}_benchmark"
    year_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for table_type, url in tables_dict.items():
        filename = url.split('/')[-1]
        destination = year_dir / filename

        # Skip if already downloaded
        if destination.exists():
            print(f"[SKIP] Already exists: {filename}")
            success_count += 1
            continue

        # Download
        if download_file(url, destination):
            success_count += 1
            time.sleep(1)  # Be nice to BEA servers

    print(f"\n{year}: Downloaded {success_count}/{len(tables_dict)} files")
    return success_count


def main():
    """Main download routine."""
    print("BEA Input-Output Tables Downloader")
    print("Wassily Project")
    print("="*60)

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    total_success = 0
    total_files = 0

    # Download historical benchmark years
    for year, tables in HISTORICAL_TABLES.items():
        total_files += len(tables)
        total_success += download_benchmark_year(year, tables)

    # Summary
    print("\n" + "="*60)
    print("Download Summary")
    print("="*60)
    print(f"Total files downloaded: {total_success}/{total_files}")

    # Note about newer benchmarks
    print("\n" + "="*60)
    print("Note: 2012 and 2017 Benchmark Tables")
    print("="*60)
    print("These are available through BEA's Interactive Data Application:")
    print("https://apps.bea.gov/iTable/?reqid=151&step=1")
    print("\nManual download steps:")
    print("1. Visit the interactive application")
    print("2. Select Input-Output tables")
    print("3. Choose benchmark year (2012 or 2017)")
    print("4. Select table type (Use, Make, Requirements)")
    print("5. Download as Excel or CSV")
    print(f"6. Save to: {DATA_DIR}/YEAR_benchmark/")

    print("\n[DONE] Download script complete!")


if __name__ == "__main__":
    main()
