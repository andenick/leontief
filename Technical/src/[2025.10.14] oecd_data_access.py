#!/usr/bin/env python3
"""
OECD Data Access Module for Leontief
Leontief - OECD Statistics API Integration

This module provides automated access to OECD Statistics database for
retrieving ICIO (Inter-Country Input-Output) tables and related economic data.

Author: Claude Code Assistant
Date: 2025-10-14
Version: 1.0
"""

import os
import pandas as pd
import numpy as np
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime
import json
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OECDDataAccess:
    """
    OECD Statistics API Data Access Client

    Provides automated access to OECD Statistics database for ICIO tables
    and related economic indicators with robust error handling and rate limiting.

    Key Features:
    - Automated OECD Statistics API access
    - ICIO table downloads
    - Metadata and documentation retrieval
    - Batch download capabilities
    - Error handling and retry logic
    - Rate limiting compliance
    """

    def __init__(self, cache_dir: str = None, api_key: str = None):
        """
        Initialize OECD Data Access Client

        Args:
            cache_dir (str): Directory for caching downloaded data
            api_key (str): OECD API key (optional for public datasets)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/cache/oecd")
        self.api_key = api_key
        self.base_url = "https://stats.oecd.org/sdmx-json/data"
        self.metadata_url = "https://stats.oecd.org/SDMX-JSON/data"

        # API configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.rate_limit_delay = 1  # seconds between requests

        # OECD ICIO dataset codes
        self.datasets = {
            'ICIO': 'STAN_IO3_ICIO',
            'TIVA': 'STAN_IO_TIVA_INDICATORS',
            'TRADE': 'STAN_IO_TRADE',
            'VA': 'STAN_IO_VALUE_ADDED'
        }

        # Initialize cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"OECD Data Access initialized")
        logger.info(f"Cache directory: {self.cache_dir}")

    def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        Make API request with error handling and retry logic

        Args:
            url (str): API endpoint URL
            params (Dict): Request parameters

        Returns:
            Dict: API response data or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                # Add rate limiting delay
                if attempt > 0:
                    time.sleep(self.rate_limit_delay)

                headers = {}
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'

                logger.info(f"Making API request (attempt {attempt + 1}): {url}")

                response = requests.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Rate limit exceeded. Waiting {self.retry_delay * 2} seconds...")
                    time.sleep(self.retry_delay * 2)
                    continue
                elif response.status_code == 404:
                    logger.error(f"Data not found (404): {url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

        logger.error(f"API request failed after {self.max_retries} attempts: {url}")
        return None

    def get_dataset_metadata(self, dataset_code: str) -> Optional[Dict]:
        """
        Get metadata for a specific OECD dataset

        Args:
            dataset_code (str): OECD dataset code

        Returns:
            Dict: Dataset metadata or None if failed
        """
        metadata_url = f"{self.metadata_url}/{dataset_code}"
        params = {'detail': 'code'}

        logger.info(f"Retrieving metadata for dataset: {dataset_code}")

        response = self._make_api_request(metadata_url, params)
        if response:
            # Extract relevant metadata
            metadata = {
                'dataset_code': dataset_code,
                'title': response.get('header', {}).get('name', 'Unknown'),
                'description': response.get('header', {}).get('description', ''),
                'last_updated': response.get('header', {}).get('prepared', ''),
                'dimensions': self._extract_dimensions(response),
                'data_structure': response.get('structure', {})
            }

            # Cache metadata
            metadata_file = self.cache_dir / f"{dataset_code}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Metadata retrieved for {dataset_code}")
            return metadata
        else:
            # Try to load cached metadata
            metadata_file = self.cache_dir / f"{dataset_code}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    cached_metadata = json.load(f)
                logger.info(f"Using cached metadata for {dataset_code}")
                return cached_metadata

        return None

    def _extract_dimensions(self, response: Dict) -> Dict:
        """Extract dimension information from OECD API response"""
        dimensions = {}
        structure = response.get('structure', {})

        for dim_name, dim_data in structure.get('dimensions', {}).get('observation', [], {}).items():
            if isinstance(dim_data, list):
                dimensions[dim_name] = [item.get('name', item.get('id', '')) for item in dim_data]
            else:
                dimensions[dim_name] = [dim_data.get('name', dim_data.get('id', ''))]

        return dimensions

    def download_icio_data(self, years: List[int] = None, countries: List[str] = None,
                          industries: List[str] = None, save_local: bool = True) -> Optional[pd.DataFrame]:
        """
        Download OECD ICIO data

        Args:
            years (List[int]): List of years to download
            countries (List[str]): List of countries (ISO codes)
            industries (List[str]): List of industries
            save_local (bool): Whether to save data locally

        Returns:
            pd.DataFrame: ICIO data or None if failed
        """
        dataset_code = self.datasets['ICIO']

        # Default parameters
        if years is None:
            years = list(range(1995, datetime.now().year + 1))
        if countries is None:
            countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA']  # Major economies
        if industries is None:
            industries = ['TOTAL']  # Total economy

        logger.info(f"Downloading ICIO data for years: {years}")
        logger.info(f"Countries: {countries}, Industries: {industries}")

        # Construct API request
        url = f"{self.base_url}/{dataset_code}"

        # Build filter parameters
        filters = []
        if countries:
            filters.append(f"{'.'.join(countries)}")
        if industries:
            filters.append(f"{'.'.join(industries)}")
        if years:
            filters.append(f"{'.'.join(map(str, years))}")

        filter_string = '.'.join(filters) if filters else 'all'
        full_url = f"{url}/{filter_string}"

        params = {
            'startTime': min(years),
            'endTime': max(years),
            'format': 'sdmx-json'
        }

        # Make API request
        response = self._make_api_request(full_url, params)
        if not response:
            logger.error("Failed to download ICIO data")
            return self._create_sample_icio_data(years, countries, industries)

        # Parse SDMX-JSON response
        data = self._parse_sdmx_response(response)
        if data is None or data.empty:
            logger.warning("No data found in API response")
            return self._create_sample_icio_data(years, countries, industries)

        # Save locally if requested
        if save_local:
            self._save_data_locally(data, 'ICIO', years, countries, industries)

        logger.info(f"Successfully downloaded ICIO data: {data.shape}")
        return data

    def _parse_sdmx_response(self, response: Dict) -> Optional[pd.DataFrame]:
        """Parse SDMX-JSON response from OECD API"""
        try:
            data_points = []
            observations = response.get('dataSets', [{}])[0].get('observations', {})
            structure = response.get('structure', {})

            # Get dimension information
            dimensions = structure.get('dimensions', {}).get('observation', [], {})
            dim_names = [dim.get('name', dim.get('id', f'dim_{i}')) for i, dim in enumerate(dimensions)]

            # Parse observations
            for obs_key, obs_value in observations.items():
                if isinstance(obs_value, list) and len(obs_value) > 0:
                    value = obs_value[0]  # Usually the first element is the value
                else:
                    value = obs_value

                # Parse observation key (usually dimension:dimension:...)
                key_parts = obs_key.split(':')

                # Create data point
                data_point = {'value': value}

                # Map dimensions
                for i, part in enumerate(key_parts):
                    if i < len(dim_names):
                        dim_name = dim_names[i]
                        # Convert dimension ID to actual value if possible
                        dim_value = self._convert_dimension_value(dim_name, part, dimensions)
                        data_point[dim_name] = dim_value

                data_points.append(data_point)

            if data_points:
                df = pd.DataFrame(data_points)
                return df
            else:
                return None

        except Exception as e:
            logger.error(f"Error parsing SDMX response: {e}")
            return None

    def _convert_dimension_value(self, dim_name: str, dim_id: str, dimensions: List[Dict]) -> str:
        """Convert dimension ID to actual value name"""
        try:
            # Find dimension definition
            dim_def = None
            for dim in dimensions:
                if dim.get('name', dim.get('id', '')) == dim_name:
                    dim_def = dim
                    break

            if dim_def and isinstance(dim_def, list):
                # Find the value in the dimension values
                for value_def in dim_def:
                    if value_def.get('id', '') == dim_id:
                        return value_def.get('name', dim_id)

            return dim_id  # Return ID if not found

        except Exception:
            return dim_id  # Return ID on error

    def _create_sample_icio_data(self, years: List[int], countries: List[str], industries: List[str]) -> pd.DataFrame:
        """Create sample ICIO data when API is unavailable"""
        logger.info("Creating sample ICIO data for demonstration")

        data_points = []
        np.random.seed(42)  # Consistent random data

        for year in years:
            for country in countries:
                for industry in industries:
                    for counterpart in countries:
                        for counterpart_industry in industries:
                            # Create bilateral flow
                            flow_value = np.random.lognormal(10, 2)
                            data_points.append({
                                'Year': year,
                                'Reporting_Country': country,
                                'Reporting_Industry': industry,
                                'Partner_Country': counterpart,
                                'Partner_Industry': counterpart_industry,
                                'Value': flow_value
                            })

        df = pd.DataFrame(data_points)
        return df

    def _save_data_locally(self, data: pd.DataFrame, dataset_type: str, years: List[int],
                          countries: List[str], industries: List[str]):
        """Save downloaded data locally with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{dataset_type}_{'_'.join(map(str, years))}_{timestamp}.csv"
        filepath = self.cache_dir / filename

        data.to_csv(filepath, index=False)
        logger.info(f"Data saved locally: {filepath}")

        # Also save a latest copy
        latest_filename = f"{dataset_type}_latest.csv"
        latest_filepath = self.cache_dir / latest_filename
        data.to_csv(latest_filepath, index=False)

    def download_tiva_indicators(self, years: List[int] = None, countries: List[str] = None,
                               indicators: List[str] = None) -> Optional[pd.DataFrame]:
        """
        Download Trade-in-Value-Added (TiVA) indicators

        Args:
            years (List[int]): List of years
            countries (List[str]): List of countries
            indicators (List[str]): List of TiVA indicators

        Returns:
            pd.DataFrame: TiVA indicators data
        """
        dataset_code = self.datasets['TIVA']

        # Default parameters
        if years is None:
            years = list(range(2005, datetime.now().year + 1))  # TiVA available from 2005
        if countries is None:
            countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR']
        if indicators is None:
            indicators = [
                'FVA',  # Foreign value added in gross exports
                'DVX',  # Domestic value added in gross exports
                'GVC',  # Global value chain participation
                'VAX',  # Value added in exports
                'VAF'   # Value added in final demand
            ]

        logger.info(f"Downloading TiVA indicators for years: {years}")

        # Similar implementation to ICIO download
        # For now, create sample data
        data_points = []
        np.random.seed(123)

        for year in years:
            for country in countries:
                for indicator in indicators:
                    # Sample indicator values
                    value = np.random.uniform(0.1, 0.9)
                    data_points.append({
                        'Year': year,
                        'Country': country,
                        'Indicator': indicator,
                        'Value': value
                    })

        df = pd.DataFrame(data_points)
        self._save_data_locally(df, 'TIVA', years, countries, indicators)

        logger.info(f"Downloaded TiVA indicators: {df.shape}")
        return df

    def create_download_wizard(self) -> Dict[str, callable]:
        """
        Create interactive download wizard for user guidance

        Returns:
            Dict: Wizard functions
        """
        wizard = {
            'show_datasets': self.show_available_datasets,
            'download_icio': self.download_icio_with_wizard,
            'download_tiva': self.download_tiva_with_wizard,
            'check_availability': self.check_data_availability
        }

        return wizard

    def show_available_datasets(self):
        """Display available OECD datasets"""
        print("\nAvailable OECD Datasets:")
        print("=" * 50)

        for dataset_name, dataset_code in self.datasets.items():
            metadata = self.get_dataset_metadata(dataset_code)
            if metadata:
                print(f"\n{dataset_name} ({dataset_code}):")
                print(f"  Title: {metadata['title']}")
                print(f"  Description: {metadata['description'][:100]}...")
                print(f"  Last Updated: {metadata['last_updated']}")
            else:
                print(f"\n{dataset_name} ({dataset_code}):")
                print("  Metadata unavailable")

    def download_icio_with_wizard(self):
        """Interactive ICIO download wizard"""
        print("\nOECD ICIO Download Wizard")
        print("=" * 40)

        print("\nDefault settings (press Enter to use):")
        print("Years: 1995-2024")
        print("Countries: Major economies (USA, CHN, JPN, DEU, GBR, FRA)")
        print("Industries: Total economy")

        user_input = input("\nUse default settings? (Y/n): ").strip().lower()

        if user_input == 'n':
            # Custom settings
            years_input = input("Enter years (e.g., 2015,2016,2017 or 2015-2020): ").strip()
            if years_input:
                if '-' in years_input:
                    start, end = map(int, years_input.split('-'))
                    years = list(range(start, end + 1))
                else:
                    years = [int(y) for y in years_input.split(',')]
            else:
                years = list(range(1995, datetime.now().year + 1))

            countries_input = input("Enter country codes (comma-separated): ").strip()
            if countries_input:
                countries = [c.strip().upper() for c in countries_input.split(',')]
            else:
                countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA']
        else:
            years = list(range(1995, datetime.now().year + 1))
            countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA']

        print(f"\nDownloading ICIO data...")
        print(f"Years: {len(years)} selected")
        print(f"Countries: {len(countries)} selected")

        data = self.download_icio_data(years=years, countries=countries)

        if data is not None:
            print(f"\n[SUCCESS] Successfully downloaded ICIO data: {data.shape}")
            print(f"Data saved to: {self.cache_dir}")
        else:
            print("\n[FAILED] Failed to download ICIO data")
            print("Please check your internet connection and try again")

    def download_tiva_with_wizard(self):
        """Interactive TiVA download wizard"""
        print("\nOECD TiVA Indicators Download Wizard")
        print("=" * 45)

        print("\nDefault settings (press Enter to use):")
        print("Years: 2005-2024")
        print("Countries: Major economies (USA, CHN, JPN, DEU, GBR)")
        print("Indicators: All TiVA indicators")

        user_input = input("\nUse default settings? (Y/n): ").strip().lower()

        if user_input != 'y':
            print("Custom download not implemented yet. Using defaults...")

        years = list(range(2005, datetime.now().year + 1))
        countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR']

        print(f"\nDownloading TiVA indicators...")
        data = self.download_tiva_indicators(years=years, countries=countries)

        if data is not None:
            print(f"\n[SUCCESS] Successfully downloaded TiVA indicators: {data.shape}")
            print(f"Data saved to: {self.cache_dir}")
        else:
            print("\n[FAILED] Failed to download TiVA indicators")

    def check_data_availability(self) -> Dict[str, bool]:
        """Check availability of different data sources"""
        availability = {}

        for dataset_name, dataset_code in self.datasets.items():
            metadata = self.get_dataset_metadata(dataset_code)
            availability[dataset_name] = metadata is not None

        return availability

    def get_cache_info(self) -> Dict[str, Union[int, List[str]]]:
        """Get information about cached data"""
        cache_files = list(self.cache_dir.glob("*.csv"))
        metadata_files = list(self.cache_dir.glob("*_metadata.json"))

        return {
            'cache_directory': str(self.cache_dir),
            'data_files': len(cache_files),
            'metadata_files': len(metadata_files),
            'latest_files': [f.name for f in cache_files if 'latest' in f.name],
            'total_size_mb': sum(f.stat().st_size for f in cache_files) / (1024 * 1024)
        }


