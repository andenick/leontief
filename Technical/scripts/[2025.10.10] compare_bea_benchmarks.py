#!/usr/bin/env python3
"""
Compare Leontief Results to BEA Published Benchmarks
Leontief Project - Validation Script

Compares our calculated multipliers and Leontief inverse
to BEA's published Industry-by-Industry Total Requirements.
"""

import os
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_bea_total_requirements(filepath: Path) -> pd.DataFrame:
    """
    Load BEA Industry-by-Industry Total Requirements table.

    Args:
        filepath: Path to IndbyIndTRDetail.txt

    Returns:
        DataFrame with Leontief inverse matrix
    """
    print(f"Loading BEA total requirements from: {filepath.name}")

    # Parse the file manually - space-delimited with fixed-width fields
    # Strategy: Work backwards from the end (similar to BEA Use table parser)
    import re
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        # Skip header
        header = next(f)

        for line_num, line in enumerate(f, start=2):
            # Split on whitespace
            parts = line.split()

            if len(parts) < 4:
                continue

            # Last field is year
            year = parts[-1]

            # Second to last is coefficient
            try:
                coeff = float(parts[-2])
            except (ValueError, IndexError):
                continue

            # Everything before coefficient is: Industry1 + desc1 + Industry2 + desc2
            # Strategy: Industry codes are alphanumeric patterns (e.g., 1111A0, 336111)
            # Find the first two tokens that look like industry codes

            industry_codes = []
            for part in parts[:-2]:  # Exclude coeff and year
                if re.match(r'^[0-9A-Z]+$', part) and len(part) >= 4:
                    industry_codes.append(part)
                    if len(industry_codes) == 2:
                        break

            if len(industry_codes) < 2:
                continue

            industry1 = industry_codes[0]
            industry2 = industry_codes[1]

            records.append({
                'Industry': industry1,
                'Industry2': industry2,
                'Coeff': coeff,
                'IOYear': year
            })

    df = pd.DataFrame(records)

    print(f"  Loaded {len(df):,} coefficients")
    print(f"  Unique industries (rows): {df['Industry'].nunique()}")
    print(f"  Unique industries (cols): {df['Industry2'].nunique()}")

    # Create matrix from long format
    # Industry = row (what produces)
    # Industry2 = column (what is required for)
    # Coeff = L matrix coefficient

    L_matrix = df.pivot_table(
        values='Coeff',
        index='Industry',
        columns='Industry2',
        aggfunc='first',  # Should only be one value per cell
        fill_value=0.0
    )

    # Sort indices
    L_matrix = L_matrix.sort_index(axis=0).sort_index(axis=1)

    print(f"  Matrix shape: {L_matrix.shape}")
    print(f"  Mean coefficient: {L_matrix.values.mean():.6f}")
    print(f"  Diagonal mean: {np.diag(L_matrix).mean():.6f}")

    return L_matrix


def calculate_bea_multipliers(L_matrix: pd.DataFrame) -> pd.Series:
    """
    Calculate output multipliers from Leontief inverse.

    Output multiplier = sum of column (total direct + indirect requirements)

    Args:
        L_matrix: Leontief inverse matrix

    Returns:
        Series of output multipliers by industry
    """
    print(f"\nCalculating BEA output multipliers...")

    # Output multiplier = column sum of L matrix
    multipliers = L_matrix.sum(axis=0)

    print(f"  Multipliers calculated: {len(multipliers)}")
    print(f"  Mean multiplier: {multipliers.mean():.4f}")
    print(f"  Min multiplier: {multipliers.min():.4f}")
    print(f"  Max multiplier: {multipliers.max():.4f}")

    return multipliers


def load_wassily_results(filepath: Path) -> dict:
    """Load Leontief analysis results."""
    print(f"\nLoading Leontief results from: {filepath.name}")

    with open(filepath, 'rb') as f:
        results = pickle.load(f)

    print(f"  Loaded results")

    # Handle both old and new result formats
    L_key = 'L_industry' if 'L_industry' in results else 'L_matrix'
    print(f"  L matrix shape: {results[L_key].shape}")
    print(f"  Industries: {len(results['output_multipliers'])}")

    return results


