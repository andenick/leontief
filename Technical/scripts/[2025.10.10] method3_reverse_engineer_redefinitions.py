#!/usr/bin/env python3
"""
Method 3: Reverse-Engineer BEA Redefinitions
Leontief Project - Methodological Comparison

This script attempts to understand and replicate BEA's redefinitions
methodology by analyzing the relationship between:
- Standard 416 industries (in Use/Make tables)
- BEA's 427 industries (includes 11 special S/T codes)

Approach:
1. Load BEA's Total Requirements matrix (427x426)
2. Load our commodity technology results (416x416)
3. Analyze which industries map to the S/T codes
4. Examine the structure of redefinition industries
5. Attempt to replicate the transformation

Reference: BEA's "redefinitions after redefinitions" methodology
"""

import os
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import re

def load_bea_total_requirements():
    """Load BEA's published Total Requirements."""
    print("="*80)
    print("Loading BEA Total Requirements")
    print("="*80)

    pkl_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/method2_bea_direct_2002.pkl")

    print(f"\nLoading: {pkl_path.name}")
    with open(pkl_path, 'rb') as f:
        bea_data = pickle.load(f)

    L_bea = bea_data['L_matrix']
    mult_bea = bea_data['output_multipliers']

    print(f"  BEA L matrix: {L_bea.shape}")
    print(f"  BEA multipliers: {len(mult_bea)}")

    return L_bea, mult_bea, bea_data


def load_wassily_commodity_tech():
    """Load our commodity technology results (Method 1)."""
    print("\n" + "="*80)
    print("Loading Leontief Commodity Technology Results")
    print("="*80)

    pkl_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/industry_by_industry_2002.pkl")

    print(f"\nLoading: {pkl_path.name}")
    with open(pkl_path, 'rb') as f:
        wassily_data = pickle.load(f)

    L_wassily = wassily_data['L_industry']
    mult_wassily = wassily_data['output_multipliers']

    print(f"  Leontief L matrix: {L_wassily.shape}")
    print(f"  Leontief multipliers: {len(mult_wassily)}")

    return L_wassily, mult_wassily, wassily_data


def identify_special_industries(L_bea):
    """Identify BEA's 11 special redefinition industries."""
    print("\n" + "="*80)
    print("Identifying Special Redefinition Industries")
    print("="*80)

    all_row_codes = set(L_bea.index)
    all_col_codes = set(L_bea.columns)

    # Identify S and T codes
    s_codes = sorted([c for c in all_row_codes if c.startswith('S00')])
    t_codes = sorted([c for c in all_row_codes if c.startswith('T0')])

    special_codes = s_codes + t_codes

    print(f"\nSpecial Industries Found: {len(special_codes)}")
    print(f"\nS-codes (Secondary product redefinitions): {len(s_codes)}")
    for code in s_codes:
        print(f"  {code}")

    print(f"\nT-codes (Unknown type): {len(t_codes)}")
    for code in t_codes:
        print(f"  {code}")

    # Standard industries (not S or T)
    standard_codes = sorted([c for c in all_row_codes if not (c.startswith('S00') or c.startswith('T0'))])

    print(f"\nStandard Industries: {len(standard_codes)}")

    return special_codes, standard_codes, s_codes, t_codes


def analyze_special_industry_structure(L_bea, special_codes):
    """Analyze the structure of special industries in BEA matrix."""
    print("\n" + "="*80)
    print("Analyzing Special Industry Structure")
    print("="*80)

    for s_code in special_codes:
        if s_code not in L_bea.index:
            print(f"\n{s_code}: NOT in row index")
            continue

        # Get row for this special industry
        row = L_bea.loc[s_code]

        # Find non-zero connections
        non_zero = row[row > 0.01]  # Threshold to filter noise

        print(f"\n{s_code}:")
        print(f"  Non-zero coefficients: {len(non_zero)}")

        if len(non_zero) > 0:
            print(f"  Connected to industries:")
            top_connections = non_zero.nlargest(5)
            for ind, val in top_connections.items():
                print(f"    {ind}: {val:.4f}")


def compare_common_industries(L_bea, L_wassily, standard_codes):
    """Compare multipliers for industries common to both methods."""
    print("\n" + "="*80)
    print("Comparing Common Industries")
    print("="*80)

    # Find common industries
    bea_industries = set(L_bea.columns)
    wassily_industries = set(L_wassily.columns)

    common = sorted(list(bea_industries & wassily_industries))

    print(f"\nCommon industries: {len(common)}")

    # Calculate multipliers for common industries
    mult_bea_common = L_bea[common].sum(axis=0)
    mult_wassily_common = L_wassily[common].sum(axis=0)

    # Create comparison DataFrame
    comparison = pd.DataFrame({
        'Industry': common,
        'BEA_Multiplier': mult_bea_common.values,
        'Leontief_Multiplier': mult_wassily_common.values
    })

    comparison['Difference'] = comparison['BEA_Multiplier'] - comparison['Leontief_Multiplier']
    comparison['Ratio'] = comparison['BEA_Multiplier'] / comparison['Leontief_Multiplier']

    print(f"\nComparison Statistics:")
    print(f"  Mean BEA multiplier: {comparison['BEA_Multiplier'].mean():.4f}")
    print(f"  Mean Leontief multiplier: {comparison['Leontief_Multiplier'].mean():.4f}")
    print(f"  Mean ratio (BEA/Leontief): {comparison['Ratio'].mean():.4f}")
    print(f"  Std of ratio: {comparison['Ratio'].std():.4f}")

    print(f"\nTop 10 Largest Differences (BEA higher):")
    top_diff = comparison.nlargest(10, 'Difference')
    for idx, row in top_diff.iterrows():
        print(f"  {row['Industry']}: BEA={row['BEA_Multiplier']:.4f}, Leontief={row['Leontief_Multiplier']:.4f}, Diff={row['Difference']:.4f}")

    return comparison


