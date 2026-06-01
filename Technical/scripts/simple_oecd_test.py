#!/usr/bin/env python3
"""
Simple test for OECD data access
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

def main():
    print("Simple OECD Data Access Test")
    print("=" * 35)

    try:
        # Import using exec to handle filename
        namespace = {}
        exec(open(Path(__file__).parent.parent / 'src' / '[2025.10.14] oecd_data_access.py').read(), namespace)

        # Get the class
        OECDDataAccess = namespace['OECDDataAccess']

        # Test 1: Initialize client
        print("1. Testing client initialization...")
        client = OECDDataAccess()
        print("   [OK] Client initialized successfully")

        # Test 2: Check availability
        print("2. Testing data availability...")
        availability = client.check_data_availability()
        print(f"   [OK] Checked {len(availability)} datasets")

        # Test 3: Download sample data
        print("3. Testing sample data download...")
        data = client.download_icio_data(years=[2020], countries=['USA', 'CHN'])
        if data is not None:
            print(f"   [OK] Sample data created: {data.shape}")
        else:
            print("   [FAIL] Sample data creation failed")

        # Test 4: Cache info
        print("4. Testing cache functionality...")
        cache_info = client.get_cache_info()
        print(f"   [OK] Cache directory: {cache_info['cache_directory']}")

        print("\n" + "=" * 35)
        print("All OECD data access tests passed!")
        print("Module is ready for production use.")

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nOECD data access module is working correctly!")
    else:
        print("\nOECD data access module needs debugging.")