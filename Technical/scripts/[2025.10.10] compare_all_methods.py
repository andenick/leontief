#!/usr/bin/env python3
"""
Comprehensive Comparison of All 3 Methods
Wassily Project - Methodological Analysis

Compares three approaches to calculating output multipliers:
1. Method 1: Commodity Technology Assumption (D @ B transformation)
2. Method 2: BEA Total Requirements (direct load)
3. Method 3: Reverse-Engineered Redefinitions (scaled commodity tech)

Generates comprehensive comparison Excel file (Druck compliant: ONE sheet only!)
"""

import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

def load_all_methods():
    """Load results from all three methods."""
    print("="*80)
    print("Loading Results from All Methods")
    print("="*80)

    # Method 1: Commodity Technology
    print("\nMethod 1: Commodity Technology")
    method1_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/industry_by_industry_2002.pkl")
    with open(method1_path, 'rb') as f:
        method1 = pickle.load(f)
    mult1 = method1['output_multipliers']
    print(f"  Loaded {len(mult1)} multipliers")
    print(f"  Mean: {mult1.mean():.4f}, Range: {mult1.min():.4f} - {mult1.max():.4f}")

    # Method 2: BEA Direct
    print("\nMethod 2: BEA Total Requirements (Direct)")
    method2_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/method2_bea_direct_2002.pkl")
    with open(method2_path, 'rb') as f:
        method2 = pickle.load(f)
    mult2 = method2['output_multipliers']
    print(f"  Loaded {len(mult2)} multipliers")
    print(f"  Mean: {mult2.mean():.4f}, Range: {mult2.min():.4f} - {mult2.max():.4f}")

    # Method 3: Reverse-Engineered
    print("\nMethod 3: Reverse-Engineered Redefinitions")
    method3_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/method3_reverse_engineered_2002.pkl")
    with open(method3_path, 'rb') as f:
        method3 = pickle.load(f)
    mult3 = method3['output_multipliers']
    print(f"  Loaded {len(mult3)} multipliers")
    print(f"  Mean: {mult3.mean():.4f}, Range: {mult3.min():.4f} - {mult3.max():.4f}")

    return mult1, mult2, mult3, method1, method2, method3


def create_comprehensive_comparison(mult1, mult2, mult3):
    """Create side-by-side comparison of all methods."""
    print("\n" + "="*80)
    print("Creating Comprehensive Comparison")
    print("="*80)

    # Find common industries across all methods
    industries1 = set(mult1.index)
    industries2 = set(mult2.index)
    industries3 = set(mult3.index)

    # Common between M1 and M3 (both 416)
    common_13 = industries1 & industries3
    # Common with M2 (which has 426)
    common_all = common_13 & industries2

    print(f"\nIndustries in each method:")
    print(f"  Method 1 (Commodity Tech): {len(industries1)}")
    print(f"  Method 2 (BEA Direct): {len(industries2)}")
    print(f"  Method 3 (Reverse-Eng): {len(industries3)}")
    print(f"  Common to all 3: {len(common_all)}")

    # Create comparison for common industries
    common_sorted = sorted(list(common_all))

    comparison = pd.DataFrame({
        'Industry_Code': common_sorted,
        'M1_Commodity_Tech': mult1.loc[common_sorted].values,
        'M2_BEA_Official': mult2.loc[common_sorted].values,
        'M3_Scaled_CommodityTech': mult3.loc[common_sorted].values
    })

    # Calculate differences and ratios
    comparison['M2_vs_M1_Diff'] = comparison['M2_BEA_Official'] - comparison['M1_Commodity_Tech']
    comparison['M2_vs_M1_Ratio'] = comparison['M2_BEA_Official'] / comparison['M1_Commodity_Tech']

    comparison['M3_vs_M2_Diff'] = comparison['M3_Scaled_CommodityTech'] - comparison['M2_BEA_Official']
    comparison['M3_vs_M2_Ratio'] = comparison['M3_Scaled_CommodityTech'] / comparison['M2_BEA_Official']

    print(f"\nComparison Statistics (n={len(comparison)}):")
    print(f"\nMethod 1 (Commodity Technology):")
    print(f"  Mean multiplier: {comparison['M1_Commodity_Tech'].mean():.4f}")
    print(f"  Std: {comparison['M1_Commodity_Tech'].std():.4f}")

    print(f"\nMethod 2 (BEA Official):")
    print(f"  Mean multiplier: {comparison['M2_BEA_Official'].mean():.4f}")
    print(f"  Std: {comparison['M2_BEA_Official'].std():.4f}")

    print(f"\nMethod 3 (Scaled Commodity Tech):")
    print(f"  Mean multiplier: {comparison['M3_Scaled_CommodityTech'].mean():.4f}")
    print(f"  Std: {comparison['M3_Scaled_CommodityTech'].std():.4f}")

    print(f"\nBEA vs Commodity Tech (M2 vs M1):")
    print(f"  Mean ratio: {comparison['M2_vs_M1_Ratio'].mean():.4f}")
    print(f"  Std ratio: {comparison['M2_vs_M1_Ratio'].std():.4f}")
    print(f"  Mean diff: {comparison['M2_vs_M1_Diff'].mean():.4f}")

    print(f"\nScaled vs BEA (M3 vs M2):")
    print(f"  Mean ratio: {comparison['M3_vs_M2_Ratio'].mean():.4f}")
    print(f"  Std ratio: {comparison['M3_vs_M2_Ratio'].std():.4f}")
    print(f"  Mean diff: {comparison['M3_vs_M2_Diff'].mean():.4f}")

    return comparison


