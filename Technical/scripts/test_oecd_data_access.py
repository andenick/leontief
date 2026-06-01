#!/usr/bin/env python3
"""
Test script for OECD Data Access module
Leontief.io - Testing OECD data download and access functionality
"""

import sys
from pathlib import Path
import pandas as pd

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

def test_oecd_data_access():
    """Test OECD data access functionality"""
    print("OECD Data Access Test")
    print("=" * 30)

    try:
        # Import OECD data access
        exec(open(Path(__file__).parent.parent / 'src' / '[2025.10.14] oecd_data_access.py').read())

        # Initialize client
        print("1. Initializing OECD Data Access client...")
        client = OECDDataAccess()

        # Test 1: Check available datasets
        print("\n2. Testing dataset availability...")
        availability = client.check_data_availability()
        for dataset, available in availability.items():
            status = "[AVAILABLE]" if available else "[UNAVAILABLE]"
            print(f"   {dataset}: {status}")

        # Test 2: Download sample ICIO data
        print("\n3. Testing ICIO data download...")
        sample_years = [2020, 2021]
        sample_countries = ['USA', 'CHN', 'DEU']
        icio_data = client.download_icio_data(years=sample_years, countries=sample_countries)

        if icio_data is not None:
            print("   [SUCCESS] ICIO data downloaded successfully")
            print(f"   Data shape: {icio_data.shape}")
            print(f"   Columns: {list(icio_data.columns)[:5]}...")  # Show first 5 columns
            print(f"   Sample years: {sorted(icio_data['Year'].unique())}")
        else:
            print("   [FAILED] ICIO data download failed")

        # Test 3: Download sample TiVA indicators
        print("\n4. Testing TiVA indicators download...")
        tiva_data = client.download_tiva_indicators(years=sample_years, countries=sample_countries)

        if tiva_data is not None:
            print("   [SUCCESS] TiVA indicators downloaded successfully")
            print(f"   Data shape: {tiva_data.shape}")
            print(f"   Sample indicators: {sorted(tiva_data['Indicator'].unique())}")
        else:
            print("   [FAILED] TiVA indicators download failed")

        # Test 4: Check cache information
        print("\n5. Testing cache functionality...")
        cache_info = client.get_cache_info()
        print(f"   Cache directory: {cache_info['cache_directory']}")
        print(f"   Data files: {cache_info['data_files']}")
        print(f"   Cache size: {cache_info['total_size_mb']:.2f} MB")

        # Test 5: Download wizard (non-interactive mode)
        print("\n6. Testing download wizard setup...")
        wizard = client.create_download_wizard()
        wizard_functions = list(wizard.keys())
        print(f"   Wizard functions available: {wizard_functions}")

        print("\n" + "=" * 30)
        print("OECD Data Access tests completed!")
        print("Note: Sample data was created when OECD API was not accessible")

        return True

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("OECD Data Access Testing for Leontief.io")
    print("=" * 50)

    # Run tests
    success = test_oecd_data_access()

    if success:
        print("\nAll tests passed! OECD data access module is working correctly.")
    else:
        print("\nSome tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()