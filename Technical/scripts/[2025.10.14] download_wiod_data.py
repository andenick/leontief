#!/usr/bin/env python3
"""
WIOD Data Download Assistant
Leontief - WIOD 2016 Release Data Acquisition

This script assists with downloading and organizing WIOD 2016 data.
Due to registration requirements, it provides guidance and validation
for manual download process.

Author: Claude Code Assistant
Date: 2025-10-14
Version: 1.0
"""

import os
import sys
import requests
from pathlib import Path
import pandas as pd
import zipfile
import hashlib
from typing import List, Dict, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WIODDownloader:
    """
    WIOD Data Download Assistant

    Provides guidance and validation for downloading WIOD 2016 data
    """

    def __init__(self, base_path: str = None):
        """
        Initialize WIOD Downloader

        Args:
            base_path: Base path for WIOD data storage
        """
        if base_path is None:
            self.base_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/raw/wiod/2016_release")
        else:
            self.base_path = Path(base_path)

        # Create directories
        self._create_directories()

        # Expected files and their checksums (if available)
        self.expected_files = {
            'WIOT': [
                'WIOT2000_October16.xlsx',
                'WIOT2001_October16.xlsx',
                'WIOT2002_October16.xlsx',
                'WIOT2003_October16.xlsx',
                'WIOT2004_October16.xlsx',
                'WIOT2005_October16.xlsx',
                'WIOT2006_October16.xlsx',
                'WIOT2007_October16.xlsx',
                'WIOT2008_October16.xlsx',
                'WIOT2009_October16.xlsx',
                'WIOT2010_October16.xlsx',
                'WIOT2011_October16.xlsx',
                'WIOT2012_October16.xlsx',
                'WIOT2013_October16.xlsx',
                'WIOT2014_October16.xlsx'
            ],
            'NIOT': [
                'NIOT2000_WIOD.xlsx',
                'NIOT2001_WIOD.xlsx',
                'NIOT2002_WIOD.xlsx',
                'NIOT2003_WIOD.xlsx',
                'NIOT2004_WIOD.xlsx',
                'NIOT2005_WIOD.xlsx',
                'NIOT2006_WIOD.xlsx',
                'NIOT2007_WIOD.xlsx',
                'NIOT2008_WIOD.xlsx',
                'NIOT2009_WIOD.xlsx',
                'NIOT2010_WIOD.xlsx',
                'NIOT2011_WIOD.xlsx',
                'NIOT2012_WIOD.xlsx',
                'NIOT2013_WIOD.xlsx',
                'NIOT2014_WIOD.xlsx'
            ],
            'Social_Accounts': [
                'SEA_WIOD_October16.xlsx'
            ]
        }

    def _create_directories(self):
        """Create necessary directory structure"""
        subdirs = ['WIOT', 'NIOT', 'Social_Accounts', 'Environmental', 'Metadata']
        for subdir in subdirs:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    def print_download_instructions(self):
        """Print detailed download instructions"""
        print("=" * 80)
        print("WIOD 2016 DATA DOWNLOAD INSTRUCTIONS")
        print("=" * 80)
        print()
        print("IMPORTANT: WIOD data requires manual download due to registration requirements")
        print()
        print("STEP 1: Access WIOD Website")
        print("  URL: https://www.wiod.org/")
        print("  Navigate to: Database → WIOD 2016 Release")
        print()
        print("STEP 2: Register for Access")
        print("  - Click on 'Register' or 'Request Access'")
        print("  - Fill out the registration form (free academic access)")
        print("  - Wait for email confirmation")
        print()
        print("STEP 3: Download Data Package")
        print("  - Look for 'Complete WIOD 2016 Release' or similar")
        print("  - Download the main data package (usually a ZIP file)")
        print("  - Save to: <DATA_ROOT>/Technical/data/raw/wiod/downloads/")
        print()
        print("STEP 4: Extract and Organize")
        print("  - Extract ZIP file to temporary location")
        print("  - Run this script again to organize files automatically")
        print()
        print("STEP 5: Validate Download")
        print("  - Run validation function to check file completeness")
        print()
        print("Alternative Sources:")
        print("  - Academic repositories (if available)")
        print("  - Research gate or other academic sharing platforms")
        print("  - Contact WIOD team directly for access")
        print()
        print("=" * 80)

    def create_download_directory(self):
        """Create downloads directory for manual file placement"""
        download_dir = self.base_path.parent / 'downloads'
        download_dir.mkdir(parents=True, exist_ok=True)

        print(f"Created download directory: {download_dir}")
        print("Please download WIOD ZIP file to this directory")
        print(f"Expected file name: wiods16.zip or similar")

        return download_dir

    def organize_downloaded_files(self, source_dir: str = None) -> bool:
        """
        Organize downloaded files into proper directory structure

        Args:
            source_dir: Directory containing extracted WIOD files

        Returns:
            True if successful, False otherwise
        """
        try:
            if source_dir is None:
                source_dir = self.base_path.parent / 'downloads'
            else:
                source_dir = Path(source_dir)

            if not source_dir.exists():
                logger.error(f"Source directory does not exist: {source_dir}")
                return False

            print(f"Organizing files from: {source_dir}")
            print(f"Target directory: {self.base_path}")
            print()

            # Look for WIOD files in source directory
            source_files = list(source_dir.glob("**/*.xlsx"))

            if not source_files:
                print("No Excel files found in source directory")
                print("Please extract WIOD ZIP file and try again")
                return False

            organized_count = 0

            for file_path in source_files:
                file_name = file_path.name

                # Determine target directory based on file name
                if file_name.startswith('WIOT'):
                    target_dir = self.base_path / 'WIOT'
                elif file_name.startswith('NIOT'):
                    target_dir = self.base_path / 'NIOT'
                elif file_name.startswith('SEA'):
                    target_dir = self.base_path / 'Social_Accounts'
                else:
                    # Skip unrecognized files
                    continue

                # Copy file to target directory
                target_path = target_dir / file_name
                if not target_path.exists():
                    import shutil
                    shutil.copy2(file_path, target_path)
                    organized_count += 1
                    print(f"  Organized: {file_name} → {target_dir.name}/")
                else:
                    print(f"  Skipped (exists): {file_name}")

            print()
            print(f"Organized {organized_count} files")
            return True

        except Exception as e:
            logger.error(f"Error organizing files: {e}")
            return False

    def validate_download(self) -> Dict:
        """
        Validate downloaded files for completeness

        Returns:
            Validation report dictionary
        """
        try:
            print("Validating WIOD download...")
            print("=" * 50)

            validation_report = {
                'total_expected': 0,
                'total_found': 0,
                'missing_files': [],
                'extra_files': [],
                'categories': {}
            }

            total_expected = 0
            total_found = 0

            for category, expected_files in self.expected_files.items():
                category_path = self.base_path / category
                found_files = []

                if category_path.exists():
                    found_files = [f.name for f in category_path.glob("*.xlsx")]

                missing = [f for f in expected_files if f not in found_files]
                extra = [f for f in found_files if f not in expected_files]

                validation_report['categories'][category] = {
                    'expected': len(expected_files),
                    'found': len(found_files),
                    'missing': missing,
                    'extra': extra,
                    'completeness': len(found_files) / len(expected_files) if expected_files else 1.0
                }

                total_expected += len(expected_files)
                total_found += len(found_files)

                # Print category results
                print(f"{category}:")
                print(f"  Expected: {len(expected_files)} files")
                print(f"  Found: {len(found_files)} files")
                print(f"  Completeness: {len(found_files)/len(expected_files)*100:.1f}%")

                if missing:
                    print(f"  Missing: {len(missing)} files")
                    for file in missing[:3]:  # Show first 3 missing files
                        print(f"    - {file}")
                    if len(missing) > 3:
                        print(f"    ... and {len(missing)-3} more")

                if extra:
                    print(f"  Extra: {len(extra)} files")
                    for file in extra[:3]:  # Show first 3 extra files
                        print(f"    - {file}")
                    if len(extra) > 3:
                        print(f"    ... and {len(extra)-3} more")
                print()

            validation_report['total_expected'] = total_expected
            validation_report['total_found'] = total_found
            validation_report['overall_completeness'] = total_found / total_expected if total_expected > 0 else 1.0

            # Overall summary
            print("=" * 50)
            print(f"OVERALL VALIDATION RESULTS:")
            print(f"  Total Expected Files: {total_expected}")
            print(f"  Total Found Files: {total_found}")
            print(f"  Overall Completeness: {validation_report['overall_completeness']*100:.1f}%")
            print()

            if validation_report['overall_completeness'] >= 1.0:
                print("✅ DOWNLOAD COMPLETE - All expected files found")
            elif validation_report['overall_completeness'] >= 0.8:
                print("⚠️  DOWNLOAD MOSTLY COMPLETE - Some files missing")
            else:
                print("❌ DOWNLOAD INCOMPLETE - Many files missing")

            return validation_report

        except Exception as e:
            logger.error(f"Error validating download: {e}")
            return {}

    def test_file_accessibility(self) -> bool:
        """
        Test if downloaded files are accessible and readable

        Returns:
            True if files are accessible, False otherwise
        """
        try:
            print("Testing file accessibility...")
            print("=" * 40)

            # Test a sample of files from each category
            sample_files = []

            for category in ['WIOT', 'NIOT', 'Social_Accounts']:
                category_path = self.base_path / category
                if category_path.exists():
                    files = list(category_path.glob("*.xlsx"))
                    if files:
                        sample_files.append(files[0])  # Test first file in each category

            accessible_count = 0
            total_count = len(sample_files)

            for file_path in sample_files:
                try:
                    # Try to read file metadata
                    df = pd.read_excel(file_path, nrows=1)
                    file_size = file_path.stat().st_size

                    print(f"✅ {file_path.name}: {file_size/1024/1024:.1f} MB, {df.shape[1]} columns")
                    accessible_count += 1

                except Exception as e:
                    print(f"❌ {file_path.name}: Error - {e}")

            print("=" * 40)
            print(f"File Accessibility: {accessible_count}/{total_count} files readable")

            return accessible_count == total_count

        except Exception as e:
            logger.error(f"Error testing file accessibility: {e}")
            return False

    def create_metadata_files(self):
        """Create metadata files for WIOD data"""
        try:
            print("Creating metadata files...")

            # Country codes
            countries = [
                ('AUT', 'Austria'),
                ('BEL', 'Belgium'),
                ('BGR', 'Bulgaria'),
                ('CYP', 'Cyprus'),
                ('CZE', 'Czech Republic'),
                ('DEU', 'Germany'),
                ('DNK', 'Denmark'),
                ('ESP', 'Spain'),
                ('EST', 'Estonia'),
                ('FIN', 'Finland'),
                ('FRA', 'France'),
                ('GBR', 'United Kingdom'),
                ('GRC', 'Greece'),
                ('HRV', 'Croatia'),
                ('HUN', 'Hungary'),
                ('IRL', 'Ireland'),
                ('ITA', 'Italy'),
                ('LTU', 'Lithuania'),
                ('LUX', 'Luxembourg'),
                ('LVA', 'Latvia'),
                ('MLT', 'Malta'),
                ('NLD', 'Netherlands'),
                ('POL', 'Poland'),
                ('PRT', 'Portugal'),
                ('ROU', 'Romania'),
                ('SVK', 'Slovakia'),
                ('SVN', 'Slovenia'),
                ('SWE', 'Sweden'),
                ('USA', 'United States'),
                ('CAN', 'Canada'),
                ('MEX', 'Mexico'),
                ('JPN', 'Japan'),
                ('KOR', 'Korea, Republic of'),
                ('AUS', 'Australia'),
                ('CHN', 'China'),
                ('IND', 'India'),
                ('IDN', 'Indonesia'),
                ('TWN', 'Taiwan'),
                ('TUR', 'Turkey'),
                ('RUS', 'Russia'),
                ('BRA', 'Brazil'),
                ('ZAF', 'South Africa')
            ]

            country_df = pd.DataFrame(countries, columns=['Code', 'Name'])
            country_file = self.base_path / 'Metadata' / 'country_codes.csv'
            country_df.to_csv(country_file, index=False)

            # Years covered
            years_df = pd.DataFrame({'Year': list(range(2000, 2015))})
            years_file = self.base_path / 'Metadata' / 'years_covered.csv'
            years_df.to_csv(years_file, index=False)

            print("✅ Metadata files created")
            return True

        except Exception as e:
            logger.error(f"Error creating metadata files: {e}")
            return False

    def run_complete_setup(self) -> bool:
        """
        Run complete download setup and validation process

        Returns:
            True if setup successful, False otherwise
        """
        try:
            print("WIOD DATA SETUP WIZARD")
            print("=" * 50)
            print()

            # Step 1: Check if files already exist
            validation_report = self.validate_download()

            if validation_report.get('overall_completeness', 0) >= 1.0:
                print("✅ WIOD data already complete!")

                # Test accessibility
                if self.test_file_accessibility():
                    print("✅ All files are accessible")

                    # Create metadata
                    self.create_metadata_files()

                    print("\n🎉 WIOD setup complete! Ready for processing.")
                    return True
                else:
                    print("⚠️  Files exist but some are not accessible")
                    return False

            # Step 2: Provide download instructions if needed
            print("\n📥 WIOD data download required")
            self.print_download_instructions()

            # Step 3: Create download directory
            download_dir = self.create_download_directory()

            # Step 4: Ask user to confirm download
            response = input("\nHave you downloaded the WIOD data package? (y/n): ")

            if response.lower() == 'y':
                # Step 5: Organize files
                print("\nOrganizing downloaded files...")
                if self.organize_downloaded_files():
                    # Step 6: Validate again
                    validation_report = self.validate_download()

                    if validation_report.get('overall_completeness', 0) >= 0.8:
                        # Step 7: Test accessibility
                        if self.test_file_accessibility():
                            # Step 8: Create metadata
                            self.create_metadata_files()

                            print("\n🎉 WIOD setup complete!")
                            return True

                print("\n❌ Setup incomplete. Please check files and try again.")
                return False
            else:
                print("\nPlease download WIOD data and run this script again.")
                return False

        except Exception as e:
            logger.error(f"Error in complete setup: {e}")
            return False

def main():
    """Main function"""
    downloader = WIODDownloader()

    try:
        success = downloader.run_complete_setup()

        if success:
            print("\n✅ Setup completed successfully!")
            print("You can now run the WIOD processor to integrate the data.")
        else:
            print("\n❌ Setup incomplete. Please follow the instructions and try again.")

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")

if __name__ == "__main__":
    main()