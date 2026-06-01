"""Download energy and emissions satellite data for I-O environmental extension.

Sources:
1. BEA Environmental-Economic Accounts (IEA): Energy use by industry
   https://apps.bea.gov/iTable/?reqid=161
2. EPA GHG Inventory: Emissions by economic sector
   https://www.epa.gov/ghgemissions/inventory-us-greenhouse-gas-emissions-and-sinks

Note: BEA IEA tables require manual Excel download (no API endpoint).
This script provides download URLs and parses downloaded files.
"""

import json
import csv
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent.parent
SATELLITE = PROJECT / "Technical" / "data" / "raw" / "satellite" / "energy"
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "satellite"

# BEA API key (same as bea_api_collector.py)
API_KEY = "857E9ADD-656E-43ED-9598-4EA83299418F"
BASE_URL = "https://apps.bea.gov/api/data"
RATE_LIMIT = 0.5


def api_request(params: dict) -> dict:
    """Make a BEA API request."""
    params["UserID"] = API_KEY
    params["ResultFormat"] = "JSON"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}?{query}"
    try:
        req = Request(url, headers={"User-Agent": "Leontief.io/1.0"})
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        time.sleep(RATE_LIMIT)
        return data
    except URLError as e:
        logger.error(f"API error: {e}")
        return {}


def download_bea_energy_accounts():
    """Attempt to download BEA energy satellite accounts via API.

    BEA provides energy use data through the InputOutput dataset
    as supplementary tables. If not available via API, prints
    manual download instructions.
    """
    SATELLITE.mkdir(parents=True, exist_ok=True)

    logger.info("Checking BEA API for energy satellite accounts...")

    # Try InputOutput dataset supplementary tables
    meta = api_request({
        "method": "GetParameterValues",
        "DatasetName": "InputOutput",
        "ParameterName": "TableID",
    })

    if meta:
        tables = meta.get("BEAAPI", {}).get("Results", {}).get("ParamValue", [])
        energy_tables = [t for t in tables if "energy" in t.get("Desc", "").lower()
                         or "environment" in t.get("Desc", "").lower()]

        if energy_tables:
            for t in energy_tables:
                logger.info(f"  Found: {t['Key']} - {t['Desc']}")
        else:
            logger.info("  No energy-specific tables in InputOutput dataset")

    print("\n" + "=" * 70)
    print("MANUAL DOWNLOAD REQUIRED FOR ENERGY DATA")
    print("=" * 70)
    print("""
BEA Environmental-Economic Accounts (energy satellite data) are not
available via the standard BEA API. Download manually:

1. BEA Energy Use Tables:
   URL: https://apps.bea.gov/iTable/?reqid=161&step=1&isuri=1
   -> Select "Energy Use" -> Download Excel
   -> Save to: Technical/data/raw/satellite/energy/

2. EPA GHG Inventory (Annex tables with sector detail):
   URL: https://www.epa.gov/ghgemissions/inventory-us-greenhouse-gas-emissions-and-sinks
   -> Download "Annex" Excel tables
   -> Save to: Technical/data/raw/satellite/energy/

3. EIA MECS (Manufacturing Energy Consumption Survey):
   URL: https://www.eia.gov/consumption/manufacturing/
   -> Download latest survey data
   -> Save to: Technical/data/raw/satellite/energy/

After downloading, run parse_energy_satellite() to process.
""")


def parse_energy_excel(filepath: Path) -> dict:
    """Parse a downloaded BEA energy satellite Excel file.

    Args:
        filepath: Path to Excel file.

    Returns:
        Dict with year -> pd.Series of energy use by sector.
    """
    import pandas as pd

    logger.info(f"Parsing energy data from {filepath.name}")
    try:
        df = pd.read_excel(filepath, sheet_name=0, header=None)
        logger.info(f"  Shape: {df.shape}")
        return {"raw": df}
    except Exception as e:
        logger.error(f"  Parse error: {e}")
        return {}


def check_satellite_data_status():
    """Report what satellite energy data is available."""
    print("\n--- Energy Satellite Data Status ---")

    files = list(SATELLITE.glob("*"))
    if files:
        print(f"Files in {SATELLITE}:")
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.0f} KB)")
    else:
        print(f"No files in {SATELLITE}")
        print("Run download_bea_energy_accounts() for download instructions.")

    processed = list(PROCESSED.glob("energy*"))
    if processed:
        print(f"\nProcessed files:")
        for f in processed:
            print(f"  {f.name}")
    else:
        print("\nNo processed energy satellite data yet.")


def main():
    logger.info("=" * 70)
    logger.info("ENERGY/EMISSIONS SATELLITE DATA COLLECTOR")
    logger.info("=" * 70)

    SATELLITE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    download_bea_energy_accounts()
    check_satellite_data_status()


if __name__ == "__main__":
    main()
