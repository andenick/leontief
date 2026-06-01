"""Download international trade data from BEA for RCA analysis.

Source: BEA International Trade in Goods and Services
API Dataset: ITA (International Transactions Accounts)

Also extends bea_api_collector for regional GDP by industry
(needed for interregional I-O analysis).
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
TRADE_DIR = PROJECT / "Technical" / "data" / "raw" / "satellite" / "trade"
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


def discover_trade_tables():
    """List available International Transactions tables."""
    logger.info("Discovering ITA (trade) tables...")

    for dataset in ["ITA", "IntlServTrade"]:
        meta = api_request({
            "method": "GetParameterValues",
            "DatasetName": dataset,
            "ParameterName": "Indicator",
        })

        if meta:
            params = meta.get("BEAAPI", {}).get("Results", {}).get("ParamValue", [])
            logger.info(f"  {dataset}: {len(params)} indicators")
            for p in params[:10]:
                logger.info(f"    {p.get('Key', '?')}: {p.get('Desc', '?')[:60]}")


def download_trade_by_industry():
    """Download US exports and imports by industry.

    Uses BEA International Trade in Services and International
    Transactions data.
    """
    TRADE_DIR.mkdir(parents=True, exist_ok=True)

    # Try ITA dataset for goods trade
    out_json = TRADE_DIR / "ita_trade_goods.json"
    if not out_json.exists():
        logger.info("Downloading ITA trade data...")
        data = api_request({
            "method": "GetData",
            "DatasetName": "ITA",
            "Indicator": "BalGds",
            "AreaOrCountry": "AllCountries",
            "Frequency": "A",
            "Year": "ALL",
        })

        if data:
            with open(out_json, "w") as f:
                json.dump(data, f, indent=2)
            try:
                rows = data["BEAAPI"]["Results"]["Data"]
                logger.info(f"  Trade goods: {len(rows)} rows")
            except (KeyError, TypeError):
                logger.warning("  No data rows in response")
        else:
            logger.warning("  ITA request returned empty")

    # Services trade
    out_json = TRADE_DIR / "intl_services_trade.json"
    if not out_json.exists():
        logger.info("Downloading International Services Trade...")
        data = api_request({
            "method": "GetData",
            "DatasetName": "IntlServTrade",
            "TypeOfService": "ALL",
            "TradeDirection": "ALL",
            "Affiliation": "ALL",
            "AreaOrCountry": "AllCountries",
            "Year": "ALL",
        })

        if data:
            with open(out_json, "w") as f:
                json.dump(data, f, indent=2)
            try:
                rows = data["BEAAPI"]["Results"]["Data"]
                logger.info(f"  Services trade: {len(rows)} rows")
            except (KeyError, TypeError):
                pass


def download_regional_gdp_by_industry():
    """Download state-level GDP by industry for interregional I-O.

    Uses BEA Regional dataset: SQGDP (State Quarterly GDP by Industry).
    """
    REGIONAL_DIR = PROJECT / "Technical" / "data" / "raw" / "satellite" / "trade"
    REGIONAL_DIR.mkdir(parents=True, exist_ok=True)

    out_json = REGIONAL_DIR / "regional_gdp_by_industry.json"
    if out_json.exists():
        logger.info("Regional GDP data already exists, skipping")
        return

    logger.info("Downloading Regional GDP by industry...")

    # BEA Regional dataset: SAGDP2N = GDP by industry (NAICS)
    data = api_request({
        "method": "GetData",
        "DatasetName": "Regional",
        "TableName": "SAGDP2N",
        "LineCode": "1",
        "GeoFips": "STATE",
        "Year": "ALL",
    })

    if data:
        with open(out_json, "w") as f:
            json.dump(data, f, indent=2)
        try:
            rows = data["BEAAPI"]["Results"]["Data"]
            logger.info(f"  Regional GDP: {len(rows)} rows")
        except (KeyError, TypeError):
            pass
    else:
        logger.warning("  Regional dataset request failed")
        logger.info("  This data may require different API parameters.")


def parse_trade_data(filepath: Path) -> dict:
    """Parse downloaded BEA trade JSON.

    Returns:
        Dict of year -> pd.DataFrame with exports, imports by sector/country.
    """
    import pandas as pd

    with open(filepath) as f:
        data = json.load(f)

    try:
        rows = data["BEAAPI"]["Results"]["Data"]
    except (KeyError, TypeError):
        return {}

    df = pd.DataFrame(rows)
    logger.info(f"  Parsed {len(df)} records from {filepath.name}")
    return {"raw": df}


def check_satellite_data_status():
    """Report available trade satellite data."""
    print("\n--- Trade Satellite Data Status ---")

    files = list(TRADE_DIR.glob("*"))
    if files:
        print(f"Files in {TRADE_DIR}:")
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.0f} KB)")
    else:
        print(f"No files in {TRADE_DIR}")


def main():
    logger.info("=" * 70)
    logger.info("TRADE & REGIONAL SATELLITE DATA COLLECTOR")
    logger.info("=" * 70)

    TRADE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    discover_trade_tables()
    download_trade_by_industry()
    download_regional_gdp_by_industry()
    check_satellite_data_status()


if __name__ == "__main__":
    main()
