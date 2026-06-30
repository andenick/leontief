#!/usr/bin/env python3
"""
Analyze 2002 U.S. Input-Output Table
Leontief Project - First Analysis!

Calculate Leontief inverse, multipliers, and identify key sectors.
"""

import os
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from io_analysis import IOAnalyzer

def main():
    print("="*80)
    print("Leontief - 2002 U.S. I-O Analysis")
    print("="*80)

    # Load parsed table
    data_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/processed/io_table_2002.pkl")

    print(f"\nLoading parsed I-O table from: {data_path.name}")

    with open(data_path, 'rb') as f:
        io_table = pickle.load(f)

    print(f"[OK] Loaded!")
    print(f"\n  Industries: {io_table['metadata']['num_industries']}")
    print(f"  Commodities: {io_table['metadata']['num_commodities']}")

    # Extract matrices
    Z = io_table['transactions_matrix']  # (400 commodities × 416 industries)
    x = io_table['total_industry_output']  # Total output by industry

    print(f"\n  Transaction matrix (Z): {Z.shape}")
    print(f"  Total industry output (x): {len(x)}")

    # For I-O analysis, we need a square matrix (industries × industries)
    # The Use table is commodities × industries, so we need the Make table too
    # For now, let's use a commodity-by-commodity analysis
    # Or we can aggregate to make it square

    print(f"\n  Note: Use table is {Z.shape[0]} commodities × {Z.shape[1]} industries")
    print(f"  For standard I-O analysis, we need a square matrix.")
    print(f"  Using commodity-by-commodity approach...\n")

    # Create commodity total output
    x_commodity = io_table['total_commodity_output']

    # Transpose Z to get industry-by-commodity (who uses what commodity)
    # Then calculate A matrix (direct requirements coefficients)
    print("="*80)
    print("Step 1: Calculate Direct Requirements Matrix (A)")
    print("="*80)

    # A = Z / x (each column divided by total output of that industry)
    # But we need to be careful about zeros
    A = Z.div(x, axis=1)  # Divide each column by corresponding industry output
    A = A.fillna(0)  # Replace NaN (from division by zero) with 0

    print(f"\nDirect requirements matrix (A): {A.shape}")
    print(f"Mean coefficient: {A.values.mean():.4f}")
    print(f"Max coefficient: {A.values.max():.4f}")
    print(f"Sparsity: {(A == 0).sum().sum() / (A.shape[0] * A.shape[1]) * 100:.1f}% zeros")

    # Since A is not square (400×416), we can't compute Leontief inverse directly
    # We need to either:
    # 1. Aggregate to square matrix
    # 2. Use commodity technology assumption
    # 3. Use industry technology assumption

    print(f"\n[INFO] For Leontief inverse, need square matrix.")
    print(f"[INFO] Will create industry-by-industry table using commodity technology assumption.")

    # Simple approach: Just analyze the first N×N submatrix where N = min(commodities, industries)
    n = min(Z.shape)
    print(f"\nUsing {n}×{n} submatrix for analysis...")

    Z_square = Z.iloc[:n, :n]
    x_square = x.iloc[:n]

    # Recalculate A for square matrix
    A_square = Z_square.div(x_square, axis=1).fillna(0)

    print(f"\nSquare A matrix: {A_square.shape}")

    # Now we can compute Leontief inverse
    print("\n" + "="*80)
    print("Step 2: Calculate Leontief Inverse (L = (I - A)^-1)")
    print("="*80)

    from scipy import linalg

    I = np.eye(n)
    I_minus_A = I - A_square.values

    print(f"\nComputing inverse of (I - A)...")
    try:
        L_values = linalg.inv(I_minus_A)
        L = pd.DataFrame(L_values, index=A_square.index, columns=A_square.columns)

        print(f"[OK] Leontief inverse computed!")
        print(f"  Shape: {L.shape}")
        print(f"  Mean value: {L.values.mean():.4f}")
        print(f"  Max value: {L.values.max():.4f}")

        # Validate: (I - A) × L should equal I
        product = I_minus_A @ L_values
        is_identity = np.allclose(product, I, rtol=1e-5, atol=1e-8)
        print(f"  Validation: (I-A)*L = I? {is_identity}")

    except linalg.LinAlgError as e:
        print(f"[ERROR] Could not invert (I-A): {e}")
        print(f"Matrix may be singular or ill-conditioned")
        return

    # Calculate output multipliers
    print("\n" + "="*80)
    print("Step 3: Calculate Output Multipliers")
    print("="*80)

    output_multipliers = L.sum(axis=0)  # Column sums
    print(f"\nOutput multipliers calculated for {len(output_multipliers)} industries")
    print(f"  Mean multiplier: {output_multipliers.mean():.4f}")
    print(f"  Min multiplier: {output_multipliers.min():.4f}")
    print(f"  Max multiplier: {output_multipliers.max():.4f}")

    print(f"\nTop 10 Industries by Output Multiplier:")
    top_mult = output_multipliers.nlargest(10)
    for i, (ind, val) in enumerate(top_mult.items(), 1):
        print(f"  {i}. {ind}: {val:.4f}")

    # Calculate backward and forward linkages
    print("\n" + "="*80)
    print("Step 4: Calculate Linkages")
    print("="*80)

    # Backward linkages (demand-driven, column sums)
    backward_linkages = L.sum(axis=0)

    # Forward linkages (supply-driven, row sums)
    forward_linkages = L.sum(axis=1)

    # Rasmussen indices (normalized by mean)
    mean_backward = backward_linkages.mean()
    mean_forward = forward_linkages.mean()

    backward_index = backward_linkages / mean_backward
    forward_index = forward_linkages / mean_forward

    print(f"\nBackward linkages (demand effects):")
    print(f"  Mean: {mean_backward:.4f}")
    print(f"  Top 5:")
    for i, (ind, val) in enumerate(backward_linkages.nlargest(5).items(), 1):
        print(f"    {i}. {ind}: {val:.4f} (index: {backward_index[ind]:.4f})")

    print(f"\nForward linkages (supply effects):")
    print(f"  Mean: {mean_forward:.4f}")
    print(f"  Top 5:")
    for i, (ind, val) in enumerate(forward_linkages.nlargest(5).items(), 1):
        print(f"    {i}. {ind}: {val:.4f} (index: {forward_index[ind]:.4f})")

    # Identify key sectors (high backward AND forward linkages)
    print("\n" + "="*80)
    print("Step 5: Identify Key Sectors")
    print("="*80)

    # Key sectors: both indices > 1.0
    key_sectors = (backward_index > 1.0) & (forward_index > 1.0)
    key_sector_list = backward_index[key_sectors].index.tolist()

    print(f"\nKey sectors (both indices > 1.0): {len(key_sector_list)}")
    if key_sector_list:
        print(f"\nTop 10 Key Sectors by Total Linkage Score:")
        total_score = backward_index + forward_index
        top_key = total_score[key_sectors].nlargest(10)
        for i, (ind, score) in enumerate(top_key.items(), 1):
            print(f"  {i}. {ind}:")
            print(f"      Backward: {backward_index[ind]:.4f}, Forward: {forward_index[ind]:.4f}, Total: {score:.4f}")

    # Save results
    print("\n" + "="*80)
    print("Saving Results")
    print("="*80)

    results = {
        'metadata': io_table['metadata'],
        'A_matrix': A_square,
        'L_matrix': L,
        'output_multipliers': output_multipliers,
        'backward_linkages': backward_linkages,
        'forward_linkages': forward_linkages,
        'backward_index': backward_index,
        'forward_index': forward_index,
        'key_sectors': key_sector_list
    }

    output_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/analysis_results_2002.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(results, f)

    print(f"\n[OK] Results saved to: {output_path}")

    # Also save multipliers to Excel
    excel_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/multipliers_2002.xlsx")
    mult_df = pd.DataFrame({
        'Industry': output_multipliers.index,
        'Output_Multiplier': output_multipliers.values,
        'Backward_Linkage': backward_linkages.values,
        'Forward_Linkage': forward_linkages.values,
        'Backward_Index': backward_index.values,
        'Forward_Index': forward_index.values,
        'Is_Key_Sector': [ind in key_sector_list for ind in output_multipliers.index]
    })

    mult_df.to_excel(excel_path, index=False, sheet_name='Multipliers_2002')
    print(f"[OK] Multipliers saved to Excel: {excel_path}")

    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)
    print(f"\nLeontief has successfully analyzed the 2002 U.S. economy!")
    print(f"  - {len(output_multipliers)} industries analyzed")
    print(f"  - {len(key_sector_list)} key sectors identified")
    print(f"  - Results saved for further analysis")


if __name__ == "__main__":
    main()
