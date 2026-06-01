#!/usr/bin/env python3
"""
Transform Use and Make Tables to Industry-by-Industry
Wassily Project - Proper I-O Transformation

Implements commodity technology assumption to create
industry-by-industry direct requirements matrix.

Mathematical Approach:
1. B = commodity-by-industry direct requirements from Use table
   B = Z × diag(1/q) where q is total industry output

2. D = industry-by-commodity market shares from Make table
   D = V × diag(1/g) where g is total commodity output

3. A_industry = D × B (industry-by-industry direct requirements)

4. L_industry = (I - A_industry)^-1 (Leontief inverse)

Reference: Miller & Blair (2022), Chapter 5
"""

import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
from scipy import linalg

def load_tables():
    """Load parsed Use and Make tables."""
    print("="*80)
    print("Loading Use and Make Tables")
    print("="*80)

    use_path = Path("D:/Arcanum/Projects/Wassily/Technical/data/processed/io_table_2002.pkl")
    make_path = Path("D:/Arcanum/Projects/Wassily/Technical/data/processed/make_table_2002.pkl")

    print(f"\nLoading Use table: {use_path.name}")
    with open(use_path, 'rb') as f:
        use_table = pickle.load(f)

    print(f"Loading Make table: {make_path.name}")
    with open(make_path, 'rb') as f:
        make_table = pickle.load(f)

    print(f"\n[OK] Tables loaded")
    print(f"  Use (Z): {use_table['transactions_matrix'].shape}")
    print(f"  Make (V): {make_table['make_matrix'].shape}")

    return use_table, make_table


def align_tables(use_table, make_table):
    """
    Align Use and Make tables to common industries and commodities.

    Use: commodities × industries
    Make: industries × commodities

    Need to ensure both cover the same set of industries and commodities.
    """
    print("\n" + "="*80)
    print("Aligning Use and Make Tables")
    print("="*80)

    Z = use_table['transactions_matrix']
    V = make_table['make_matrix']

    print(f"\nOriginal dimensions:")
    print(f"  Use (Z): {Z.shape[0]} commodities × {Z.shape[1]} industries")
    print(f"  Make (V): {V.shape[0]} industries × {V.shape[1]} commodities")

    # Find common industries and commodities
    use_commodities = set(Z.index)
    use_industries = set(Z.columns)

    make_industries = set(V.index)
    make_commodities = set(V.columns)

    common_commodities = use_commodities & make_commodities
    common_industries = use_industries & make_industries

    print(f"\nCommon elements:")
    print(f"  Commodities: {len(common_commodities)}")
    print(f"  Industries: {len(common_industries)}")

    # Reindex to common sets
    common_commodities = sorted(list(common_commodities))
    common_industries = sorted(list(common_industries))

    Z_aligned = Z.loc[common_commodities, common_industries]
    V_aligned = V.loc[common_industries, common_commodities]

    print(f"\nAligned dimensions:")
    print(f"  Use (Z): {Z_aligned.shape}")
    print(f"  Make (V): {V_aligned.shape}")

    # Calculate aligned total outputs
    # q = Total industry output for B matrix (from Use table: inputs + value added)
    # g = Total commodity output for D matrix (from Make table: production by all industries)

    # Get total industry output from Use table
    q_use = use_table['total_industry_output']
    q = q_use.loc[common_industries]

    # Get total commodity output from Make table
    g = V_aligned.sum(axis=0)

    print(f"\nTotal output:")
    print(f"  Industry output (q from Use): ${q.sum()/1e6:,.1f} billion")
    print(f"  Commodity output (g from Make): ${g.sum()/1e6:,.1f} billion")

    # Check for zeros or very small values
    if (q == 0).any():
        print(f"  [WARNING] {(q == 0).sum()} industries have zero output in Use table")
    if (g == 0).any():
        print(f"  [WARNING] {(g == 0).sum()} commodities have zero output in Make table")

    return Z_aligned, V_aligned, q, g, common_industries, common_commodities


def commodity_technology_transformation(Z, V, q, g):
    """
    Apply commodity technology assumption to create industry-by-industry table.

    Args:
        Z: Use matrix (commodities × industries)
        V: Make matrix (industries × commodities)
        q: Total industry output (from V row sums)
        g: Total commodity output (from V column sums)

    Returns:
        A_industry: Industry-by-industry direct requirements matrix
    """
    print("\n" + "="*80)
    print("Commodity Technology Transformation")
    print("="*80)

    n_commodities = Z.shape[0]
    n_industries = Z.shape[1]

    print(f"\nStep 1: Calculate B matrix (commodity-by-industry direct requirements)")
    print(f"  B = Z × diag(1/q)")

    # B[i,j] = Z[i,j] / q[j]
    # How much commodity i is required per dollar of industry j output
    B = Z.div(q, axis=1).fillna(0)

    print(f"  B shape: {B.shape}")
    print(f"  B mean: {B.values.mean():.6f}")
    print(f"  B max: {B.values.max():.6f}")

    print(f"\nStep 2: Calculate D matrix (industry-by-commodity market shares)")
    print(f"  D = V × diag(1/g)")

    # D[i,j] = V[i,j] / g[j]
    # Share of commodity j output produced by industry i
    # V is industries × commodities, g is commodities
    D = V.div(g, axis=1).fillna(0)

    print(f"  D shape: {D.shape}")
    print(f"  D mean: {D.values.mean():.6f}")
    print(f"  D max: {D.values.max():.6f}")

    # Check D sums to 1 along columns (each commodity's production shares sum to 1)
    col_sums = D.sum(axis=0)
    print(f"  D column sums (should be ~1.0): mean={col_sums.mean():.4f}, min={col_sums.min():.4f}, max={col_sums.max():.4f}")

    print(f"\nStep 3: Calculate A_industry matrix")
    print(f"  A_industry = D @ B")
    print(f"  This gives: industry-by-industry direct requirements")

    # D: industries × commodities (market shares)
    # B: commodities × industries (direct requirements)
    # A_industry: industries × industries (final result)
    # A_industry[i,j] = sum over commodities k: D[i,k] * B[k,j]
    # How much output from industry i is required per dollar of industry j output
    A_industry = D @ B

    print(f"  A_industry shape: {A_industry.shape}")
    print(f"  A_industry mean: {A_industry.values.mean():.6f}")
    print(f"  A_industry max: {A_industry.values.max():.6f}")
    print(f"  A_industry sparsity: {(A_industry == 0).sum().sum() / (A_industry.shape[0] * A_industry.shape[1]) * 100:.1f}% zeros")

    return A_industry, B, D


