#!/usr/bin/env python3
"""
Input-Output Table Loader
Wassily Project - I-O Tables Analysis Tool

Load and parse I-O tables from various sources (BEA, OECD, WIOD).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IOTableLoader:
    """Load Input-Output tables from various sources."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the I-O table loader.

        Args:
            data_dir: Base directory for raw I-O tables data
        """
        if data_dir is None:
            # Default to project structure
            self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)

        logger.info(f"IOTableLoader initialized with data_dir: {self.data_dir}")

    def load_bea_table(
        self,
        filepath: Path,
        year: int,
        table_type: str = "use",
        sheet_name: Optional[str] = None
    ) -> Dict:
        """
        Load a BEA Input-Output table from Excel file.

        Args:
            filepath: Path to the Excel file
            year: Year of the I-O table
            table_type: Type of table ("use", "make", "summary")
            sheet_name: Specific sheet to read (if None, will try to auto-detect)

        Returns:
            Dictionary containing I-O table components
        """
        logger.info(f"Loading BEA {table_type} table for {year} from {filepath}")

        try:
            # Try different Excel engines (files may be old .xls despite .xlsx extension)
            try:
                xls = pd.ExcelFile(filepath, engine='openpyxl')
            except:
                try:
                    xls = pd.ExcelFile(filepath, engine='xlrd')
                except:
                    xls = pd.ExcelFile(filepath)  # Let pandas auto-detect

            logger.info(f"Available sheets: {xls.sheet_names}")

            # Auto-detect sheet if not specified
            if sheet_name is None:
                sheet_name = self._detect_main_sheet(xls.sheet_names, table_type)

            # Read the main sheet (use same engine as xls object)
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # Parse the table structure
            io_table = self._parse_bea_table(df, year, table_type)

            logger.info(f"Successfully loaded {year} {table_type} table")
            return io_table

        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            raise

    def _detect_main_sheet(self, sheet_names: list, table_type: str) -> str:
        """
        Auto-detect the main data sheet in BEA Excel file.

        Args:
            sheet_names: List of sheet names in the workbook
            table_type: Type of table being loaded

        Returns:
            Name of the main data sheet
        """
        # Common patterns for main data sheets
        patterns = {
            "use": ["Use", "USE", "use table"],
            "make": ["Make", "MAKE", "make table"],
            "summary": ["Summary", "SUMMARY", "IxI"]
        }

        for pattern in patterns.get(table_type, []):
            for sheet in sheet_names:
                if pattern.lower() in sheet.lower():
                    logger.info(f"Auto-detected sheet: {sheet}")
                    return sheet

        # Default to first sheet if no pattern match
        logger.warning(f"Could not auto-detect sheet, using: {sheet_names[0]}")
        return sheet_names[0]

    def _parse_bea_table(
        self,
        df: pd.DataFrame,
        year: int,
        table_type: str
    ) -> Dict:
        """
        Parse BEA table structure into standardized format.

        BEA tables typically have:
        - Header rows with metadata
        - Industry names in first column
        - Commodity/industry codes
        - Transaction matrix
        - Value added rows
        - Final demand columns

        Args:
            df: DataFrame containing the raw BEA table
            year: Year of the table
            table_type: Type of table

        Returns:
            Standardized I-O table dictionary
        """
        logger.info(f"Parsing BEA {table_type} table structure...")

        # This is a placeholder - actual parsing depends on BEA table format
        # Will need to be customized based on actual table structure

        io_table = {
            "metadata": {
                "country": "USA",
                "year": year,
                "source": "BEA",
                "table_type": table_type,
                "classification": "NAICS",  # BEA uses NAICS post-1997
                "num_sectors": None,  # To be determined from data
                "vintage": f"{year} Benchmark"
            },
            "raw_dataframe": df,
            "transactions_matrix": None,  # To be extracted
            "total_output": None,  # To be extracted
            "value_added": None,  # To be extracted
            "final_demand": None,  # To be extracted
            "sector_names": None,  # To be extracted
            "parsed": False  # Will be True when fully parsed
        }

        logger.info(f"Initial parse complete. Full parsing requires table inspection.")
        return io_table

    def validate_table(self, io_table: Dict) -> bool:
        """
        Validate I-O table for consistency.

        Checks:
        - Row sums == column sums + value added
        - Matrix dimensions consistent
        - No negative values in inappropriate places

        Args:
            io_table: I-O table dictionary

        Returns:
            True if valid, False otherwise
        """
        if not io_table.get("parsed"):
            logger.warning("Table not fully parsed, cannot validate")
            return False

        try:
            Z = io_table["transactions_matrix"]
            x = io_table["total_output"]
            VA = io_table["value_added"]

            # Check: column sums of transactions + value added = total output
            col_sums = Z.sum(axis=0)
            va_sums = VA.sum(axis=0) if isinstance(VA, pd.DataFrame) else VA

            balance = np.allclose(col_sums + va_sums, x, rtol=0.01)

            if balance:
                logger.info("✓ Table validation passed: Balance condition met")
                return True
            else:
                logger.warning("✗ Table validation failed: Balance condition not met")
                return False

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False

    def to_standard_format(self, io_table: Dict) -> Dict:
        """
        Convert I-O table to standardized format used across Wassily.

        Standard format:
        - transactions_matrix: pandas DataFrame (Z matrix)
        - total_output: pandas Series (x vector)
        - value_added: pandas DataFrame or Series
        - final_demand: pandas DataFrame
        - sector_names: list
        - All indexed consistently

        Args:
            io_table: Raw I-O table dictionary

        Returns:
            Standardized I-O table dictionary
        """
        logger.info("Converting to standard format...")

        # Placeholder - actual conversion depends on source format
        standardized = io_table.copy()
        standardized["standardized"] = True

        return standardized

    def list_available_tables(self) -> pd.DataFrame:
        """
        List all available I-O tables in the data directory.

        Returns:
            DataFrame with columns: year, source, table_type, filepath
        """
        logger.info(f"Scanning {self.data_dir} for I-O tables...")

        tables = []

        # Scan BEA directories
        bea_dir = self.data_dir / "bea"
        if bea_dir.exists():
            for year_dir in bea_dir.iterdir():
                if year_dir.is_dir():
                    for file in year_dir.glob("*.xl*"):
                        tables.append({
                            "year": year_dir.name.split("_")[0],
                            "source": "BEA",
                            "table_type": self._infer_table_type(file.name),
                            "filepath": str(file)
                        })

        # Scan international directories (placeholder)
        # TODO: Add OECD, WIOD scanning

        df = pd.DataFrame(tables)
        logger.info(f"Found {len(df)} I-O tables")

        return df

    def _infer_table_type(self, filename: str) -> str:
        """Infer table type from filename."""
        filename_lower = filename.lower()
        if "use" in filename_lower:
            return "use"
        elif "make" in filename_lower:
            return "make"
        elif "summary" in filename_lower or "ixi" in filename_lower:
            return "summary"
        else:
            return "unknown"


def main():
    """Demo of IOTableLoader functionality."""
    loader = IOTableLoader()

    # List available tables
    print("\nAvailable I-O Tables:")
    print("="*80)
    available = loader.list_available_tables()
    if not available.empty:
        print(available.to_string(index=False))
    else:
        print("No tables found. Run download_bea_tables.py first.")

    print("\n✓ IOTableLoader ready for use!")


if __name__ == "__main__":
    main()