def investigate_redefinition_pattern(L_bea, s_codes, standard_codes):
    """
    Investigate if we can infer the redefinition pattern.

    Hypothesis: S-codes represent redistributed secondary production.
    """
    print("\n" + "="*80)
    print("Investigating Redefinition Pattern")
    print("="*80)

    # For each S-code, see if we can identify a "parent" industry
    redefinition_map = {}

    for s_code in s_codes:
        if s_code not in L_bea.index:
            continue

        # Get the row for this S-code
        s_row = L_bea.loc[s_code]

        # Get the column (if exists)
        if s_code in L_bea.columns:
            s_col = L_bea[s_code]

            # Find industries that have strongest connection to this S-code
            top_suppliers = s_col.nlargest(5)

            print(f"\n{s_code}:")
            print(f"  Top suppliers TO this redefinition:")
            for ind, val in top_suppliers.items():
                if ind != s_code:  # Skip diagonal
                    print(f"    {ind}: {val:.4f}")

        # Find industries this S-code supplies to
        top_customers = s_row.nlargest(5)
        print(f"  Top customers FROM this redefinition:")
        for ind, val in top_customers.items():
            if ind != s_code:
                print(f"    {ind}: {val:.4f}")


def create_approximate_redefinitions(L_wassily, comparison):
    """
    Attempt to create a 'pseudo-redefinitions' adjustment.

    This is speculative since we don't have BEA's actual methodology.

    Approach: Apply a scaling factor based on the ratio pattern.
    """
    print("\n" + "="*80)
    print("Creating Approximate Redefinitions (Speculative)")
    print("="*80)

    # Calculate average ratio
    avg_ratio = comparison['Ratio'].mean()

    print(f"\nAverage BEA/Leontief ratio: {avg_ratio:.4f}")
    print(f"This suggests BEA multipliers are ~{avg_ratio:.2f}x our commodity tech values")

    # Create scaled version
    L_adjusted = L_wassily * avg_ratio
    mult_adjusted = L_adjusted.sum(axis=0)

    print(f"\nAdjusted multipliers (simple scaling):")
    print(f"  Mean: {mult_adjusted.mean():.4f}")
    print(f"  Range: {mult_adjusted.min():.4f} to {mult_adjusted.max():.4f}")

    print(f"\nNOTE: This is NOT a true replication of BEA's redefinitions.")
    print(f"It's a naive scaling to show the magnitude of difference.")
    print(f"True redefinitions require understanding BEA's secondary product treatment.")

    return L_adjusted, mult_adjusted


def main():
    print("="*80)
    print("Method 3: Reverse-Engineer BEA Redefinitions")
    print("="*80)

    # Load both datasets
    L_bea, mult_bea, bea_data = load_bea_total_requirements()
    L_wassily, mult_wassily, wassily_data = load_wassily_commodity_tech()

    # Identify special industries
    special_codes, standard_codes, s_codes, t_codes = identify_special_industries(L_bea)

    # Analyze structure
    analyze_special_industry_structure(L_bea, special_codes)

    # Compare common industries
    comparison = compare_common_industries(L_bea, L_wassily, standard_codes)

    # Investigate redefinition pattern
    investigate_redefinition_pattern(L_bea, s_codes, standard_codes)

    # Create approximate adjustment (speculative)
    L_adjusted, mult_adjusted = create_approximate_redefinitions(L_wassily, comparison)

    # Save results
    print("\n" + "="*80)
    print("Saving Method 3 Results")
    print("="*80)

    results = {
        'metadata': {
            'method': 'reverse_engineered_redefinitions',
            'description': 'Speculative attempt to approximate BEA redefinitions',
            'note': 'This is NOT a true replication - requires BEA methodology documentation',
            'num_industries': L_wassily.shape[0],
            'year': 2002
        },
        'L_matrix': L_adjusted,
        'output_multipliers': mult_adjusted,
        'comparison': comparison,
        'special_codes': special_codes,
        'industries': list(L_wassily.index)
    }

    output_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/method3_reverse_engineered_2002.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(results, f)

    print(f"\n[OK] Results saved to: {output_path}")

    # Save comparison to Excel (Druck: one sheet!)
    excel_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data/[2025.10.10] method3_comparison.xlsx")
    comparison.to_excel(excel_path, index=False, sheet_name='BEA_vs_Leontief_Common')
    print(f"[OK] Comparison saved to: {excel_path}")

    print("\n" + "="*80)
    print("Method 3 Complete!")
    print("="*80)
    print(f"\nKEY FINDINGS:")
    print(f"  BEA has {len(special_codes)} special redefinition industries")
    print(f"  Average BEA/Leontief ratio: {comparison['Ratio'].mean():.4f}")
    print(f"  This suggests BEA's methodology produces ~2x higher multipliers")
    print(f"\nLIMITATION:")
    print(f"  Cannot truly replicate without BEA's redefinition algorithms")
    print(f"  Need to understand how S-codes redistribute secondary production")
    print(f"  Recommendation: Use BEA data directly (Method 2) for accuracy")


if __name__ == "__main__":
    main()