def analyze_bea_special_industries(mult2, comparison):
    """Analyze BEA's 10 special redefinition industries."""
    print("\n" + "="*80)
    print("BEA Special Redefinition Industries")
    print("="*80)

    all_industries = set(mult2.index)
    common_industries = set(comparison['Industry_Code'])
    special_industries = all_industries - common_industries

    special_sorted = sorted(list(special_industries))

    print(f"\nSpecial industries not in commodity tech: {len(special_sorted)}")
    print(f"\nIndustry Code | Multiplier")
    print("-" * 40)
    for ind in special_sorted:
        mult = mult2.loc[ind]
        print(f"{ind:12} | {mult:8.4f}")

    # Create summary DataFrame
    special_df = pd.DataFrame({
        'Industry_Code': special_sorted,
        'BEA_Multiplier': [mult2.loc[ind] for ind in special_sorted],
        'Type': ['Redefinition' if ind.startswith('S00') else 'Special' for ind in special_sorted]
    })

    return special_df


def generate_summary_statistics(comparison, special_df):
    """Generate summary statistics table."""
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)

    summary = pd.DataFrame({
        'Statistic': [
            'Number of Industries',
            'Mean Multiplier',
            'Std Dev',
            'Min Multiplier',
            'Max Multiplier',
            'Median',
            '25th Percentile',
            '75th Percentile'
        ],
        'M1_Commodity_Tech': [
            len(comparison),
            comparison['M1_Commodity_Tech'].mean(),
            comparison['M1_Commodity_Tech'].std(),
            comparison['M1_Commodity_Tech'].min(),
            comparison['M1_Commodity_Tech'].max(),
            comparison['M1_Commodity_Tech'].median(),
            comparison['M1_Commodity_Tech'].quantile(0.25),
            comparison['M1_Commodity_Tech'].quantile(0.75)
        ],
        'M2_BEA_Official': [
            len(comparison),
            comparison['M2_BEA_Official'].mean(),
            comparison['M2_BEA_Official'].std(),
            comparison['M2_BEA_Official'].min(),
            comparison['M2_BEA_Official'].max(),
            comparison['M2_BEA_Official'].median(),
            comparison['M2_BEA_Official'].quantile(0.25),
            comparison['M2_BEA_Official'].quantile(0.75)
        ],
        'M3_Scaled': [
            len(comparison),
            comparison['M3_Scaled_CommodityTech'].mean(),
            comparison['M3_Scaled_CommodityTech'].std(),
            comparison['M3_Scaled_CommodityTech'].min(),
            comparison['M3_Scaled_CommodityTech'].max(),
            comparison['M3_Scaled_CommodityTech'].median(),
            comparison['M3_Scaled_CommodityTech'].quantile(0.25),
            comparison['M3_Scaled_CommodityTech'].quantile(0.75)
        ]
    })

    print("\nSummary table created")
    return summary