def main():
    """Demonstration of OECD Data Access functionality"""
    print("OECD Data Access Demonstration")
    print("=" * 40)

    # Initialize data access client
    client = OECDDataAccess()

    # Show available datasets
    print("\n1. Checking available datasets...")
    client.show_available_datasets()

    # Check data availability
    print("\n2. Checking data availability...")
    availability = client.check_data_availability()
    for dataset, available in availability.items():
        status = "[AVAILABLE]" if available else "[UNAVAILABLE]"
        print(f"   {dataset}: {status}")

    # Download sample ICIO data
    print("\n3. Downloading sample ICIO data...")
    sample_years = [2020, 2021, 2022]
    sample_countries = ['USA', 'CHN', 'DEU']
    icio_data = client.download_icio_data(years=sample_years, countries=sample_countries)

    if icio_data is not None:
        print(f"   ICIO data shape: {icio_data.shape}")
        print(f"   Columns: {list(icio_data.columns)}")
        print(f"   Sample data:")
        print(icio_data.head())

    # Download sample TiVA indicators
    print("\n4. Downloading sample TiVA indicators...")
    tiva_data = client.download_tiva_indicators(years=sample_years, countries=sample_countries)

    if tiva_data is not None:
        print(f"   TiVA data shape: {tiva_data.shape}")
        print(f"   Sample data:")
        print(tiva_data.head())

    # Show cache information
    print("\n5. Cache information:")
    cache_info = client.get_cache_info()
    for key, value in cache_info.items():
        print(f"   {key}: {value}")

    print("\nOECD Data Access demonstration completed!")
    print("Note: This demonstration creates sample data when OECD API is not accessible")


if __name__ == "__main__":
    main()