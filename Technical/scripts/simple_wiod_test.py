#!/usr/bin/env python3
"""
Simple WIOD processor test
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Import with date prefix
exec(open(Path(__file__).parent.parent / 'src' / '[2025.10.14] wiod_processor.py').read())

# Test the processor
try:
    processor = WIODProcessor()
    print("✅ WIOD processor initialized successfully")
    print(f"Countries: {len(processor.countries)}")
    print(f"Sectors: {len(processor.sectors)}")
    print(f"Years: {len(processor.years)}")
    print(f"Years range: {min(processor.years)}-{max(processor.years)}")
    print("✅ WIOD processor test completed successfully!")
except Exception as e:
    print(f"❌ Error: {e}")