def compare_results(bea_mult, wassily_mult, bea_L, wassily_L):
    """
    Compare BEA and Leontief results.

    Args:
        bea_mult: BEA output multipliers
        wassily_mult: Leontief output multipliers
        bea_L: BEA Leontief inverse
        wassily_L: Wassily Leontief inverse
    """
    print("\n" + "="*80)
    print("COMPARISON: BEA vs Leontief")
    print("="*80)

    # Find common industries
    common_industries = set(bea_mult.index) & set(wassily_mult.index)
    print(f"\nCommon industries: {len(common_industries)}")
    print(f"  BEA industries: {len(bea_mult)}")
    print(f"  Leontief industries: {len(wassily_mult)}")

    if len(common_industries) == 0:
        print("\n[WARNING] No common industries found!")
        print("  This likely means we're comparing different sectors.")
        print("  BEA might have industry codes, Leontief might have commodity codes.")
        return

    # Align to common industries
    bea_common = bea_mult.loc[list(common_industries)].sort_index()
    wassily_common = wassily_mult.loc[list(common_industries)].sort_index()

    # Calculate differences
    diff = wassily_common - bea_common
    abs_diff = np.abs(diff)
    pct_diff = (diff / bea_common * 100)

    print(f"\nMultiplier Comparison:")
    print(f"  Mean absolute difference: {abs_diff.mean():.6f}")
    print(f"  Max absolute difference: {abs_diff.max():.6f}")
    print(f"  Mean % difference: {pct_diff.mean():.2f}%")
    print(f"  Max % difference: {pct_diff.max():.2f}%")

    # Correlation
    correlation = wassily_common.corr(bea_common)
    print(f"  Correlation: {correlation:.6f}")

    # Show top differences
    print(f"\nTop 10 Largest Absolute Differences:")
    top_diff = abs_diff.nlargest(10)
    for i, (ind, diff_val) in enumerate(top_diff.items(), 1):
        bea_val = bea_common[ind]
        wassily_val = wassily_common[ind]
        pct = (wassily_val - bea_val) / bea_val * 100
        print(f"  {i}. {ind}:")
        print(f"      BEA: {bea_val:.4f}, Leontief: {wassily_val:.4f}, Diff: {diff_val:.4f} ({pct:+.2f}%)")

    # Show top matches
    print(f"\nTop 10 Closest Matches:")
    closest = abs_diff.nsmallest(10)
    for i, (ind, diff_val) in enumerate(closest.items(), 1):
        bea_val = bea_common[ind]
        wassily_val = wassily_common[ind]
        print(f"  {i}. {ind}: BEA={bea_val:.4f}, Leontief={wassily_val:.4f}, Diff={diff_val:.6f}")

    # Create comparison DataFrame
    comparison_df = pd.DataFrame({
        'BEA_Multiplier': bea_common,
        'Leontief_Multiplier': wassily_common,
        'Absolute_Diff': abs_diff,
        'Percent_Diff': pct_diff
    })

    # Save comparison
    output_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/bea_wassily_comparison.xlsx")
    comparison_df.to_excel(output_path, sheet_name='Multiplier_Comparison')
    print(f"\n[OK] Comparison saved to: {output_path}")

    return comparison_df


def main():
    print("="*80)
    print("BEA Benchmark Validation")
    print("="*80)

    # Paths
    bea_file = (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/raw/bea/benchmarks/ixitr2002/IndbyIndTRDetail.txt")
    wassily_file = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/industry_by_industry_2002.pkl")

    # Load BEA data
    print("\n[1/3] Loading BEA Total Requirements...")
    bea_L = load_bea_total_requirements(bea_file)
    bea_mult = calculate_bea_multipliers(bea_L)

    # Load Leontief results
    print("\n[2/3] Loading Leontief Results...")
    wassily_results = load_wassily_results(wassily_file)
    wassily_mult = wassily_results['output_multipliers']
    L_key = 'L_industry' if 'L_industry' in wassily_results else 'L_matrix'
    wassily_L = wassily_results[L_key]

    # Compare
    print("\n[3/3] Comparing Results...")
    comparison = compare_results(bea_mult, wassily_mult, bea_L, wassily_L)

    print("\n" + "="*80)
    print("Validation Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
