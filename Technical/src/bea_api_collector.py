"""BEA API Data Collector for Input-Output and GDP-by-Industry tables.

Downloads all available I-O tables (1997-2024) and GDP-by-Industry data
using the BEA API. Saves raw JSON responses and converted CSV files.

BEA API Key: From Robin (Council/Robin/ADMIN/api-keys/economic-data-keys.env)
Base URL: https://apps.bea.gov/api/data

Usage:
    python bea_api_collector.py
"""

import json
import time
import csv
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

API_KEY = "857E9ADD-656E-43ED-9598-4EA83299418F"
BASE_URL = "https://apps.bea.gov/api/data"
RATE_LIMIT = 0.5  # seconds between requests

PROJECT = Path(__file__).parent.parent.parent
INPUTS = PROJECT / "Inputs" / "bea_api"
IO_DIR = INPUTS / "io_tables"
GDP_DIR = INPUTS / "gdp_by_industry"
META_DIR = INPUTS / "metadata"

# I-O Table IDs (discovered via GetParameterValues)
IO_TABLES = {
    61: "Total_Requirements_IxI_Summary",
    60: "Total_Requirements_IxI_Sector",
    57: "Total_Requirements_IxC_Summary",
    56: "Total_Requirements_IxC_Sector",
    59: "Total_Requirements_CxC_Summary",
    58: "Total_Requirements_CxC_Sector",
    259: "Use_of_Commodities_Summary",
    258: "Use_of_Commodities_Sector",
    262: "Supply_of_Commodities_Summary",
    261: "Supply_of_Commodities_Sector",
}

YEARS = list(range(1997, 2025))


def api_request(params: dict) -> dict:
    """Make a BEA API request with rate limiting."""
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
    except (URLError, HTTPError) as e:
        logger.error(f"API error: {e}")
        time.sleep(2)
        return {}


def download_io_tables():
    """Download all I-O tables for all years."""
    IO_DIR.mkdir(parents=True, exist_ok=True)

    # Priority tables: Summary-level (faster, smaller, ~71 sectors)
    priority_tables = [61, 259, 262]  # IxI Total Req, Use, Supply (Summary)

    for table_id in priority_tables:
        table_name = IO_TABLES[table_id]
        logger.info(f"Downloading {table_name} (ID={table_id}) for all years...")

        for year in YEARS:
            out_json = IO_DIR / f"{table_name}_{year}.json"
            out_csv = IO_DIR / f"{table_name}_{year}.csv"

            if out_json.exists():
                logger.info(f"  {year}: already exists, skipping")
                continue

            data = api_request({
                "method": "GetData",
                "DatasetName": "InputOutput",
                "TableID": str(table_id),
                "Year": str(year),
            })

            if not data:
                logger.warning(f"  {year}: empty response")
                continue

            # Save raw JSON
            with open(out_json, "w") as f:
                json.dump(data, f, indent=2)

            # Convert to CSV
            try:
                rows = data["BEAAPI"]["Results"]["Data"]
                if rows:
                    with open(out_csv, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                    logger.info(f"  {year}: {len(rows)} rows saved")
                else:
                    logger.warning(f"  {year}: no data rows")
            except (KeyError, TypeError) as e:
                logger.warning(f"  {year}: parse error: {e}")

    logger.info(f"I-O table download complete. Files in: {IO_DIR}")


def download_gdp_by_industry():
    """Download GDP-by-Industry tables."""
    GDP_DIR.mkdir(parents=True, exist_ok=True)

    # First discover available tables
    logger.info("Discovering GDPbyIndustry table IDs...")
    meta = api_request({
        "method": "GetParameterValues",
        "DatasetName": "GDPbyIndustry",
        "ParameterName": "TableID",
    })

    if meta:
        tables = meta.get("BEAAPI", {}).get("Results", {}).get("ParamValue", [])
        logger.info(f"Found {len(tables)} GDPbyIndustry tables")

        # Save metadata
        with open(META_DIR / "gdp_by_industry_tables.json", "w") as f:
            json.dump(meta, f, indent=2)

        for t in tables:
            print(f"  {t['Key']}: {t['Desc']}")

        # Download key tables: Value Added, Gross Output, Compensation
        # These are typically TableIDs 1 (VA), 6 (Gross Output), etc.
        # Download all available
        for table in tables:
            tid = table["Key"]
            desc = table["Desc"].replace(" ", "_").replace(",", "")[:60]
            out_json = GDP_DIR / f"gdpind_{tid}_{desc}.json"

            if out_json.exists():
                logger.info(f"  Table {tid}: already exists, skipping")
                continue

            logger.info(f"  Downloading Table {tid}: {table['Desc'][:60]}...")
            data = api_request({
                "method": "GetData",
                "DatasetName": "GDPbyIndustry",
                "TableID": str(tid),
                "Frequency": "A",
                "Industry": "ALL",
                "Year": "ALL",
            })

            if data:
                with open(out_json, "w") as f:
                    json.dump(data, f, indent=2)

                try:
                    rows = data["BEAAPI"]["Results"]["Data"]
                    logger.info(f"    {len(rows)} rows")
                except (KeyError, TypeError):
                    logger.warning(f"    No data rows")


def download_underlying_gdp():
    """Download UnderlyingGDPbyIndustry for finer detail."""
    GDP_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Discovering UnderlyingGDPbyIndustry tables...")
    meta = api_request({
        "method": "GetParameterValues",
        "DatasetName": "UnderlyingGDPbyIndustry",
        "ParameterName": "TableID",
    })

    if meta:
        tables = meta.get("BEAAPI", {}).get("Results", {}).get("ParamValue", [])
        with open(META_DIR / "underlying_gdp_tables.json", "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Found {len(tables)} UnderlyingGDPbyIndustry tables")
        for t in tables:
            print(f"  {t['Key']}: {t['Desc']}")


def main():
    logger.info("=" * 70)
    logger.info("BEA API COLLECTOR — Leontief.io")
    logger.info("=" * 70)

    # Ensure directories exist
    for d in [IO_DIR, GDP_DIR, META_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Download I-O tables (priority: summary-level)
    download_io_tables()

    # Step 2: Download GDP-by-Industry
    download_gdp_by_industry()

    # Step 3: Discover underlying detail (metadata only for now)
    download_underlying_gdp()

    logger.info("=" * 70)
    logger.info("ALL DOWNLOADS COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
