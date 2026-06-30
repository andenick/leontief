#!/usr/bin/env python3
"""
Input-Output Analysis Engine
Leontief Project - I-O Tables Analysis Tool

Core I-O analysis functions:
- Leontief inverse calculation
- Output, income, and employment multipliers
- Forward and backward linkages
- Key sector identification
"""

import pandas as pd
import numpy as np
from scipy import linalg
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IOAnalyzer:
    """Perform Input-Output analysis calculations."""

    def __init__(self, io_table: Dict):
        """
        Initialize I-O analyzer with a standardized I-O table.

        Args:
            io_table: Dictionary containing I-O table components:
                - transactions_matrix (Z): pandas DataFrame
                - total_output (x): pandas Series
                - value_added (VA): pandas Series or DataFrame
                - final_demand (F): pandas Series or DataFrame
                - sector_names: list
        """
        self.io_table = io_table
        self.Z = io_table.get("transactions_matrix")
        self.x = io_table.get("total_output")
        self.VA = io_table.get("value_added")
        self.F = io_table.get("final_demand")
        self.sectors = io_table.get("sector_names", [])

        # Calculated matrices (computed on demand)
        self.A = None  # Direct requirements matrix
        self.L = None  # Leontief inverse (total requirements matrix)

        logger.info(f"IOAnalyzer initialized for {io_table.get('metadata', {}).get('year', 'unknown year')}")

    def calculate_direct_requirements_matrix(self) -> pd.DataFrame:
        """
        Calculate direct requirements matrix (A).

        A_ij = Z_ij / x_j

        Each element represents the direct input from sector i required
        to produce one unit of output in sector j.

        Returns:
            pd.DataFrame: Direct requirements matrix A
        """
        logger.info("Calculating direct requirements matrix (A)...")

        if self.Z is None or self.x is None:
            raise ValueError("Transactions matrix (Z) and total output (x) required")

        # Calculate A = Z / x (broadcasting division by output)
        # Avoid division by zero
        x_safe = self.x.replace(0, np.nan)
        self.A = self.Z.div(x_safe, axis=1).fillna(0)

        # Validate: all elements should be between 0 and 1
        if (self.A < 0).any().any():
            logger.warning("Negative values found in direct requirements matrix")

        if (self.A > 1).any().any():
            logger.warning("Values > 1 found in direct requirements matrix")

        logger.info(f"Direct requirements matrix calculated: {self.A.shape}")
        return self.A

    def calculate_leontief_inverse(self, validate: bool = True) -> pd.DataFrame:
        """
        Calculate Leontief inverse matrix (L).

        L = (I - A)^{-1}

        Each element L_ij represents the total (direct + indirect) output
        from sector i required to produce one unit of final demand in sector j.

        Args:
            validate: If True, validate that (I - A) * L = I

        Returns:
            pd.DataFrame: Leontief inverse matrix L
        """
        logger.info("Calculating Leontief inverse matrix (L)...")

        # Calculate A if not already done
        if self.A is None:
            self.calculate_direct_requirements_matrix()

        # Create identity matrix
        n = self.A.shape[0]
        I = np.eye(n)

        # Calculate (I - A)
        I_minus_A = I - self.A.values

        # Check if (I - A) is invertible
        det = np.linalg.det(I_minus_A)
        if np.abs(det) < 1e-10:
            logger.error(f"(I - A) is singular or near-singular (det = {det})")
            raise ValueError("Cannot invert (I - A) matrix")

        # Calculate Leontief inverse: L = (I - A)^{-1}
        L_values = linalg.inv(I_minus_A)

        # Convert to DataFrame with same index/columns as A
        self.L = pd.DataFrame(L_values, index=self.A.index, columns=self.A.columns)

        # Validation
        if validate:
            # Check that (I - A) * L = I
            product = I_minus_A @ L_values
            is_identity = np.allclose(product, I, rtol=1e-5, atol=1e-8)

            if is_identity:
                logger.info("✓ Leontief inverse validated: (I - A) × L = I")
            else:
                max_error = np.max(np.abs(product - I))
                logger.warning(f"✗ Leontief inverse validation warning: max error = {max_error}")

        logger.info(f"Leontief inverse calculated: {self.L.shape}")
        return self.L

    def calculate_output_multipliers(self) -> pd.Series:
        """
        Calculate output multipliers.

        Output multiplier for sector j = sum of column j in Leontief inverse.

        Interpretation: Total output from all sectors required to produce
        one unit of final demand in sector j.

        Returns:
            pd.Series: Output multipliers indexed by sector
        """
        logger.info("Calculating output multipliers...")

        if self.L is None:
            self.calculate_leontief_inverse()

        # Column sums of Leontief inverse
        output_multipliers = self.L.sum(axis=0)
        output_multipliers.name = "Output Multiplier"

        logger.info(f"Output multipliers calculated: mean = {output_multipliers.mean():.3f}")
        return output_multipliers

    def calculate_income_multipliers(
        self,
        value_added_coefficients: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Calculate income (or value-added) multipliers.

        Income multiplier = v × L

        where v is the vector of value-added coefficients (VA / x).

        Args:
            value_added_coefficients: If provided, use these coefficients.
                Otherwise calculate from VA and x.

        Returns:
            pd.Series: Income multipliers indexed by sector
        """
        logger.info("Calculating income multipliers...")

        if self.L is None:
            self.calculate_leontief_inverse()

        # Calculate value-added coefficients if not provided
        if value_added_coefficients is None:
            if self.VA is None or self.x is None:
                raise ValueError("Value added (VA) and total output (x) required")

            # Handle VA as DataFrame (multiple components) or Series
            if isinstance(self.VA, pd.DataFrame):
                # Sum across value-added components
                va_total = self.VA.sum(axis=0)
            else:
                va_total = self.VA

            # Calculate coefficients: v = VA / x
            x_safe = self.x.replace(0, np.nan)
            v = (va_total / x_safe).fillna(0)
        else:
            v = value_added_coefficients

        # Calculate income multipliers: v × L
        income_multipliers = v.values @ self.L.values
        income_multipliers = pd.Series(income_multipliers, index=self.L.columns)
        income_multipliers.name = "Income Multiplier"

        logger.info(f"Income multipliers calculated: mean = {income_multipliers.mean():.3f}")
        return income_multipliers

    def calculate_linkages(self) -> pd.DataFrame:
        """
        Calculate forward and backward linkages.

        Backward linkage (demand-side): column sum of L
        Forward linkage (supply-side): row sum of L

        Rasmussen indices normalize by the mean.

        Returns:
            pd.DataFrame: Linkages with columns:
                - backward_linkage
                - forward_linkage
                - backward_index (Rasmussen)
                - forward_index (Rasmussen)
        """
        logger.info("Calculating forward and backward linkages...")

        if self.L is None:
            self.calculate_leontief_inverse()

        n = self.L.shape[0]

        # Backward linkages (column sums)
        backward = self.L.sum(axis=0)

        # Forward linkages (row sums)
        forward = self.L.sum(axis=1)

        # Rasmussen indices (normalized by mean)
        mean_backward = backward.mean()
        mean_forward = forward.mean()

        backward_index = backward / mean_backward
        forward_index = forward / mean_forward

        # Combine into DataFrame
        linkages = pd.DataFrame({
            "backward_linkage": backward,
            "forward_linkage": forward,
            "backward_index": backward_index,
            "forward_index": forward_index
        })

        logger.info("Linkages calculated")
        return linkages

    def identify_key_sectors(
        self,
        backward_threshold: float = 1.0,
        forward_threshold: float = 1.0
    ) -> pd.DataFrame:
        """
        Identify key sectors using linkage indices.

        Key sectors have both:
        - Backward index > threshold (strong demand-side effects)
        - Forward index > threshold (strong supply-side effects)

        Args:
            backward_threshold: Threshold for backward index (default 1.0)
            forward_threshold: Threshold for forward index (default 1.0)

        Returns:
            pd.DataFrame: Key sectors with their linkage indices
        """
        logger.info("Identifying key sectors...")

        linkages = self.calculate_linkages()

        # Identify key sectors
        is_key = (
            (linkages["backward_index"] > backward_threshold) &
            (linkages["forward_index"] > forward_threshold)
        )

        key_sectors = linkages[is_key].copy()
        key_sectors = key_sectors.sort_values("backward_index", ascending=False)

        logger.info(f"Identified {len(key_sectors)} key sectors")
        return key_sectors

    def hypothetical_extraction(self, sector_index: int) -> Dict:
        """
        Perform hypothetical extraction of a sector.

        Calculates the impact of removing a sector from the economy
        by setting its row and column in the Leontief inverse to zero.

        Args:
            sector_index: Index of sector to extract

        Returns:
            Dictionary with:
                - output_loss: Total output loss across all sectors
                - output_loss_pct: Percentage loss of total output
                - sector_impacts: Output loss by sector
        """
        logger.info(f"Performing hypothetical extraction for sector {sector_index}...")

        if self.L is None:
            self.calculate_leontief_inverse()

        # Original total output
        original_output = self.x.sum()

        # Create modified Leontief inverse with sector extracted
        L_modified = self.L.copy()
        L_modified.iloc[sector_index, :] = 0
        L_modified.iloc[:, sector_index] = 0

        # Calculate new output with modified L
        # Simplified: assume same final demand structure
        if isinstance(self.F, pd.DataFrame):
            final_demand = self.F.sum(axis=1)
        else:
            final_demand = self.F

        new_output = L_modified.values @ final_demand.values
        new_output = pd.Series(new_output, index=self.L.index)

        # Calculate impacts
        output_loss = self.x - new_output
        total_loss = output_loss.sum()
        loss_pct = (total_loss / original_output) * 100

        result = {
            "sector_extracted": self.sectors[sector_index] if self.sectors else sector_index,
            "output_loss": total_loss,
            "output_loss_pct": loss_pct,
            "sector_impacts": output_loss
        }

        logger.info(f"Extraction complete: {loss_pct:.2f}% output loss")
        return result


def main():
    """Demo of IOAnalyzer (requires loaded I-O table)."""
    print("IOAnalyzer - Input-Output Analysis Engine")
    print("="*80)
    print("\nThis module provides core I-O analysis functions:")
    print("- Leontief inverse calculation")
    print("- Output multipliers")
    print("- Income multipliers")
    print("- Forward and backward linkages")
    print("- Key sector identification")
    print("- Hypothetical extraction")
    print("\n✓ IOAnalyzer ready for use!")


if __name__ == "__main__":
    main()