def main():
    print("="*80)
    print("Comprehensive Methodological Comparison")
    print("Wassily Project - Input-Output Analysis")
    print("="*80)

    # Load all methods
    mult1, mult2, mult3, method1, method2, method3 = load_all_methods()

    # Create comprehensive comparison
    comparison = create_comprehensive_comparison(mult1, mult2, mult3)

    # Analyze special industries
    special_df = analyze_bea_special_industries(mult2, comparison)

    # Generate summary statistics
    summary = generate_summary_statistics(comparison, special_df)

    # Save to Excel (Druck: ONE sheet only!)
    print("\n" + "="*80)
    print("Saving Comprehensive Comparison")
    print("="*80)

    excel_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/[2025.10.10] comprehensive_methods_comparison.xlsx")

    # Create Excel with multiple sections in ONE sheet
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Start at row 0
        current_row = 0

        # Section 1: Summary Statistics
        summary.to_excel(writer, sheet_name='Complete_Analysis', startrow=current_row, index=False)
        current_row += len(summary) + 3

        # Section 2: Main Comparison (all 416 common industries)
        comparison.to_excel(writer, sheet_name='Complete_Analysis', startrow=current_row, index=False)
        current_row += len(comparison) + 3

        # Section 3: BEA Special Industries
        special_df.to_excel(writer, sheet_name='Complete_Analysis', startrow=current_row, index=False)

    print(f"\n[OK] Comprehensive comparison saved to:")
    print(f"     {excel_path}")
    print(f"\n     ONE sheet with 3 sections:")
    print(f"     1. Summary Statistics (8 rows)")
    print(f"     2. Full Industry Comparison ({len(comparison)} industries)")
    print(f"     3. BEA Special Industries ({len(special_df)} industries)")

    # Also save just the comparison DataFrame separately for easy access
    comparison_only_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/[2025.10.10] multipliers_all_methods.xlsx")
    comparison.to_excel(comparison_only_path, index=False, sheet_name='Methods_Comparison')
    print(f"\n[OK] Industry comparison also saved to:")
    print(f"     {comparison_only_path}")

    print("\n" + "="*80)
    print("Comprehensive Comparison Complete!")
    print("="*80)

    print(f"\nKEY FINDINGS:")
    print(f"  1. BEA multipliers are ~{comparison['M2_vs_M1_Ratio'].mean():.2f}x commodity tech values")
    print(f"  2. This ratio is highly consistent (std={comparison['M2_vs_M1_Ratio'].std():.4f})")
    print(f"  3. BEA's 10 special industries handle secondary production")
    print(f"  4. Scaled commodity tech (M3) approximates BEA within ~{abs(comparison['M3_vs_M2_Ratio'].mean() - 1)*100:.1f}%")

    print(f"\nMETHODOLOGICAL CONCLUSION:")
    print(f"  - Method 1 (Commodity Tech): Correct math, different assumption")
    print(f"  - Method 2 (BEA Direct): Official benchmark, use for accuracy")
    print(f"  - Method 3 (Scaled): Approximation for understanding scale")

    print(f"\nRECOMMENDATION:")
    print(f"  Use Method 2 (BEA direct) for production analysis")
    print(f"  Document Method 1 for methodological transparency")
    print(f"  Method 3 shows the transformation is primarily scalar")


if __name__ == "__main__":
    main()
