#!/usr/bin/env python3
"""
BEA HTML Table Parser
Wassily Project - I-O Tables Analysis Tool

Parse BEA Input-Output tables from HTML format.
BEA historical tables are HTML despite .xlsx extension.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BEAHTMLParser:
    """Parse BEA I-O tables from HTML format."""

    def __init__(self):
        """Initialize parser."""
        logger.info("BEAHTMLParser initialized")

    def parse_html_table(
        self,
        filepath: Path,
        year: int,
        table_type: str = "use"
    ) -> Dict:
        """
        Parse BEA I-O table from HTML file.

        BEA tables structure:
        - Multiple HTML tables in one file
        - Main data table is usually the largest
        - Has row headers (industries) and column headers (commodities/industries)
        - Contains transactions matrix, totals, and value added

        Args:
            filepath: Path to HTML file (.xlsx extension but HTML content)
            year: Year of the table
            table_type: Type ("use", "make", "summary")

        Returns:
            Dictionary with parsed I-O table components
        """
        logger.info(f"Parsing BEA HTML table: {filepath.name}")

        try:
            # Read all tables from HTML
            tables = pd.read_html(filepath, encoding='utf-8')
            logger.info(f"Found {len(tables)} tables in HTML file")

            # Find the main data table (usually the largest)
            main_table = self._find_main_table(tables)

            if main_table is None:
                raise ValueError("Could not identify main data table")

            logger.info(f"Main table shape: {main_table.shape}")
            logger.info(f"Columns: {len(main_table.columns)}")
            logger.info(f"Rows: {len(main_table)}")

            # Parse the table structure
            parsed = self._parse_table_structure(main_table, year, table_type)

            return parsed

        except Exception as e:
            logger.error(f"Error parsing HTML table: {e}")
            raise

    def _find_main_table(self, tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Find the main data table from list of tables.

        The main table is typically:
        - Largest by number of cells
        - Has both row and column headers
        - Contains numeric data

        Args:
            tables: List of DataFrames from read_html

        Returns:
            Main data table or None
        """
        if not tables:
            return None

        # Find largest table by number of cells
        largest = max(tables, key=lambda t: t.shape[0] * t.shape[1])

        logger.info(f"Selected table with shape {largest.shape}")
        return largest

    def _parse_table_structure(
        self,
        df: pd.DataFrame,
        year: int,
        table_type: str
    ) -> Dict:
        """
        Parse the structure of BEA I-O table.

        BEA Use table typically has:
        - First column: Industry names
        - Subsequent columns: Commodities
        - Bottom rows: Value added components
        - Last rows: Total output/commodity output

        Args:
            df: DataFrame with raw table
            year: Year
            table_type: Table type

        Returns:
            Parsed I-O table dictionary
        """
        logger.info("Analyzing table structure...")

        # Basic structure identification
        # (Will need to be customized based on actual BEA format)

        io_table = {
            "metadata": {
                "country": "USA",
                "year": year,
                "source": "BEA",
                "table_type": table_type,
                "classification": "NAICS",
                "num_sectors": None,
                "vintage": f"{year} Benchmark",
                "format": "HTML"
            },
            "raw_dataframe": df,
            "transactions_matrix": None,
            "total_output": None,
            "value_added": None,
            "final_demand": None,
            "sector_names": None,
            "parsed": False
        }

        # Try to identify key components
        # This requires inspecting actual BEA table format
        logger.info("Table structure identified. Manual parsing needed for full extraction.")

        return io_table

    def extract_transactions_matrix(
        self,
        df: pd.DataFrame,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int
    ) -> pd.DataFrame:
        """
        Extract transactions matrix (Z) from specific location in table.

        Args:
            df: Raw DataFrame
            start_row, end_row: Row range for Z matrix
            start_col, end_col: Column range for Z matrix

        Returns:
            Transactions matrix Z
        """
        Z = df.iloc[start_row:end_row, start_col:end_col]

        # Convert to numeric
        Z = Z.apply(pd.to_numeric, errors='coerce').fillna(0)

        logger.info(f"Extracted transactions matrix: {Z.shape}")
        return Z

    def identify_table_sections(self, df: pd.DataFrame) -> Dict:
        """
        Identify different sections of BEA I-O table.

        Looks for keywords to find:
        - Transactions matrix area
        - Value added section
        - Final demand columns
        - Total output row/column

        Args:
            df: Raw DataFrame

        Returns:
            Dictionary with section locations (row/col indices)
        """
        logger.info("Identifying table sections...")

        sections = {
            "transactions_start_row": None,
            "transactions_end_row": None,
            "value_added_start_row": None,
            "final_demand_start_col": None,
            "total_output_row": None,
            "total_output_col": None
        }

        # Search for common keywords
        keywords = {
            "value_added": ["Value added", "Compensation", "Taxes"],
            "final_demand": ["Personal consumption", "Gross private", "Government"],
            "total": ["Total", "Gross output", "Commodity output"]
        }

        # Look through first column for row headers
        first_col = df.iloc[:, 0].astype(str)

        for idx, value in first_col.items():
            value_lower = value.lower()

            # Check for value added
            if any(kw.lower() in value_lower for kw in keywords["value_added"]):
                if sections["value_added_start_row"] is None:
                    sections["value_added_start_row"] = idx
                    logger.info(f"Found value added at row {idx}")

            # Check for total
            if any(kw.lower() in value_lower for kw in keywords["total"]):
                sections["total_output_row"] = idx
                logger.info(f"Found total row at {idx}")

        # Look through first row for column headers
        first_row = df.iloc[0, :].astype(str)

        for idx, value in first_row.items():
            value_lower = value.lower()

            # Check for final demand
            if any(kw.lower() in value_lower for kw in keywords["final_demand"]):
                if sections["final_demand_start_col"] is None:
                    sections["final_demand_start_col"] = idx
                    logger.info(f"Found final demand at column {idx}")

        return sections


def main():
    """Test BEA HTML parser."""
    print("="*80)
    print("BEA HTML Table Parser")
    print("="*80)

    parser = BEAHTMLParser()

    # Try parsing 2002 Use table
    filepath = Path("D:/Arcanum/Projects/Wassily/Technical/data/raw/bea/2002_benchmark/Use_SUT_Framework_2002.xlsx")

    if filepath.exists():
        print(f"\nParsing: {filepath.name}")

        try:
            result = parser.parse_html_table(filepath, year=2002, table_type="use")

            print("\n[OK] Parsed successfully!")
            print(f"Table shape: {result['raw_dataframe'].shape}")
            print(f"\nFirst few rows and columns:")
            print(result['raw_dataframe'].iloc[:5, :3].to_string())

            # Try to identify sections
            sections = parser.identify_table_sections(result['raw_dataframe'])
            print("\n[INFO] Table sections identified:")
            for key, value in sections.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n[ERROR] File not found: {filepath}")


if __name__ == "__main__":
    main()
