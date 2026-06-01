"""Download water use satellite data for I-O water footprint analysis.

Sources:
1. BEA Water Satellite Accounts (experimental, 2007/2012)
   https://www.bea.gov/data/special-topics/water
2. USGS Water Use Data (every 5 years)
   https://water.usgs.gov/watuse/

Note: Both sources require manual Excel download.
This script provides URLs and parses downloaded files.
"""

from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent.parent
SATELLITE = PROJECT / "Technical" / "data" / "raw" / "satellite" / "water"
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "satellite"


def print_download_instructions():
    """Print manual download instructions for water data."""
    print("\n" + "=" * 70)
    print("WATER USE SATELLITE DATA — MANUAL DOWNLOAD REQUIRED")
    print("=" * 70)
    print("""
Water use data is not available via API. Download manually:

1. BEA Water Satellite Accounts (best alignment with I-O sectors):
   URL: https://www.bea.gov/data/special-topics/water
   -> Download "Water Use Tables" Excel
   -> Available years: 2007, 2012 (experimental)
   -> Save to: Technical/data/raw/satellite/water/

2. USGS Water Use Data (comprehensive, county-level):
   URL: https://waterdata.usgs.gov/nwis/wu
   -> Select: State, Category, Year
   -> Download CSV
   -> Available years: 2000, 2005, 2010, 2015, 2020
   -> Save to: Technical/data/raw/satellite/water/

3. EXIOBASE 3 (multi-region with water satellite accounts):
   URL: https://zenodo.org/records/5589597
   -> Download US water extension vectors
   -> Save to: Technical/data/raw/satellite/water/

After downloading, use parse functions below to process.
""")


def parse_bea_water_excel(filepath: Path) -> dict:
    """Parse BEA water satellite account Excel file.

    Args:
        filepath: Path to downloaded Excel.

    Returns:
        Dict with sector-indexed water use data.
    """
    import pandas as pd

    logger.info(f"Parsing BEA water data from {filepath.name}")
    try:
        sheets = pd.ExcelFile(filepath).sheet_names
        logger.info(f"  Sheets: {sheets}")
        df = pd.read_excel(filepath, sheet_name=0, header=None)
        logger.info(f"  Shape: {df.shape}")
        return {"raw": df, "sheets": sheets}
    except Exception as e:
        logger.error(f"  Parse error: {e}")
        return {}


def parse_usgs_water_csv(filepath: Path) -> dict:
    """Parse USGS water use CSV data.

    USGS data is by county and category. Needs aggregation to
    NAICS-like sectors for I-O integration.

    Args:
        filepath: Path to USGS CSV.

    Returns:
        Dict with aggregated water use by category.
    """
    import pandas as pd

    logger.info(f"Parsing USGS water data from {filepath.name}")
    try:
        df = pd.read_csv(filepath)
        logger.info(f"  Shape: {df.shape}, Columns: {list(df.columns[:10])}")
        return {"raw": df}
    except Exception as e:
        logger.error(f"  Parse error: {e}")
        return {}


def check_satellite_data_status():
    """Report what water satellite data is available."""
    print("\n--- Water Satellite Data Status ---")

    files = list(SATELLITE.glob("*"))
    if files:
        print(f"Files in {SATELLITE}:")
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.0f} KB)")
    else:
        print(f"No files in {SATELLITE}")
        print("Run print_download_instructions() for download URLs.")

    processed = list(PROCESSED.glob("water*"))
    if processed:
        print(f"\nProcessed files:")
        for f in processed:
            print(f"  {f.name}")
    else:
        print("\nNo processed water satellite data yet.")


def main():
    logger.info("=" * 70)
    logger.info("WATER USE SATELLITE DATA COLLECTOR")
    logger.info("=" * 70)

    SATELLITE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    print_download_instructions()
    check_satellite_data_status()


if __name__ == "__main__":
    main()
