#!/usr/bin/env python3
"""
Method 2: Load BEA Total Requirements Directly
Leontief Project - Methodological Comparison

This script loads BEA's pre-calculated Total Requirements matrix
(Leontief inverse) directly without any transformation.

Methodology: Use BEA's published results as-is
"""

import os
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import re

def load_bea_total_requirements(filepath: Path) -> tuple:
    """
    Load BEA Total Requirements matrix directly.

    This IS the Leontief inverse as calculated by BEA.

    Returns:
        L_matrix: Leontief inverse (427x427)
        multipliers: Output multipliers (column sums)
    """
    print("="*80)
    print("METHOD 2: Loading BEA Total Requirements Directly")
    print("="*80)

    print(f"\nLoading from: {filepath.name}")

    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f)  # Skip header

        for line_num, line in enumerate(f, start=2):
            parts = line.split()

            if len(parts) < 4:
                continue

            # Find industry codes
            codes = [p for p in parts if re.match(r'^[0-9A-Z]+$', p) and len(p) >= 4]

            if len(codes) < 2:
                continue

            row_ind = codes[0]
            col_ind = codes[1]

            try:
                coeff = float(parts[-2])
                year = parts[-1]

                if year == '2002':
                    records.append({
                        'Row': row_ind,
                        'Col': col_ind,
                        'Coeff': coeff
                    })
            except (ValueError, IndexError):
                continue

    df = pd.DataFrame(records)

    print(f"  Loaded {len(df):,} coefficients")
    print(f"  Unique row industries: {df['Row'].nunique()}")
    print(f"  Unique column industries: {df['Col'].nunique()}")

    # Create matrix
    L_matrix = df.pivot_table(
        values='Coeff',
        index='Row',
        columns='Col',
        aggfunc='first',
        fill_value=0.0
    )

    # Sort indices
    L_matrix = L_matrix.sort_index(axis=0).sort_index(axis=1)

    print(f"\n[OK] BEA Leontief Inverse Matrix:")
    print(f"  Shape: {L_matrix.shape}")
    print(f"  Mean coefficient: {L_matrix.values.mean():.6f}")
    print(f"  Diagonal mean: {np.diag(L_matrix).mean():.6f}")

    # Calculate multipliers (column sums)
    multipliers = L_matrix.sum(axis=0)

    print(f"\n[OK] Output Multipliers:")
    print(f"  Count: {len(multipliers)}")
    print(f"  Mean: {multipliers.mean():.4f}")
    print(f"  Range: {multipliers.min():.4f} to {multipliers.max():.4f}")

    print(f"\nTop 10 Multipliers:")
    top_mult = multipliers.nlargest(10)
    for i, (ind, val) in enumerate(top_mult.items(), 1):
        print(f"  {i}. {ind}: {val:.4f}")

    return L_matrix, multipliers


def main():
    print("="*80)
    print("Method 2: BEA Total Requirements (Direct Load)")
    print("="*80)

    # Path to BEA Total Requirements
    bea_file = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/raw/bea/benchmarks/ixitr2002/[2009.03.05] IndbyIndTRDetail.txt")

    # Load BEA data
    L_bea, mult_bea = load_bea_total_requirements(bea_file)

    # Save results
    print("\n" + "="*80)
    print("Saving Method 2 Results")
    print("="*80)

    results = {
        'metadata': {
            'method': 'BEA_direct',
            'description': 'BEA published Total Requirements loaded directly',
            'num_industries': L_bea.shape[0],
            'year': 2002,
            'source': 'BEA Total Requirements after Redefinitions'
        },
        'L_matrix': L_bea,
        'output_multipliers': mult_bea,
        'industries': list(L_bea.index)
    }

    output_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/method2_bea_direct_2002.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(results, f)

    print(f"\n[OK] Results saved to: {output_path}")

    # Save multipliers to Excel (one sheet)
    excel_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/[2025.10.10] method2_bea_multipliers.xlsx")
    mult_df = pd.DataFrame({
        'Industry': mult_bea.index,
        'Output_Multiplier': mult_bea.values
    })
    mult_df.to_excel(excel_path, index=False, sheet_name='BEA_Multipliers_2002')
    print(f"[OK] Multipliers saved to: {excel_path}")

    print("\n" + "="*80)
    print("Method 2 Complete!")
    print("="*80)
    print(f"\nBEA's official values loaded successfully:")
    print(f"  427 industries (includes 11 redefinition codes)")
    print(f"  Mean multiplier: {mult_bea.mean():.4f}")
    print(f"  These are BEA's published benchmarks")


if __name__ == "__main__":
    main()