def calculate_leontief_inverse(A_industry):
    """
    Calculate Leontief inverse from industry-by-industry direct requirements.

    Args:
        A_industry: Industry-by-industry direct requirements matrix

    Returns:
        L_industry: Leontief inverse matrix
    """
    print("\n" + "="*80)
    print("Calculate Leontief Inverse")
    print("="*80)

    n = A_industry.shape[0]
    print(f"\nMatrix size: {n} × {n}")

    # Create identity matrix
    I = np.eye(n)

    # Calculate (I - A)
    I_minus_A = I - A_industry.values

    print(f"Computing L = (I - A)^-1...")

    try:
        L_values = linalg.inv(I_minus_A)
        L_industry = pd.DataFrame(
            L_values,
            index=A_industry.index,
            columns=A_industry.columns
        )

        print(f"[OK] Leontief inverse computed!")
        print(f"  Shape: {L_industry.shape}")
        print(f"  Mean value: {L_industry.values.mean():.6f}")
        print(f"  Max value: {L_industry.values.max():.6f}")
        print(f"  Diagonal mean: {np.diag(L_industry).mean():.6f}")

        # Validate: (I - A) × L should equal I
        product = I_minus_A @ L_values
        is_identity = np.allclose(product, I, rtol=1e-5, atol=1e-8)
        print(f"  Validation: (I-A)*L = I? {is_identity}")

        if not is_identity:
            max_error = np.abs(product - I).max()
            print(f"  [WARNING] Validation failed! Max error: {max_error:.2e}")

        return L_industry

    except linalg.LinAlgError as e:
        print(f"[ERROR] Could not invert (I-A): {e}")
        print(f"Matrix may be singular or ill-conditioned")
        return None


def calculate_multipliers(L_industry):
    """Calculate output multipliers from Leontief inverse."""
    print("\n" + "="*80)
    print("Calculate Output Multipliers")
    print("="*80)

    # Output multiplier = column sum of L matrix
    multipliers = L_industry.sum(axis=0)

    print(f"\nMultipliers calculated for {len(multipliers)} industries")
    print(f"  Mean: {multipliers.mean():.4f}")
    print(f"  Min: {multipliers.min():.4f}")
    print(f"  Max: {multipliers.max():.4f}")
    print(f"  Std: {multipliers.std():.4f}")

    print(f"\nTop 10 Industries by Output Multiplier:")
    top_mult = multipliers.nlargest(10)
    for i, (ind, val) in enumerate(top_mult.items(), 1):
        print(f"  {i}. {ind}: {val:.4f}")

    return multipliers


def main():
    print("="*80)
    print("Industry-by-Industry Transformation")
    print("Commodity Technology Assumption")
    print("="*80)

    # Load tables
    use_table, make_table = load_tables()

    # Align to common industries/commodities
    Z, V, q, g, industries, commodities = align_tables(use_table, make_table)

    # Apply commodity technology transformation
    A_industry, B, D = commodity_technology_transformation(Z, V, q, g)

    # Calculate Leontief inverse
    L_industry = calculate_leontief_inverse(A_industry)

    if L_industry is None:
        print("\n[ERROR] Failed to compute Leontief inverse")
        return

    # Calculate multipliers
    multipliers = calculate_multipliers(L_industry)

    # Save results
    print("\n" + "="*80)
    print("Saving Results")
    print("="*80)

    results = {
        'metadata': {
            'transformation': 'commodity_technology',
            'num_industries': len(industries),
            'num_commodities': len(commodities),
            'year': 2002,
            'source': 'BEA'
        },
        'industries': industries,
        'commodities': commodities,
        'B_matrix': B,
        'D_matrix': D,
        'A_industry': A_industry,
        'L_industry': L_industry,
        'output_multipliers': multipliers,
        'total_industry_output': q
    }

    output_path = Path("D:/Arcanum/Projects/Wassily/Output/Data/industry_by_industry_2002.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(results, f)

    print(f"\n[OK] Results saved to: {output_path}")

    # Also save multipliers to Excel
    excel_path = Path("D:/Arcanum/Projects/Wassily/Output/Data/industry_multipliers_2002.xlsx")
    mult_df = pd.DataFrame({
        'Industry': multipliers.index,
        'Output_Multiplier': multipliers.values
    })
    mult_df.to_excel(excel_path, index=False, sheet_name='Industry_Multipliers_2002')
    print(f"[OK] Multipliers saved to Excel: {excel_path}")

    print("\n" + "="*80)
    print("Transformation Complete!")
    print("="*80)
    print(f"\nIndustry-by-industry table created using commodity technology assumption")
    print(f"  {len(industries)} industries analyzed")
    print(f"  Mean multiplier: {multipliers.mean():.4f}")
    print(f"  Ready for validation against BEA benchmarks!")


if __name__ == "__main__":
    main()
