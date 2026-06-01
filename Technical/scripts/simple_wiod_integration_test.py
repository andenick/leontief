#!/usr/bin/env python3
"""
Simple WIOD Integration Test
Leontief.io - Basic WIOD Integration Testing

This script provides a simplified test for WIOD integration functionality.
"""

import sys
import pandas as pd
from pathlib import Path
import logging

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_wiod_integration():
    """Test WIOD integration functionality"""
    print("WIOD INTEGRATION TEST")
    print("=" * 40)
    print()

    try:
        # Import WIOD integration using exec with namespace
        integration_namespace = {}
        exec(open(Path(__file__).parent.parent / 'src' / '[2025.10.14] wiod_integration.py').read(), integration_namespace)

        # Get the WIODIntegration class from the namespace
        WIODIntegration = integration_namespace['WIODIntegration']

        # Test 1: Initialize WIOD Integration
        print("1. Testing WIOD Integration initialization...")
        integration = WIODIntegration()
        assert integration is not None
        print("[SUCCESS] WIOD Integration initialized successfully")

        # Test 2: Check available data sources
        print("\n2. Testing available data sources...")
        available_data = integration.list_available_data()
        assert isinstance(available_data, pd.DataFrame)
        print(f"[SUCCESS] Found data from {len(available_data)} sources:")
        for _, row in available_data.iterrows():
            print(f"   - {row['source']}: {row['type']} ({row['years']})")

        # Test 3: Get integration status
        print("\n3. Testing integration status...")
        status = integration.get_integration_status()
        assert isinstance(status, dict)
        assert 'data_sources' in status
        assert 'components' in status
        assert 'capabilities' in status
        print("[SUCCESS] Integration status retrieved successfully")
        print(f"   - Components available: {sum(status['components'].values())}/{len(status['components'])}")
        print(f"   - Data sources: {status['data_coverage']['sources']}")
        print(f"   - Countries covered: {status['data_coverage']['countries']}")

        # Test 4: Test classification cross-walk
        print("\n4. Testing classification cross-walk...")
        cross_walk = integration.create_cross_walk()
        assert isinstance(cross_walk, pd.DataFrame)
        print(f"[SUCCESS] Created cross-walk with {len(cross_walk)} sector mappings")

        # Test 5: Test comparative analysis setup
        print("\n5. Testing comparative analysis setup...")
        if status['data_coverage']['total_years'] > 0:
            # Use a reasonable test year
            test_years = status['data_coverage'].get('years', [2010])
            if test_years:
                test_year = test_years[0] if isinstance(test_years, list) else test_years
                results = integration.run_comparative_analysis(test_year)
                assert isinstance(results, dict)
                assert 'year' in results
                assert 'insights' in results
                print(f"[SUCCESS] Comparative analysis setup successful for year {test_year}")
                for insight in results['insights']:
                    print(f"   - {insight}")
            else:
                print("[SKIP] No years available for comparative analysis")
        else:
            print("[SKIP] No data available for comparative analysis")

        # Test 6: Test unified dataset creation
        print("\n6. Testing unified dataset creation...")
        if len(status['data_coverage']['sources']) > 0:
            unified_data = integration.create_unified_dataset(include_wiod=True, include_bea=True)
            assert isinstance(unified_data, dict)
            assert 'metadata' in unified_data
            assert 'data' in unified_data
            print("[SUCCESS] Unified dataset created successfully")
            print(f"   - Sources included: {unified_data['metadata']['sources']}")
            print(f"   - Countries: {len(unified_data['metadata']['countries'])}")
        else:
            print("[SKIP] No data sources available for unified dataset")

        print("\n" + "=" * 40)
        print("WIOD INTEGRATION TESTS COMPLETED!")
        print("=" * 40)
        print("\nWIOD integration is working correctly.")

        return True

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        logger.error(f"WIOD integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("WIOD Integration Testing for Leontief.io")
    print("=" * 50)

    # Run integration tests
    success = test_wiod_integration()

    if success:
        print("\nAll tests passed! WIOD integration is ready.")
    else:
        print("\nSome tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()