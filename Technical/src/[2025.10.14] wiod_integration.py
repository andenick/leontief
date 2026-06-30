#!/usr/bin/env python3
"""
WIOD Integration Module for Leontief
Leontief - Multi-Regional Input-Output Analysis Integration

This module integrates WIOD (World Input-Output Database) data processing
capabilities with the existing Leontief framework, enabling international
and multi-regional economic analysis alongside existing U.S. BEA data.

Author: Claude Code Assistant
Date: 2025-10-14
Version: 1.0
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime

# Import existing Leontief components
try:
    from io_loader import IOTableLoader
    from io_analysis import IOAnalyzer
except ImportError:
    print("Warning: Some Leontief modules not available. Integration will be limited.")
    IOTableLoader = None
    IOAnalyzer = None

# Import WIOD processor
try:
    import sys
    wiod_processor_path = Path(__file__).parent / '[2025.10.14] wiod_processor.py'
    exec(open(wiod_processor_path).read())
except ImportError:
    print("Error: WIOD processor not found. Please ensure wiod_processor.py is available.")
    WIODProcessor = None
except NameError:
    # Handle when __file__ is not defined (during exec)
    try:
        wiod_processor_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/src/[2025.10.14] wiod_processor.py")
        exec(open(wiod_processor_path).read())
    except Exception as e:
        print(f"Error loading WIOD processor: {e}")
        WIODProcessor = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WIODIntegration:
    """
    WIOD Integration for Leontief Platform

    Provides unified interface for loading, processing, and analyzing both
    U.S. BEA data and international WIOD data within the Leontief framework.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize WIOD Integration

        Args:
            data_dir: Base data directory for all I-O data sources
        """
        if data_dir is None:
            self.data_dir = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data")
        else:
            self.data_dir = Path(data_dir)

        # Initialize data processors
        self.wiod_processor = WIODProcessor(base_path=self.data_dir / "raw/wiod/2016_release")

        # Initialize Leontief components if available
        if IOTableLoader:
            self.io_loader = IOTableLoader(data_dir=self.data_dir / "raw")
        else:
            self.io_loader = None
            logger.warning("IOTableLoader not available - BEA data integration limited")

        if IOAnalyzer:
            self.io_analyzer = IOAnalyzer()
        else:
            self.io_analyzer = None
            logger.warning("IOAnalyzer not available - analysis capabilities limited")

        # Cache for loaded data
        self.data_cache = {}
        self.available_sources = self._scan_available_data()

        logger.info("WIOD Integration initialized successfully")
        logger.info(f"Available data sources: {list(self.available_sources.keys())}")

    def _scan_available_data(self) -> Dict[str, Dict]:
        """
        Scan available data sources and their coverage

        Returns:
            Dictionary of available data sources with metadata
        """
        sources = {}

        # Scan BEA data
        bea_dir = self.data_dir / "raw/bea"
        if bea_dir.exists():
            bea_years = []
            for year_dir in bea_dir.iterdir():
                if year_dir.is_dir() and year_dir.name.replace("_benchmark", "").isdigit():
                    bea_years.append(int(year_dir.name.replace("_benchmark", "")))

            if bea_years:
                sources["BEA"] = {
                    "type": "national",
                    "country": "USA",
                    "years": sorted(bea_years),
                    "classification": "NAICS",
                    "detail_level": "high"
                }

        # Scan WIOD data
        wiot_dir = self.data_dir / "raw/wiod/2016_release/WIOT"
        if wiot_dir.exists():
            wiot_files = list(wiot_dir.glob("WIOT*.xlsx"))
            wiot_years = []
            for file in wiot_files:
                year_match = file.name.replace("WIOT", "").replace("_October16.xlsx", "")
                if year_match.isdigit():
                    wiot_years.append(int(year_match))

            if wiot_years:
                sources["WIOD"] = {
                    "type": "multi_regional",
                    "countries": len(self.wiod_processor.countries),
                    "years": sorted(wiot_years),
                    "classification": "ISIC Rev. 3",
                    "detail_level": "medium"
                }

        return sources

    def list_available_data(self) -> pd.DataFrame:
        """
        List all available data sources in a tabular format

        Returns:
            DataFrame with available data information
        """
        data_info = []

        for source, metadata in self.available_sources.items():
            data_info.append({
                "source": source,
                "type": metadata.get("type", "unknown"),
                "country": metadata.get("country", "multi"),
                "years": f"{min(metadata['years'])}-{max(metadata['years'])}" if metadata.get("years") else "N/A",
                "classification": metadata.get("classification", "unknown"),
                "detail_level": metadata.get("detail_level", "unknown")
            })

        return pd.DataFrame(data_info)

    def load_wiod_data(self, years: Optional[List[int]] = None,
                      countries: Optional[List[str]] = None) -> Dict:
        """
        Load WIOD data for specified years and countries

        Args:
            years: List of years to load (None for all available)
            countries: List of countries to load (None for all available)

        Returns:
            Dictionary containing loaded WIOD data
        """
        if not self.available_sources.get("WIOD"):
            raise ValueError("WIOD data not available. Please download WIOD data first.")

        available_years = self.available_sources["WIOD"]["years"]
        if years is None:
            years = available_years
        else:
            years = [y for y in years if y in available_years]

        if countries is None:
            countries = self.wiod_processor.countries

        logger.info(f"Loading WIOD data for years {years} and {len(countries)} countries")

        loaded_data = {}

        for year in years:
            try:
                # Load WIOT data
                wiot_data = self.wiod_processor.process_wiot_table(year)

                # Load NIOT data for country-specific analysis
                niot_data = self.wiod_processor.process_niot_table(year)

                # Load SEA data
                sea_data = self.wiod_processor.process_sea_data()

                # Filter for specified countries if provided
                if countries and wiot_data is not None:
                    wiot_data = self._filter_countries(wiot_data, countries)
                if countries and niot_data:
                    niot_data = {c: niot_data.get(c) for c in countries if c in niot_data}

                loaded_data[year] = {
                    "wiot": wiot_data,
                    "niot": niot_data,
                    "sea": sea_data,
                    "metadata": {
                        "year": year,
                        "countries": countries,
                        "sectors": len(self.wiod_processor.sectors),
                        "source": "WIOD 2016",
                        "classification": "ISIC Rev. 3"
                    }
                }

                logger.info(f"Successfully loaded WIOD data for {year}")

            except Exception as e:
                logger.error(f"Error loading WIOD data for {year}: {e}")
                continue

        return loaded_data

    def _filter_countries(self, data: pd.DataFrame, countries: List[str]) -> pd.DataFrame:
        """
        Filter WIOD data to include only specified countries

        Args:
            data: WIOD DataFrame
            countries: List of country codes to keep

        Returns:
            Filtered DataFrame
        """
        if data is None or data.empty:
            return data

        # WIOD format: country_sector labels
        filtered_indices = []
        filtered_columns = []

        for idx, label in enumerate(data.iloc[:, 0]):
            if isinstance(label, str):
                country = label.split("_")[0] if "_" in label else label
                if country in countries:
                    filtered_indices.append(idx)

        for col in data.columns[1:]:  # Skip first column (labels)
            if isinstance(col, str):
                country = col.split("_")[0] if "_" in col else col
                if country in countries:
                    filtered_columns.append(col)

        # Apply filters
        if filtered_indices and filtered_columns:
            filtered_data = data.iloc[filtered_indices]
            filtered_data = filtered_data[[data.columns[0]] + filtered_columns]
            return filtered_data
        else:
            logger.warning("No data matches country filter. Returning original data.")
            return data

    def load_bea_data(self, years: Optional[List[int]] = None) -> Dict:
        """
        Load BEA data for specified years

        Args:
            years: List of years to load (None for all available)

        Returns:
            Dictionary containing loaded BEA data
        """
        if not self.io_loader:
            raise ValueError("IOTableLoader not available. Cannot load BEA data.")

        if not self.available_sources.get("BEA"):
            raise ValueError("BEA data not available.")

        available_years = self.available_sources["BEA"]["years"]
        if years is None:
            years = available_years
        else:
            years = [y for y in years if y in available_years]

        logger.info(f"Loading BEA data for years {years}")

        loaded_data = {}

        for year in years:
            try:
                # Look for BEA files
                bea_dir = self.data_dir / "raw/bea" / f"{year}_benchmark"

                # Try to load use table
                use_files = list(bea_dir.glob("*use*.xlsx"))
                make_files = list(bea_dir.glob("*make*.xlsx"))
                summary_files = list(bea_dir.glob("*summary*.xlsx"))

                year_data = {"metadata": {
                    "year": year,
                    "country": "USA",
                    "source": "BEA",
                    "classification": "NAICS",
                    "vintage": f"{year} Benchmark"
                }}

                if use_files:
                    use_table = self.io_loader.load_bea_table(use_files[0], year, "use")
                    year_data["use"] = use_table

                if make_files:
                    make_table = self.io_loader.load_bea_table(make_files[0], year, "make")
                    year_data["make"] = make_table

                if summary_files:
                    summary_table = self.io_loader.load_bea_table(summary_files[0], year, "summary")
                    year_data["summary"] = summary_table

                loaded_data[year] = year_data
                logger.info(f"Successfully loaded BEA data for {year}")

            except Exception as e:
                logger.error(f"Error loading BEA data for {year}: {e}")
                continue

        return loaded_data

    def create_unified_dataset(self, years: Optional[List[int]] = None,
                              include_wiod: bool = True,
                              include_bea: bool = True) -> Dict:
        """
        Create a unified dataset combining WIOD and BEA data

        Args:
            years: Years to include in unified dataset
            include_wiod: Whether to include WIOD data
            include_bea: Whether to include BEA data

        Returns:
            Unified dataset dictionary
        """
        unified_data = {
            "metadata": {
                "created_date": datetime.now().isoformat(),
                "sources": [],
                "year_range": None,
                "countries": [],
                "sectors": {}
            },
            "data": {}
        }

        # Determine overlapping years
        wiod_years = self.available_sources.get("WIOD", {}).get("years", [])
        bea_years = self.available_sources.get("BEA", {}).get("years", [])

        if years is None:
            # Use intersection of available years
            years = sorted(list(set(wiod_years) & set(bea_years)))
            if not years:
                years = sorted(list(set(wiod_years + bea_years)))

        unified_data["metadata"]["year_range"] = f"{min(years)}-{max(years)}"

        # Load WIOD data
        if include_wiod and self.available_sources.get("WIOD"):
            try:
                wiod_data = self.load_wiod_data(years)
                unified_data["data"]["wiod"] = wiod_data
                unified_data["metadata"]["sources"].append("WIOD")
                unified_data["metadata"]["countries"].extend(self.wiod_processor.countries)
                unified_data["metadata"]["sectors"]["wiod"] = len(self.wiod_processor.sectors)
                logger.info(f"Added WIOD data for {len(wiod_data)} years")
            except Exception as e:
                logger.error(f"Error loading WIOD data: {e}")

        # Load BEA data
        if include_bea and self.available_sources.get("BEA"):
            try:
                bea_data = self.load_bea_data(years)
                unified_data["data"]["bea"] = bea_data
                unified_data["metadata"]["sources"].append("BEA")
                unified_data["metadata"]["countries"].append("USA")
                unified_data["metadata"]["sectors"]["bea"] = "high"  # BEA has higher detail
                logger.info(f"Added BEA data for {len(bea_data)} years")
            except Exception as e:
                logger.error(f"Error loading BEA data: {e}")

        # Remove duplicate countries
        unified_data["metadata"]["countries"] = list(set(unified_data["metadata"]["countries"]))

        return unified_data

    def create_cross_walk(self) -> pd.DataFrame:
        """
        Create classification cross-walk between WIOD and BEA sectors

        Returns:
            DataFrame mapping WIOD sectors to BEA sectors where possible
        """
        # This is a simplified cross-walk - in practice would need detailed mapping
        wiod_sectors = self.wiod_processor.sectors

        # Example mappings (would need to be expanded based on actual classifications)
        cross_walk = []

        for wiod_code, wiod_desc in wiod_sectors[:10]:  # Sample first 10 for demo
            # Simplified mapping logic
            bea_equivalent = self._map_wiod_to_bea(wiod_code, wiod_desc)
            cross_walk.append({
                "wiod_code": wiod_code,
                "wiod_description": wiod_desc,
                "bea_equivalent": bea_equivalent,
                "mapping_confidence": "medium"
            })

        return pd.DataFrame(cross_walk)

    def _map_wiod_to_bea(self, wiod_code: str, wiod_desc: str) -> str:
        """
        Map WIOD sector to BEA sector (simplified)

        Args:
            wiod_code: WIOD sector code
            wiod_desc: WIOD sector description

        Returns:
            Best guess BEA equivalent
        """
        # This is a placeholder - actual mapping would require detailed classification analysis
        if "Agriculture" in wiod_desc or wiod_code.startswith("A"):
            return "11 Agriculture, Forestry, Fishing and Hunting"
        elif "Mining" in wiod_desc or wiod_code.startswith("B"):
            return "21 Mining, Quarrying, and Oil and Gas Extraction"
        elif "Manufacturing" in wiod_desc or wiod_code.startswith("C"):
            return "31-33 Manufacturing"
        elif "Construction" in wiod_desc or wiod_code.startswith("F"):
            return "23 Construction"
        elif "Wholesale" in wiod_desc or "Retail" in wiod_desc or wiod_code.startswith("G"):
            return "42-44 Wholesale and Retail Trade"
        elif "Transport" in wiod_desc or wiod_code.startswith("H"):
            return "48-49 Transportation and Warehousing"
        elif "Finance" in wiod_desc or "Insurance" in wiod_desc or wiod_code.startswith("K"):
            return "52 Finance and Insurance"
        else:
            return "Other Services"

    def run_comparative_analysis(self, year: int,
                               countries: Optional[List[str]] = None) -> Dict:
        """
        Run comparative analysis between WIOD and BEA data

        Args:
            year: Year to analyze
            countries: Countries to include in WIOD analysis

        Returns:
            Analysis results dictionary
        """
        results = {
            "year": year,
            "comparison": {},
            "insights": []
        }

        try:
            # Load data for the specified year
            if self.available_sources.get("WIOD") and year in self.available_sources["WIOD"]["years"]:
                wiod_data = self.load_wiod_data([year], countries)
                results["wiod_available"] = True
                results["wiod_countries"] = list(wiod_data.get(year, {}).get("niot", {}).keys())
            else:
                results["wiod_available"] = False

            if self.available_sources.get("BEA") and year in self.available_sources["BEA"]["years"]:
                bea_data = self.load_bea_data([year])
                results["bea_available"] = True
            else:
                results["bea_available"] = False

            # Generate insights
            if results["wiod_available"] and results["bea_available"]:
                results["insights"].append("Both WIOD and BEA data available for comparison")
                results["insights"].append("Can analyze U.S. position in global value chains")
            elif results["wiod_available"]:
                results["insights"].append("WIOD data available for international analysis")
            elif results["bea_available"]:
                results["insights"].append("BEA data available for U.S. domestic analysis")

        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            results["error"] = str(e)

        return results

    def export_unified_data(self, unified_data: Dict,
                          output_dir: Optional[str] = None) -> bool:
        """
        Export unified dataset to Excel format

        Args:
            unified_data: Unified dataset dictionary
            output_dir: Output directory (None for default)

        Returns:
            True if successful, False otherwise
        """
        try:
            if output_dir is None:
                output_dir = self.data_dir / "processed" / "unified_datasets"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"unified_io_data_{timestamp}.xlsx"

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write metadata
                metadata_df = pd.DataFrame([unified_data["metadata"]])
                metadata_df.to_excel(writer, sheet_name="Metadata", index=False)

                # Write WIOD data summary
                if "wiod" in unified_data["data"]:
                    wiod_summary = []
                    for year, data in unified_data["data"]["wiod"].items():
                        wiod_summary.append({
                            "year": year,
                            "countries": len(data.get("niot", {})),
                            "data_available": data.get("wiot") is not None
                        })
                    pd.DataFrame(wiod_summary).to_excel(writer, sheet_name="WIOD_Summary", index=False)

                # Write BEA data summary
                if "bea" in unified_data["data"]:
                    bea_summary = []
                    for year, data in unified_data["data"]["bea"].items():
                        bea_summary.append({
                            "year": year,
                            "use_table": "use" in data,
                            "make_table": "make" in data,
                            "summary_table": "summary" in data
                        })
                    pd.DataFrame(bea_summary).to_excel(writer, sheet_name="BEA_Summary", index=False)

                # Write classification cross-walk
                cross_walk = self.create_cross_walk()
                cross_walk.to_excel(writer, sheet_name="Classification_Crosswalk", index=False)

            logger.info(f"Unified data exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting unified data: {e}")
            return False

    def get_integration_status(self) -> Dict:
        """
        Get current integration status and capabilities

        Returns:
            Status dictionary
        """
        status = {
            "data_sources": self.available_sources,
            "components": {
                "wiod_processor": self.wiod_processor is not None,
                "io_loader": self.io_loader is not None,
                "io_analyzer": self.io_analyzer is not None
            },
            "capabilities": {
                "load_wiod": self.wiod_processor is not None,
                "load_bea": self.io_loader is not None,
                "comparative_analysis": self.wiod_processor is not None and self.io_loader is not None,
                "unified_datasets": True,
                "classification_mapping": True
            },
            "data_coverage": {
                "total_years": len(set(
                    self.available_sources.get("WIOD", {}).get("years", []) +
                    self.available_sources.get("BEA", {}).get("years", [])
                )),
                "countries": len(self.available_sources.get("WIOD", {}).get("countries", [])),
                "sources": list(self.available_sources.keys())
            }
        }

        return status


def main():
    """Main function for demonstrating WIOD integration"""
    try:
        # Initialize integration
        integration = WIODIntegration()

        print("WIOD Integration for Leontief")
        print("=" * 50)

        # Show available data
        print("\nAvailable Data Sources:")
        available_data = integration.list_available_data()
        print(available_data.to_string(index=False))

        # Show integration status
        print("\nIntegration Status:")
        status = integration.get_integration_status()
        print(f"Data Sources: {status['data_coverage']['sources']}")
        print(f"Total Years: {status['data_coverage']['total_years']}")
        print(f"Countries: {status['data_coverage']['countries']}")
        print(f"Components Available: {sum(status['components'].values())}/{len(status['components'])}")

        # Example: Create unified dataset for overlapping years
        if len(status['data_coverage']['sources']) > 1:
            print("\nCreating unified dataset...")
            unified_data = integration.create_unified_dataset(years=[2010, 2011])
            print(f"Created unified dataset with {len(unified_data['metadata']['sources'])} sources")

            # Export unified data
            success = integration.export_unified_data(unified_data)
            if success:
                print("Unified dataset exported successfully")

        print("\nWIOD integration ready for use!")

    except Exception as e:
        print(f"Error in WIOD integration demo: {e}")
        logger.error(f"WIOD integration demo failed: {e}")


if __name__ == "__main__":
    main()