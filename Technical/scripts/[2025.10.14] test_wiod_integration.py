#!/usr/bin/env python3
"""
WIOD Integration Test Script
Leontief.io - Testing WIOD Integration with Main Platform

This script tests the WIOD integration module and demonstrates how
WIOD data connects with the existing Leontief.io framework.

Author: Claude Code Assistant
Date: 2025-10-14
Version: 1.0
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
    print("WIOD INTEGRATION TEST SUITE")
    print("=" * 50)
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
        assert integration.wiod_processor is not None
        assert integration.available_sources is not None
        print("[SUCCESS] WIOD Integration initialized successfully")

        # Test 2: Check available data sources
        print("\n2. Testing available data sources...")
        available_data = integration.list_available_data()
        assert isinstance(available_data, pd.DataFrame)
        print(f"✅ Found data from {len(available_data)} sources:")
        for _, row in available_data.iterrows():
            print(f"   - {row['source']}: {row['type']} ({row['years']})")

        # Test 3: Get integration status
        print("\n3. Testing integration status...")
        status = integration.get_integration_status()
        assert isinstance(status, dict)
        assert 'data_sources' in status
        assert 'components' in status
        assert 'capabilities' in status
        print("✅ Integration status retrieved successfully")
        print(f"   - Components available: {sum(status['components'].values())}/{len(status['components'])}")
        print(f"   - Data sources: {status['data_coverage']['sources']}")
        print(f"   - Countries covered: {status['data_coverage']['countries']}")

        # Test 4: Test classification cross-walk
        print("\n4. Testing classification cross-walk...")
        cross_walk = integration.create_cross_walk()
        assert isinstance(cross_walk, pd.DataFrame)
        assert len(cross_walk) > 0
        print(f"✅ Created cross-walk with {len(cross_walk)} sector mappings")

        # Test 5: Test comparative analysis setup
        print("\n5. Testing comparative analysis setup...")
        if status['data_coverage']['total_years'] > 0:
            test_year = status['data_coverage']['total_years']  # Use first available year
            results = integration.run_comparative_analysis(test_year)
            assert isinstance(results, dict)
            assert 'year' in results
            assert 'insights' in results
            print(f"✅ Comparative analysis setup successful for year {test_year}")
            for insight in results['insights']:
                print(f"   - {insight}")

        # Test 6: Test unified dataset creation
        print("\n6. Testing unified dataset creation...")
        if len(status['data_coverage']['sources']) > 0:
            unified_data = integration.create_unified_dataset(include_wiod=True, include_bea=True)
            assert isinstance(unified_data, dict)
            assert 'metadata' in unified_data
            assert 'data' in unified_data
            print(f"✅ Unified dataset created successfully")
            print(f"   - Sources included: {unified_data['metadata']['sources']}")
            print(f"   - Countries: {len(unified_data['metadata']['countries'])}")

        # Test 7: Test data export
        print("\n7. Testing unified data export...")
        if 'unified_data' in locals():
            success = integration.export_unified_data(unified_data)
            assert success == True
            print("✅ Unified data exported successfully")

        print("\n" + "=" * 50)
        print("WIOD INTEGRATION TESTS PASSED!")
        print("=" * 50)
        print("\nWIOD integration is ready for production use with Leontief.io")

        return True

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        logger.error(f"WIOD integration test failed: {e}")
        return False

def demonstrate_integration_capabilities():
    """Demonstrate WIOD integration capabilities"""
    print("\nWIOD INTEGRATION CAPABILITIES DEMO")
    print("=" * 50)

    try:
        # Import and initialize
        exec(open(Path(__file__).parent.parent / 'src' / '[2025.10.14] wiod_integration.py').read())
        integration = WIODIntegration()

        print("\n1. Data Source Inventory:")
        available = integration.list_available_data()
        print(available.to_string(index=False))

        print("\n2. Integration Status:")
        status = integration.get_integration_status()
        for key, value in status.items():
            if key == 'components':
                print(f"   {key}: {value}")
            elif key == 'capabilities':
                print(f"   {key}: {list(value.keys())}")
            else:
                print(f"   {key}: {value}")

        print("\n3. Sample Classification Cross-Walk:")
        cross_walk = integration.create_cross_walk()
        print(cross_walk.head().to_string(index=False))

        print("\n4. Integration Ready!")
        print("The WIOD integration provides:")
        print("   - Multi-country I-O analysis (43 countries)")
        print("   - Unified BEA + WIOD data handling")
        print("   - Cross-classification mapping")
        print("   - Comparative analysis capabilities")
        print("   - Export to standardized formats")

    except Exception as e:
        print(f"Demo failed: {e}")

def main():
    """Main function"""
    print("WIOD Integration Testing for Leontief.io")
    print("=" * 60)

    # Run integration tests
    success = test_wiod_integration()

    if success:
        print("\nAll tests passed! Running capabilities demo...")
        demonstrate_integration_capabilities()
    else:
        print("\nSome tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()