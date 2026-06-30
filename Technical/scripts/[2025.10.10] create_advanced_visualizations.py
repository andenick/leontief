#!/usr/bin/env python3
"""
Advanced Visualizations for I-O Analysis
Leontief Project - Heatmaps and Network Graphs

Creates publication-quality visualizations:
1. Heatmaps of Leontief inverse matrices
2. Network graphs of inter-industry linkages
3. Correlation heatmaps between methods
4. Difference heatmaps showing methodological divergence

Author: Leontief Project
Date: October 10, 2025
"""

import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import networkx as nx
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Load all method results."""
    print("="*80)
    print("Loading Data")
    print("="*80)

    base_path = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Data")

    with open(base_path / "industry_by_industry_2002.pkl", 'rb') as f:
        method1 = pickle.load(f)

    with open(base_path / "method2_bea_direct_2002.pkl", 'rb') as f:
        method2 = pickle.load(f)

    with open(base_path / "method3_reverse_engineered_2002.pkl", 'rb') as f:
        method3 = pickle.load(f)

    print(f"\n[OK] Loaded all methods")
    return method1, method2, method3


def create_leontief_heatmap(method_data, method_name, output_path, top_n=50):
    """Create heatmap of top N×N industries in Leontief inverse."""
    print(f"\n{'='*80}")
    print(f"Creating Leontief Inverse Heatmap: {method_name}")
    print(f"{'='*80}")

    # Get L matrix and multipliers
    L = method_data['L_matrix'] if 'L_matrix' in method_data else method_data['L_industry']
    multipliers = method_data['output_multipliers']

    # Select top N industries by multiplier
    top_industries = multipliers.nlargest(top_n).index.tolist()

    # Extract submatrix
    L_sub = L.loc[top_industries, top_industries]

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 14))

    # Create heatmap
    sns.heatmap(
        L_sub,
        cmap='YlOrRd',
        cbar_kws={'label': 'Leontief Coefficient'},
        xticklabels=True,
        yticklabels=True,
        ax=ax,
        vmin=0,
        vmax=L_sub.values.max() * 0.3,  # Cap to show structure better
        linewidths=0.1,
        linecolor='gray'
    )

    ax.set_title(f'{method_name}: Leontief Inverse Matrix\nTop {top_n} Industries by Output Multiplier',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Supplying Industry', fontsize=12)
    ax.set_ylabel('Purchasing Industry', fontsize=12)

    # Rotate labels
    plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=8)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Saved heatmap to: {output_path}")


def create_method_correlation_heatmap(method1, method2, method3, output_path):
    """Create correlation heatmap between methods."""
    print(f"\n{'='*80}")
    print("Creating Method Correlation Heatmap")
    print(f"{'='*80}")

    mult1 = method1['output_multipliers']
    mult2 = method2['output_multipliers']
    mult3 = method3['output_multipliers']

    # Find common industries
    common = sorted(list(set(mult1.index) & set(mult2.index) & set(mult3.index)))

    # Create DataFrame
    df = pd.DataFrame({
        'M1_Commodity': mult1.loc[common].values,
        'M2_BEA': mult2.loc[common].values,
        'M3_Scaled': mult3.loc[common].values
    }, index=common)

    # Calculate correlation
    corr = df.corr()

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Heatmap with annotations
    sns.heatmap(
        corr,
        annot=True,
        fmt='.4f',
        cmap='coolwarm',
        center=1.0,
        vmin=0.95,
        vmax=1.0,
        square=True,
        linewidths=2,
        cbar_kws={'label': 'Correlation Coefficient'},
        ax=ax
    )

    ax.set_title('Correlation Between Methodological Approaches\nOutput Multipliers (n=416 industries)',
                fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Correlation matrix:\n{corr}")
    print(f"[OK] Saved correlation heatmap to: {output_path}")


def create_difference_heatmap(method1, method2, output_path, top_n=40):
    """Create heatmap showing where M2-M1 differences are largest."""
    print(f"\n{'='*80}")
    print("Creating Difference Heatmap (M2 - M1)")
    print(f"{'='*80}")

    L1 = method1['L_industry']
    L2 = method2['L_matrix']

    # Find common industries
    common = sorted(list(set(L1.index) & set(L2.index)))

    # Extract common submatrices
    L1_common = L1.loc[common, common]
    L2_common = L2.loc[common, common]

    # Calculate difference
    L_diff = L2_common - L1_common

    # Find industries with largest differences
    diff_sums = L_diff.abs().sum(axis=0).sort_values(ascending=False)
    top_industries = diff_sums.head(top_n).index.tolist()

    # Extract submatrix
    L_diff_sub = L_diff.loc[top_industries, top_industries]

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 14))

    # Create heatmap
    sns.heatmap(
        L_diff_sub,
        cmap='RdBu_r',
        center=0,
        cbar_kws={'label': 'Difference (M2 - M1)'},
        xticklabels=True,
        yticklabels=True,
        ax=ax,
        linewidths=0.1,
        linecolor='gray'
    )

    ax.set_title(f'Methodological Differences: BEA vs Commodity Technology\nTop {top_n} Industries by Total Difference',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Supplying Industry', fontsize=12)
    ax.set_ylabel('Purchasing Industry', fontsize=12)

    # Rotate labels
    plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=8)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Industries with largest differences:")
    print(diff_sums.head(10))
    print(f"[OK] Saved difference heatmap to: {output_path}")


def create_network_graph(method_data, method_name, output_path, top_n=30, threshold=0.1):
    """Create network graph of inter-industry linkages."""
    print(f"\n{'='*80}")
    print(f"Creating Network Graph: {method_name}")
    print(f"{'='*80}")

    L = method_data['L_matrix'] if 'L_matrix' in method_data else method_data['L_industry']
    multipliers = method_data['output_multipliers']

    # Select top N industries
    top_industries = multipliers.nlargest(top_n).index.tolist()
    L_sub = L.loc[top_industries, top_industries]

    # Create directed graph
    G = nx.DiGraph()

    # Add nodes with multiplier as attribute
    for ind in top_industries:
        G.add_node(ind, multiplier=multipliers.loc[ind])

    # Add edges (only if coefficient > threshold)
    for i, ind_i in enumerate(top_industries):
        for j, ind_j in enumerate(top_industries):
            if i != j:  # Skip diagonal
                coef = L_sub.iloc[i, j]
                if coef > threshold:
                    G.add_edge(ind_j, ind_i, weight=coef)  # ind_j supplies to ind_i

    print(f"[OK] Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Calculate layout
    pos = nx.spring_layout(G, k=1, iterations=50, seed=42)

    # Create edge trace
    edge_traces = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = G.edges[edge]['weight']

        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=weight*10, color='rgba(125,125,125,0.3)'),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)

    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        mult = G.nodes[node]['multiplier']
        degree = G.degree(node)

        node_text.append(f"Industry: {node}<br>Multiplier: {mult:.4f}<br>Connections: {degree}")
        node_size.append(mult * 5)
        node_color.append(mult)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[node[:6] for node in G.nodes()],  # Abbreviated labels
        textposition='top center',
        textfont=dict(size=8),
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(
                title="Output<br>Multiplier",
                thickness=15,
                len=0.7
            ),
            line=dict(width=1, color='white')
        )
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace],
                   layout=go.Layout(
                       title=dict(
                           text=f'{method_name}: Inter-Industry Linkage Network<br>Top {top_n} Industries (threshold={threshold})',
                           font=dict(size=16)
                       ),
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20, l=5, r=5, t=80),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       width=1400,
                       height=1000
                   ))

    fig.write_html(output_path)
    print(f"[OK] Saved network graph to: {output_path}")


def create_clustered_heatmap(method1, output_path, top_n=60):
    """Create clustered heatmap with hierarchical clustering."""
    print(f"\n{'='*80}")
    print("Creating Clustered Heatmap with Hierarchical Clustering")
    print(f"{'='*80}")

    L = method1['L_industry']
    multipliers = method1['output_multipliers']

    # Select top N industries
    top_industries = multipliers.nlargest(top_n).index.tolist()
    L_sub = L.loc[top_industries, top_industries]

    # Create figure with clustering
    g = sns.clustermap(
        L_sub,
        cmap='YlOrRd',
        figsize=(16, 14),
        vmin=0,
        vmax=L_sub.values.max() * 0.3,
        linewidths=0.1,
        linecolor='gray',
        cbar_kws={'label': 'Leontief Coefficient'},
        method='average',
        metric='euclidean'
    )

    g.fig.suptitle(f'Hierarchical Clustering of Industries\nBased on Leontief Inverse Structure (n={top_n})',
                   fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Saved clustered heatmap to: {output_path}")


def create_ratio_heatmap(method1, method2, output_path, top_n=40):
    """Create heatmap of M2/M1 ratios."""
    print(f"\n{'='*80}")
    print("Creating Ratio Heatmap (M2/M1)")
    print(f"{'='*80}")

    L1 = method1['L_industry']
    L2 = method2['L_matrix']
    mult1 = method1['output_multipliers']

    # Find common industries
    common = sorted(list(set(L1.index) & set(L2.index)))

    # Extract common submatrices
    L1_common = L1.loc[common, common]
    L2_common = L2.loc[common, common]

    # Calculate ratio (with small epsilon to avoid division by zero)
    L_ratio = L2_common / (L1_common + 1e-10)

    # Select top industries by M1 multiplier
    top_industries = mult1.loc[common].nlargest(top_n).index.tolist()
    L_ratio_sub = L_ratio.loc[top_industries, top_industries]

    # Cap extreme values for visualization
    L_ratio_sub = L_ratio_sub.clip(upper=5.0)

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 14))

    # Create heatmap
    sns.heatmap(
        L_ratio_sub,
        cmap='RdYlBu_r',
        center=1.96,
        cbar_kws={'label': 'Ratio (M2/M1)'},
        xticklabels=True,
        yticklabels=True,
        ax=ax,
        vmin=0.5,
        vmax=3.5,
        linewidths=0.1,
        linecolor='gray'
    )

    ax.set_title(f'Cell-by-Cell Ratio: BEA/Commodity Technology\nTop {top_n} Industries (ratio capped at 5.0)',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Supplying Industry', fontsize=12)
    ax.set_ylabel('Purchasing Industry', fontsize=12)

    # Rotate labels
    plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=8)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Statistics
    print(f"\n[OK] Ratio statistics:")
    print(f"     Mean: {L_ratio_sub.values.mean():.4f}")
    print(f"     Median: {np.median(L_ratio_sub.values):.4f}")
    print(f"     Std: {L_ratio_sub.values.std():.4f}")
    print(f"[OK] Saved ratio heatmap to: {output_path}")


def create_multiplier_comparison_visualization(method1, method2, method3, output_path):
    """Create comprehensive comparison visualization."""
    print(f"\n{'='*80}")
    print("Creating Multiplier Comparison Visualization")
    print(f"{'='*80}")

    mult1 = method1['output_multipliers']
    mult2 = method2['output_multipliers']
    mult3 = method3['output_multipliers']

    # Find common industries
    common = sorted(list(set(mult1.index) & set(mult2.index) & set(mult3.index)))

    # Create DataFrame
    df = pd.DataFrame({
        'Industry': common,
        'M1': mult1.loc[common].values,
        'M2': mult2.loc[common].values,
        'M3': mult3.loc[common].values
    })

    df['Ratio_M2_M1'] = df['M2'] / df['M1']
    df['Diff_M2_M1'] = df['M2'] - df['M1']

    # Create subplot figure
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # 1. Scatter: M1 vs M2
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(df['M1'], df['M2'], alpha=0.6, c=df['Ratio_M2_M1'], cmap='viridis', s=30)
    ax1.plot([df['M1'].min(), df['M1'].max()],
             [df['M1'].min(), df['M1'].max()],
             'r--', alpha=0.5, label='1:1 line')
    ax1.set_xlabel('M1: Commodity Tech', fontsize=10)
    ax1.set_ylabel('M2: BEA Official', fontsize=10)
    ax1.set_title('M2 vs M1 Correlation', fontsize=11, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Scatter: M1 vs M3
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(df['M1'], df['M3'], alpha=0.6, color='green', s=30)
    ax2.plot([df['M1'].min(), df['M1'].max()],
             [df['M1'].min() * 1.9645, df['M1'].max() * 1.9645],
             'r--', alpha=0.5, label='1.96× line')
    ax2.set_xlabel('M1: Commodity Tech', fontsize=10)
    ax2.set_ylabel('M3: Scaled', fontsize=10)
    ax2.set_title('M3 vs M1 Relationship', fontsize=11, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Scatter: M2 vs M3
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.scatter(df['M2'], df['M3'], alpha=0.6, color='orange', s=30)
    ax3.plot([df['M2'].min(), df['M2'].max()],
             [df['M2'].min(), df['M2'].max()],
             'r--', alpha=0.5, label='1:1 line')
    ax3.set_xlabel('M2: BEA Official', fontsize=10)
    ax3.set_ylabel('M3: Scaled', fontsize=10)
    ax3.set_title('M3 vs M2 (Approximation)', fontsize=11, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Histogram: Ratios
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.hist(df['Ratio_M2_M1'], bins=40, alpha=0.7, color='purple', edgecolor='black')
    ax4.axvline(df['Ratio_M2_M1'].mean(), color='red', linestyle='--',
                label=f"Mean: {df['Ratio_M2_M1'].mean():.4f}")
    ax4.set_xlabel('Ratio (M2/M1)', fontsize=10)
    ax4.set_ylabel('Frequency', fontsize=10)
    ax4.set_title('Distribution of BEA/Commodity Ratios', fontsize=11, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # 5. Histogram: Differences
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.hist(df['Diff_M2_M1'], bins=40, alpha=0.7, color='coral', edgecolor='black')
    ax5.axvline(df['Diff_M2_M1'].mean(), color='red', linestyle='--',
                label=f"Mean: {df['Diff_M2_M1'].mean():.4f}")
    ax5.set_xlabel('Difference (M2 - M1)', fontsize=10)
    ax5.set_ylabel('Frequency', fontsize=10)
    ax5.set_title('Distribution of Absolute Differences', fontsize=11, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # 6. Box plot: All methods
    ax6 = fig.add_subplot(gs[1, 2])
    box_data = [df['M1'], df['M2'], df['M3']]
    bp = ax6.boxplot(box_data, labels=['M1', 'M2', 'M3'], patch_artist=True)
    colors = ['lightblue', 'lightcoral', 'lightgreen']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax6.set_ylabel('Output Multiplier', fontsize=10)
    ax6.set_title('Distribution Comparison', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3)

    # 7. Top 20 industries comparison
    ax7 = fig.add_subplot(gs[2, :])
    top20 = df.nlargest(20, 'M2').sort_values('M2', ascending=True)
    x = np.arange(len(top20))
    width = 0.25
    ax7.barh(x - width, top20['M1'], width, label='M1: Commodity', alpha=0.8, color='#1f77b4')
    ax7.barh(x, top20['M2'], width, label='M2: BEA', alpha=0.8, color='#ff7f0e')
    ax7.barh(x + width, top20['M3'], width, label='M3: Scaled', alpha=0.8, color='#2ca02c')
    ax7.set_yticks(x)
    ax7.set_yticklabels(top20['Industry'], fontsize=8)
    ax7.set_xlabel('Output Multiplier', fontsize=10)
    ax7.set_title('Top 20 Industries by M2 Multiplier', fontsize=11, fontweight='bold')
    ax7.legend()
    ax7.grid(True, alpha=0.3, axis='x')

    plt.suptitle('Comprehensive Methodological Comparison\nLeontief Project - 2002 Benchmark I-O Analysis',
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Saved comprehensive comparison to: {output_path}")


def main():
    """Main execution function."""
    print("="*80)
    print("Advanced Visualizations Generator")
    print("Leontief Project - Input-Output Analysis")
    print("="*80)

    # Create output directory
    output_dir = (Path(os.environ.get("DATA_ROOT", ".")) / "Output/Visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    method1, method2, method3 = load_data()

    # Create visualizations
    print("\n" + "="*80)
    print("Generating Visualizations")
    print("="*80)

    # 1. Leontief heatmaps
    create_leontief_heatmap(
        method1,
        "Method 1: Commodity Technology",
        output_dir / "[2025.10.10] heatmap_leontief_m1.png",
        top_n=50
    )

    create_leontief_heatmap(
        method2,
        "Method 2: BEA Official",
        output_dir / "[2025.10.10] heatmap_leontief_m2.png",
        top_n=50
    )

    # 2. Correlation heatmap
    create_method_correlation_heatmap(
        method1, method2, method3,
        output_dir / "[2025.10.10] heatmap_method_correlation.png"
    )

    # 3. Difference heatmap
    create_difference_heatmap(
        method1, method2,
        output_dir / "[2025.10.10] heatmap_differences_m2_m1.png",
        top_n=40
    )

    # 4. Ratio heatmap
    create_ratio_heatmap(
        method1, method2,
        output_dir / "[2025.10.10] heatmap_ratios_m2_m1.png",
        top_n=40
    )

    # 5. Clustered heatmap
    create_clustered_heatmap(
        method1,
        output_dir / "[2025.10.10] heatmap_clustered.png",
        top_n=60
    )

    # 6. Network graphs
    create_network_graph(
        method1,
        "Method 1: Commodity Technology",
        output_dir / "[2025.10.10] network_graph_m1.html",
        top_n=30,
        threshold=0.1
    )

    create_network_graph(
        method2,
        "Method 2: BEA Official",
        output_dir / "[2025.10.10] network_graph_m2.html",
        top_n=30,
        threshold=0.1
    )

    # 7. Comprehensive comparison
    create_multiplier_comparison_visualization(
        method1, method2, method3,
        output_dir / "[2025.10.10] comprehensive_comparison.png"
    )

    # Summary
    print("\n" + "="*80)
    print("Visualization Generation Complete!")
    print("="*80)
    print(f"\nGenerated visualizations saved to:")
    print(f"  {output_dir}")
    print(f"\nCreated files:")
    for file in sorted(output_dir.glob("[2025.10.10]*")):
        print(f"  - {file.name}")

    print(f"\nVisualization types:")
    print(f"  ✓ Leontief inverse heatmaps (M1, M2)")
    print(f"  ✓ Method correlation heatmap")
    print(f"  ✓ Difference heatmap (M2-M1)")
    print(f"  ✓ Ratio heatmap (M2/M1)")
    print(f"  ✓ Hierarchical clustering heatmap")
    print(f"  ✓ Network graphs (M1, M2)")
    print(f"  ✓ Comprehensive comparison panel")


if __name__ == "__main__":
    main()
