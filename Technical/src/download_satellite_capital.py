"""Download capital stock data from BEA Fixed Assets accounts.

Source: BEA Fixed Assets Table 3.1ESI (Current-Cost Net Stock of
Private Fixed Assets by Industry). Available via BEA API.

API Dataset: FixedAssets
"""

import json
import csv
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent.parent
SATELLITE = PROJECT / "Technical" / "data" / "raw" / "satellite" / "capital"
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "satellite"

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


def discover_fixed_assets_tables():
    """List available FixedAssets tables."""
    logger.info("Discovering FixedAssets tables...")
    meta = api_request({
        "method": "GetParameterValues",
        "DatasetName": "FixedAssets",
        "ParameterName": "TableName",
    })

    tables = []
    if meta:
        params = meta.get("BEAAPI", {}).get("Results", {}).get("ParamValue", [])
        for p in params:
            tables.append(p)
            logger.info(f"  {p.get('Key', p.get('TableName', '?'))}: {p.get('Desc', p.get('Description', '?'))}")

    return tables


def download_net_stock_by_industry():
    """Download Table 3.1ESI: Current-Cost Net Stock of Private Fixed Assets by Industry."""
    SATELLITE.mkdir(parents=True, exist_ok=True)

    out_json = SATELLITE / "fixed_assets_net_stock.json"
    if out_json.exists():
        logger.info("Net stock data already exists, skipping download")
        return

    logger.info("Downloading Fixed Assets net stock by industry...")

    data = api_request({
        "method": "GetData",
        "DatasetName": "FixedAssets",
        "TableName": "FAAt301",
        "Frequency": "A",
        "Year": "ALL",
    })

    if not data:
        # Try alternative table name format
        data = api_request({
            "method": "GetData",
            "DatasetName": "FixedAssets",
            "TableName": "FAAt301-ESI",
            "Frequency": "A",
            "Year": "ALL",
        })

    if data:
        with open(out_json, "w") as f:
            json.dump(data, f, indent=2)

        try:
            rows = data["BEAAPI"]["Results"]["Data"]
            logger.info(f"  Downloaded {len(rows)} data points")

            out_csv = SATELLITE / "fixed_assets_net_stock.csv"
            with open(out_csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        except (KeyError, TypeError) as e:
            logger.warning(f"  Parse error: {e}")
    else:
        logger.warning("  No data returned. Table name may differ.")
        logger.info("  Run discover_fixed_assets_tables() to find correct table name.")


def download_depreciation_by_industry():
    """Download capital consumption (depreciation) by industry."""
    SATELLITE.mkdir(parents=True, exist_ok=True)

    out_json = SATELLITE / "fixed_assets_depreciation.json"
    if out_json.exists():
        logger.info("Depreciation data already exists, skipping download")
        return

    logger.info("Downloading depreciation by industry...")
    data = api_request({
        "method": "GetData",
        "DatasetName": "FixedAssets",
        "TableName": "FAAt403",
        "Frequency": "A",
        "Year": "ALL",
    })

    if data:
        with open(out_json, "w") as f:
            json.dump(data, f, indent=2)
        try:
            rows = data["BEAAPI"]["Results"]["Data"]
            logger.info(f"  Downloaded {len(rows)} data points")
        except (KeyError, TypeError):
            pass


def parse_capital_data(filepath: Path) -> dict:
    """Parse downloaded capital stock JSON into sector-indexed Series.

    Returns:
        Dict of year -> pd.Series (capital stock by NAICS industry).
    """
    import pandas as pd

    with open(filepath) as f:
        data = json.load(f)

    try:
        rows = data["BEAAPI"]["Results"]["Data"]
    except (KeyError, TypeError):
        return {}

    records = []
    for r in rows:
        try:
            records.append({
                "year": int(r.get("TimePeriod", r.get("Year", 0))),
                "industry": r.get("IndustrYDescription", r.get("Industry", "")),
                "industry_code": r.get("Industry", ""),
                "value": float(r.get("DataValue", "0").replace(",", "")),
            })
        except (ValueError, TypeError):
            continue

    df = pd.DataFrame(records)
    if df.empty:
        return {}

    result = {}
    for year in df["year"].unique():
        year_data = df[df["year"] == year].set_index("industry_code")["value"]
        result[int(year)] = year_data

    return result


def main():
    logger.info("=" * 70)
    logger.info("CAPITAL STOCK SATELLITE DATA COLLECTOR")
    logger.info("=" * 70)

    SATELLITE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    discover_fixed_assets_tables()
    download_net_stock_by_industry()
    download_depreciation_by_industry()

    logger.info("Capital data collection complete.")
    logger.info(f"Files in: {SATELLITE}")


if __name__ == "__main__":
    main()
