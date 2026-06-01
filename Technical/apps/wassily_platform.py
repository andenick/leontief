#!/usr/bin/env python3
"""
Wassily Interactive Platform
Leontief.io Project - Input-Output Analysis Explorer

A comprehensive Streamlit application for exploring Input-Output analysis results
across three methodological approaches.

Author: Arcanum Research
Date: October 10, 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Wassily Platform - I-O Analysis Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Data loading functions
@st.cache_data
def load_all_methods():
    """Load results from all three methodological approaches."""
    base_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data")

    # Method 1: Commodity Technology
    with open(base_path / "industry_by_industry_2002.pkl", 'rb') as f:
        method1 = pickle.load(f)

    # Method 2: BEA Direct
    with open(base_path / "method2_bea_direct_2002.pkl", 'rb') as f:
        method2 = pickle.load(f)

    # Method 3: Reverse-Engineered
    with open(base_path / "method3_reverse_engineered_2002.pkl", 'rb') as f:
        method3 = pickle.load(f)

    return method1, method2, method3

@st.cache_data
def load_comparison_data():
    """Load comprehensive comparison data."""
    excel_path = Path("D:/Arcanum/Projects/Leontief.io/Output/Data/[2025.10.10] comprehensive_methods_comparison.xlsx")
    return pd.read_excel(excel_path, sheet_name='Complete_Analysis')

@st.cache_data
def prepare_industry_data(method1, method2, method3):
    """Prepare combined industry-level dataset."""
    mult1 = method1['output_multipliers']
    mult2 = method2['output_multipliers']
    mult3 = method3['output_multipliers']

    # Find common industries
    common = sorted(list(set(mult1.index) & set(mult2.index) & set(mult3.index)))

    df = pd.DataFrame({
        'Industry_Code': common,
        'M1_Commodity_Tech': mult1.loc[common].values,
        'M2_BEA_Official': mult2.loc[common].values,
        'M3_Scaled': mult3.loc[common].values
    })

    # Calculate ratios and differences
    df['BEA_to_Commodity_Ratio'] = df['M2_BEA_Official'] / df['M1_Commodity_Tech']
    df['Absolute_Difference'] = df['M2_BEA_Official'] - df['M1_Commodity_Tech']

    return df

def load_data():
    """Main data loading function."""
    try:
        method1, method2, method3 = load_all_methods()
        industry_data = prepare_industry_data(method1, method2, method3)
        return method1, method2, method3, industry_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None, None

# Tab 1: Methodology Comparison
def tab_methodology_comparison(method1, method2, method3, industry_data):
    """Compare the three methodological approaches."""
    st.markdown('<p class="main-header">Methodology Comparison</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Understanding the Three Approaches to I-O Analysis</p>', unsafe_allow_html=True)

    # Overview cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Method 1: Commodity Technology")
        st.markdown("**Standard textbook approach**")
        st.metric("Industries", 416)
        st.metric("Mean Multiplier", f"{industry_data['M1_Commodity_Tech'].mean():.2f}")
        st.metric("Range", f"{industry_data['M1_Commodity_Tech'].min():.2f} - {industry_data['M1_Commodity_Tech'].max():.2f}")
        st.info("**Use case**: International comparisons, methodological transparency")

    with col2:
        st.markdown("### Method 2: BEA Official")
        st.markdown("**BEA redefinitions methodology**")
        st.metric("Industries", 426)
        st.metric("Mean Multiplier", f"{industry_data['M2_BEA_Official'].mean():.2f}")
        st.metric("Range", f"{industry_data['M2_BEA_Official'].min():.2f} - {industry_data['M2_BEA_Official'].max():.2f}")
        st.success("**Use case**: U.S. policy analysis, official statistics")

    with col3:
        st.markdown("### Method 3: Scaled")
        st.markdown("**Empirical approximation**")
        st.metric("Industries", 416)
        st.metric("Mean Multiplier", f"{industry_data['M3_Scaled'].mean():.2f}")
        st.metric("Approximation Error", "0.1%")
        st.warning("**Use case**: Understanding transformation scale")

    st.markdown("---")

    # Key finding
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("### 🔍 Key Finding: The 1.96× Relationship")
    avg_ratio = industry_data['BEA_to_Commodity_Ratio'].mean()
    std_ratio = industry_data['BEA_to_Commodity_Ratio'].std()
    st.markdown(f"""
    BEA multipliers are systematically **{avg_ratio:.4f}×** commodity technology values,
    with remarkable consistency (std = {std_ratio:.4f}). This relationship suggests BEA's
    redefinitions methodology primarily amplifies indirect effects through different
    treatment of secondary production.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Distribution comparison
    st.markdown("### Multiplier Distribution Comparison")

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=industry_data['M1_Commodity_Tech'],
        name='M1: Commodity Tech',
        opacity=0.7,
        marker_color='#1f77b4'
    ))

    fig.add_trace(go.Histogram(
        x=industry_data['M2_BEA_Official'],
        name='M2: BEA Official',
        opacity=0.7,
        marker_color='#ff7f0e'
    ))

    fig.add_trace(go.Histogram(
        x=industry_data['M3_Scaled'],
        name='M3: Scaled',
        opacity=0.7,
        marker_color='#2ca02c'
    ))

    fig.update_layout(
        barmode='overlay',
        title='Distribution of Output Multipliers Across Methods',
        xaxis_title='Output Multiplier',
        yaxis_title='Number of Industries',
        height=500,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Ratio analysis
    st.markdown("### BEA/Commodity Ratio Analysis")

    col1, col2 = st.columns(2)

    with col1:
        fig_ratio = px.histogram(
            industry_data,
            x='BEA_to_Commodity_Ratio',
            nbins=30,
            title='Distribution of BEA/Commodity Ratios',
            labels={'BEA_to_Commodity_Ratio': 'Ratio (M2/M1)'},
            color_discrete_sequence=['#8c564b']
        )
        fig_ratio.add_vline(x=avg_ratio, line_dash="dash", line_color="red",
                           annotation_text=f"Mean: {avg_ratio:.4f}")
        st.plotly_chart(fig_ratio, use_container_width=True)

    with col2:
        fig_scatter = px.scatter(
            industry_data,
            x='M1_Commodity_Tech',
            y='M2_BEA_Official',
            title='M2 vs M1: Correlation Analysis',
            labels={'M1_Commodity_Tech': 'M1: Commodity Tech', 'M2_BEA_Official': 'M2: BEA Official'},
            trendline='ols',
            color='BEA_to_Commodity_Ratio',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Statistical comparison table
    st.markdown("### Statistical Summary")

    summary_stats = pd.DataFrame({
        'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
        'M1: Commodity Tech': [
            len(industry_data),
            industry_data['M1_Commodity_Tech'].mean(),
            industry_data['M1_Commodity_Tech'].std(),
            industry_data['M1_Commodity_Tech'].min(),
            industry_data['M1_Commodity_Tech'].quantile(0.25),
            industry_data['M1_Commodity_Tech'].median(),
            industry_data['M1_Commodity_Tech'].quantile(0.75),
            industry_data['M1_Commodity_Tech'].max()
        ],
        'M2: BEA Official': [
            len(industry_data),
            industry_data['M2_BEA_Official'].mean(),
            industry_data['M2_BEA_Official'].std(),
            industry_data['M2_BEA_Official'].min(),
            industry_data['M2_BEA_Official'].quantile(0.25),
            industry_data['M2_BEA_Official'].median(),
            industry_data['M2_BEA_Official'].quantile(0.75),
            industry_data['M2_BEA_Official'].max()
        ],
        'M3: Scaled': [
            len(industry_data),
            industry_data['M3_Scaled'].mean(),
            industry_data['M3_Scaled'].std(),
            industry_data['M3_Scaled'].min(),
            industry_data['M3_Scaled'].quantile(0.25),
            industry_data['M3_Scaled'].median(),
            industry_data['M3_Scaled'].quantile(0.75),
            industry_data['M3_Scaled'].max()
        ]
    })

    st.dataframe(summary_stats.style.format({
        'M1: Commodity Tech': '{:.4f}',
        'M2: BEA Official': '{:.4f}',
        'M3: Scaled': '{:.4f}'
    }), use_container_width=True)

# Tab 2: Industry Explorer
def tab_industry_explorer(industry_data):
    """Interactive industry-level data browser."""
    st.markdown('<p class="main-header">Industry Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explore Industry-Level Output Multipliers</p>', unsafe_allow_html=True)

    # Search and filter
    col1, col2 = st.columns([2, 1])

    with col1:
        search_term = st.text_input("🔍 Search by Industry Code", placeholder="Enter industry code (e.g., 311225)")

    with col2:
        sort_by = st.selectbox("Sort by", ['M2_BEA_Official', 'M1_Commodity_Tech', 'BEA_to_Commodity_Ratio', 'Absolute_Difference'])

    # Filter data
    filtered_data = industry_data.copy()
    if search_term:
        filtered_data = filtered_data[filtered_data['Industry_Code'].str.contains(search_term, case=False)]

    filtered_data = filtered_data.sort_values(by=sort_by, ascending=False)

    # Display count
    st.markdown(f"**Showing {len(filtered_data)} of {len(industry_data)} industries**")

    # Top industries cards
    st.markdown("### Top 10 Industries")

    top10 = filtered_data.head(10)

    for idx, row in top10.iterrows():
        with st.expander(f"**{row['Industry_Code']}** - M2: {row['M2_BEA_Official']:.4f}"):
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("M1: Commodity Tech", f"{row['M1_Commodity_Tech']:.4f}")
            col2.metric("M2: BEA Official", f"{row['M2_BEA_Official']:.4f}")
            col3.metric("BEA/Commodity Ratio", f"{row['BEA_to_Commodity_Ratio']:.4f}")
            col4.metric("Absolute Difference", f"{row['Absolute_Difference']:.4f}")

            # Visual comparison
            methods = ['M1', 'M2', 'M3']
            values = [row['M1_Commodity_Tech'], row['M2_BEA_Official'], row['M3_Scaled']]

            fig = go.Figure(data=[
                go.Bar(x=methods, y=values, marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'])
            ])
            fig.update_layout(
                title=f"Multiplier Comparison: {row['Industry_Code']}",
                yaxis_title='Output Multiplier',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Full data table
    st.markdown("### Complete Industry Data")
    st.markdown("All industries with multipliers across three methods")

    st.dataframe(
        filtered_data.style.format({
            'M1_Commodity_Tech': '{:.4f}',
            'M2_BEA_Official': '{:.4f}',
            'M3_Scaled': '{:.4f}',
            'BEA_to_Commodity_Ratio': '{:.4f}',
            'Absolute_Difference': '{:.4f}'
        }),
        use_container_width=True,
        height=600
    )

# Tab 3: Impact Calculator
def tab_impact_calculator(industry_data):
    """Calculate economic impacts for user-specified investments."""
    st.markdown('<p class="main-header">Economic Impact Calculator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Estimate Total Economic Impact of Direct Investment</p>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **How to use**: Select an industry and enter a direct investment amount.
    The calculator will estimate the total economic impact (direct + indirect)
    under all three methodological approaches.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input controls
    col1, col2 = st.columns([2, 1])

    with col1:
        # Industry selection
        selected_industry = st.selectbox(
            "Select Industry",
            options=industry_data['Industry_Code'].tolist(),
            index=0
        )

    with col2:
        # Investment amount
        investment = st.number_input(
            "Direct Investment ($M)",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=10.0
        )

    # Get multipliers for selected industry
    industry_row = industry_data[industry_data['Industry_Code'] == selected_industry].iloc[0]

    # Calculate impacts
    impact_m1 = investment * industry_row['M1_Commodity_Tech']
    impact_m2 = investment * industry_row['M2_BEA_Official']
    impact_m3 = investment * industry_row['M3_Scaled']

    # Display results
    st.markdown("---")
    st.markdown("### Estimated Total Economic Impact")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Method 1: Commodity Tech")
        st.metric("Total Impact", f"${impact_m1:.2f}M")
        st.metric("Indirect Impact", f"${impact_m1 - investment:.2f}M")
        st.metric("Multiplier", f"{industry_row['M1_Commodity_Tech']:.4f}")

    with col2:
        st.markdown("#### Method 2: BEA Official")
        st.metric("Total Impact", f"${impact_m2:.2f}M")
        st.metric("Indirect Impact", f"${impact_m2 - investment:.2f}M")
        st.metric("Multiplier", f"{industry_row['M2_BEA_Official']:.4f}")

    with col3:
        st.markdown("#### Method 3: Scaled")
        st.metric("Total Impact", f"${impact_m3:.2f}M")
        st.metric("Indirect Impact", f"${impact_m3 - investment:.2f}M")
        st.metric("Multiplier", f"{industry_row['M3_Scaled']:.4f}")

    # Difference analysis
    st.markdown("---")
    st.markdown("### Methodological Sensitivity Analysis")

    diff_m2_m1 = impact_m2 - impact_m1
    pct_diff = (diff_m2_m1 / impact_m1) * 100

    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.markdown(f"""
    **Impact Difference (M2 vs M1)**: ${diff_m2_m1:.2f}M ({pct_diff:.1f}% higher under BEA methodology)

    This difference could affect policy decisions if your cost-benefit threshold falls between
    ${impact_m1:.2f}M and ${impact_m2:.2f}M.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Visualization
    methods = ['Method 1\n(Commodity Tech)', 'Method 2\n(BEA Official)', 'Method 3\n(Scaled)']
    total_impacts = [impact_m1, impact_m2, impact_m3]
    indirect_impacts = [impact_m1 - investment, impact_m2 - investment, impact_m3 - investment]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Direct Investment',
        x=methods,
        y=[investment] * 3,
        marker_color='lightblue'
    ))

    fig.add_trace(go.Bar(
        name='Indirect Impact',
        x=methods,
        y=indirect_impacts,
        marker_color='darkblue'
    ))

    fig.update_layout(
        barmode='stack',
        title=f'Economic Impact Breakdown: ${investment:.0f}M Investment in {selected_industry}',
        yaxis_title='Economic Impact ($M)',
        height=500,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Comparison table
    st.markdown("### Detailed Comparison")

    comparison_df = pd.DataFrame({
        'Method': methods,
        'Multiplier': [industry_row['M1_Commodity_Tech'], industry_row['M2_BEA_Official'], industry_row['M3_Scaled']],
        'Direct Investment ($M)': [investment] * 3,
        'Total Impact ($M)': total_impacts,
        'Indirect Impact ($M)': indirect_impacts,
        'Impact Ratio': [impact_m1/impact_m1, impact_m2/impact_m1, impact_m3/impact_m1]
    })

    st.dataframe(
        comparison_df.style.format({
            'Multiplier': '{:.4f}',
            'Direct Investment ($M)': '${:.2f}',
            'Total Impact ($M)': '${:.2f}',
            'Indirect Impact ($M)': '${:.2f}',
            'Impact Ratio': '{:.2f}×'
        }),
        use_container_width=True
    )

# Tab 4: Sector Analysis
def tab_sector_analysis(industry_data):
    """Visualize sector-level patterns and relationships."""
    st.markdown('<p class="main-header">Sector Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visualizing Patterns in Output Multipliers</p>', unsafe_allow_html=True)

    # Scatter plot: M1 vs M2
    st.markdown("### Correlation Analysis: M1 vs M2")

    fig = px.scatter(
        industry_data,
        x='M1_Commodity_Tech',
        y='M2_BEA_Official',
        color='BEA_to_Commodity_Ratio',
        size='Absolute_Difference',
        hover_data=['Industry_Code'],
        title='BEA Official vs Commodity Technology Multipliers',
        labels={
            'M1_Commodity_Tech': 'M1: Commodity Technology Multiplier',
            'M2_BEA_Official': 'M2: BEA Official Multiplier',
            'BEA_to_Commodity_Ratio': 'Ratio (M2/M1)'
        },
        color_continuous_scale='RdYlBu_r',
        height=600
    )

    # Add diagonal reference line
    max_val = max(industry_data['M1_Commodity_Tech'].max(), industry_data['M2_BEA_Official'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='1:1 Line',
        showlegend=True
    ))

    st.plotly_chart(fig, use_container_width=True)

    # Box plots
    st.markdown("### Distribution Comparison")

    col1, col2 = st.columns(2)

    with col1:
        fig_box = go.Figure()
        fig_box.add_trace(go.Box(y=industry_data['M1_Commodity_Tech'], name='M1', marker_color='#1f77b4'))
        fig_box.add_trace(go.Box(y=industry_data['M2_BEA_Official'], name='M2', marker_color='#ff7f0e'))
        fig_box.add_trace(go.Box(y=industry_data['M3_Scaled'], name='M3', marker_color='#2ca02c'))
        fig_box.update_layout(title='Multiplier Distributions', yaxis_title='Output Multiplier', height=400)
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        fig_box_ratio = go.Figure()
        fig_box_ratio.add_trace(go.Box(y=industry_data['BEA_to_Commodity_Ratio'], marker_color='#8c564b'))
        fig_box_ratio.update_layout(
            title='BEA/Commodity Ratio Distribution',
            yaxis_title='Ratio (M2/M1)',
            height=400,
            showlegend=False
        )
        fig_box_ratio.add_hline(y=1.9645, line_dash="dash", line_color="red", annotation_text="Mean: 1.9645")
        st.plotly_chart(fig_box_ratio, use_container_width=True)

    # Top and bottom performers
    st.markdown("### Extreme Multipliers")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top 10 Multipliers (M2: BEA)")
        top10_m2 = industry_data.nlargest(10, 'M2_BEA_Official')[['Industry_Code', 'M2_BEA_Official', 'M1_Commodity_Tech', 'BEA_to_Commodity_Ratio']]
        st.dataframe(top10_m2.style.format({
            'M2_BEA_Official': '{:.4f}',
            'M1_Commodity_Tech': '{:.4f}',
            'BEA_to_Commodity_Ratio': '{:.4f}'
        }), use_container_width=True)

    with col2:
        st.markdown("#### Bottom 10 Multipliers (M2: BEA)")
        bottom10_m2 = industry_data.nsmallest(10, 'M2_BEA_Official')[['Industry_Code', 'M2_BEA_Official', 'M1_Commodity_Tech', 'BEA_to_Commodity_Ratio']]
        st.dataframe(bottom10_m2.style.format({
            'M2_BEA_Official': '{:.4f}',
            'M1_Commodity_Tech': '{:.4f}',
            'BEA_to_Commodity_Ratio': '{:.4f}'
        }), use_container_width=True)

    # Ratio outliers
    st.markdown("### Ratio Outliers: Industries with Unusual M2/M1 Relationships")

    mean_ratio = industry_data['BEA_to_Commodity_Ratio'].mean()
    std_ratio = industry_data['BEA_to_Commodity_Ratio'].std()

    outliers = industry_data[
        (industry_data['BEA_to_Commodity_Ratio'] > mean_ratio + 2*std_ratio) |
        (industry_data['BEA_to_Commodity_Ratio'] < mean_ratio - 2*std_ratio)
    ].sort_values('BEA_to_Commodity_Ratio', ascending=False)

    if len(outliers) > 0:
        st.dataframe(outliers[['Industry_Code', 'M1_Commodity_Tech', 'M2_BEA_Official', 'BEA_to_Commodity_Ratio']].style.format({
            'M1_Commodity_Tech': '{:.4f}',
            'M2_BEA_Official': '{:.4f}',
            'BEA_to_Commodity_Ratio': '{:.4f}'
        }), use_container_width=True)

        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown(f"""
        Found **{len(outliers)} outlier industries** with ratios >2 standard deviations from mean.
        These industries show unusually large or small differences between methodologies,
        suggesting particularly significant effects of BEA's redefinitions treatment.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No significant outliers detected. The 1.96× relationship is remarkably consistent across all industries.")

# Tab 5: Special Industries
def tab_special_industries(method2):
    """Deep dive into BEA's special redefinition industries."""
    st.markdown('<p class="main-header">Special Redefinition Industries</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">BEA\'s 10 Special S-codes and T-codes</p>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **What are Special Industries?**
    BEA's "redefinitions after redefinitions" methodology creates 10 special industry codes
    (S00xxx and T010) that handle secondary production differently from standard classification.
    These industries appear in BEA's Total Requirements matrix but not in standard Use/Make tables.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Identify special industries
    mult2 = method2['output_multipliers']
    all_industries = mult2.index.tolist()

    s_codes = sorted([code for code in all_industries if code.startswith('S00')])
    t_codes = sorted([code for code in all_industries if code.startswith('T0')])
    special_codes = s_codes + t_codes

    st.markdown(f"### Found {len(special_codes)} Special Industries")
    st.markdown(f"- **S-codes** (Secondary product redefinitions): {len(s_codes)}")
    st.markdown(f"- **T-codes** (Unknown type): {len(t_codes)}")

    # Special industries table
    special_df = pd.DataFrame({
        'Industry_Code': special_codes,
        'Output_Multiplier': [mult2.loc[code] for code in special_codes],
        'Type': ['S-code (Redefinition)' if code.startswith('S00') else 'T-code (Special)' for code in special_codes]
    }).sort_values('Output_Multiplier', ascending=False)

    st.markdown("### Special Industries Multipliers")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Bar chart
        fig = px.bar(
            special_df,
            x='Industry_Code',
            y='Output_Multiplier',
            color='Type',
            title='Output Multipliers for Special Industries',
            labels={'Output_Multiplier': 'Output Multiplier'},
            color_discrete_map={
                'S-code (Redefinition)': '#e74c3c',
                'T-code (Special)': '#9b59b6'
            },
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            special_df.style.format({'Output_Multiplier': '{:.4f}'}),
            use_container_width=True,
            height=400
        )

    # Highlight S00201 (Petroleum)
    st.markdown("---")
    st.markdown("### 🔥 Spotlight: S00201 (Petroleum Redefinition)")

    if 'S00201' in special_codes:
        s00201_mult = mult2.loc['S00201']

        col1, col2, col3 = st.columns(3)
        col1.metric("Output Multiplier", f"{s00201_mult:.4f}")
        col2.metric("Rank", "1st (Highest)")
        col3.metric("Above Mean", f"{((s00201_mult / mult2.mean()) - 1) * 100:.1f}%")

        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown(f"""
        **S00201 has the highest multiplier (8.63) of all 426 BEA industries**, nearly 2× the mean multiplier (4.34).
        This special petroleum redefinition industry aggregates and redistributes petroleum-related secondary production,
        creating an industry with exceptionally strong inter-industry linkages.

        **Policy implication**: Energy policy conclusions are **highly sensitive** to whether this special
        industry is included in analysis. Standard commodity technology approach doesn't have an S00201 equivalent.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # Comparison with standard industries
    st.markdown("---")
    st.markdown("### Special vs Standard Industries")

    standard_codes = [code for code in all_industries if not (code.startswith('S00') or code.startswith('T0'))]

    standard_mult_mean = mult2.loc[standard_codes].mean()
    special_mult_mean = mult2.loc[special_codes].mean()

    comparison_data = pd.DataFrame({
        'Category': ['Standard Industries', 'Special Industries'],
        'Count': [len(standard_codes), len(special_codes)],
        'Mean Multiplier': [standard_mult_mean, special_mult_mean],
        'Max Multiplier': [mult2.loc[standard_codes].max(), mult2.loc[special_codes].max()],
        'Min Multiplier': [mult2.loc[standard_codes].min(), mult2.loc[special_codes].min()]
    })

    st.dataframe(
        comparison_data.style.format({
            'Mean Multiplier': '{:.4f}',
            'Max Multiplier': '{:.4f}',
            'Min Multiplier': '{:.4f}'
        }),
        use_container_width=True
    )

    # Distribution comparison
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Box(
        y=mult2.loc[standard_codes],
        name='Standard Industries',
        marker_color='#3498db'
    ))
    fig_comp.add_trace(go.Box(
        y=mult2.loc[special_codes],
        name='Special Industries',
        marker_color='#e74c3c'
    ))
    fig_comp.update_layout(
        title='Multiplier Distribution: Standard vs Special Industries',
        yaxis_title='Output Multiplier',
        height=400
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# Tab 6: Data Export
def tab_data_export(method1, method2, method3, industry_data):
    """Download capabilities for all data."""
    st.markdown('<p class="main-header">Data Export</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Download Analysis Results and Raw Data</p>', unsafe_allow_html=True)

    st.markdown("""
    Export data in various formats for further analysis, integration with other tools,
    or inclusion in reports. All exports follow **Druck standards** (one sheet per Excel file).
    """)

    st.markdown("---")

    # Export options
    st.markdown("### Available Exports")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Industry-Level Data")

        # Combined multipliers CSV
        csv_combined = industry_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Combined Multipliers (CSV)",
            data=csv_combined,
            file_name="wassily_combined_multipliers.csv",
            mime="text/csv"
        )

        # Method 1 only
        csv_m1 = industry_data[['Industry_Code', 'M1_Commodity_Tech']].to_csv(index=False)
        st.download_button(
            label="📥 Download M1 Multipliers (CSV)",
            data=csv_m1,
            file_name="wassily_method1_multipliers.csv",
            mime="text/csv"
        )

        # Method 2 only
        csv_m2 = industry_data[['Industry_Code', 'M2_BEA_Official']].to_csv(index=False)
        st.download_button(
            label="📥 Download M2 Multipliers (CSV)",
            data=csv_m2,
            file_name="wassily_method2_multipliers.csv",
            mime="text/csv"
        )

    with col2:
        st.markdown("#### 📈 Summary Statistics")

        # Summary stats
        summary = pd.DataFrame({
            'Statistic': ['Count', 'Mean', 'Std', 'Min', '25%', 'Median', '75%', 'Max'],
            'M1': [len(industry_data), industry_data['M1_Commodity_Tech'].mean(), industry_data['M1_Commodity_Tech'].std(),
                   industry_data['M1_Commodity_Tech'].min(), industry_data['M1_Commodity_Tech'].quantile(0.25),
                   industry_data['M1_Commodity_Tech'].median(), industry_data['M1_Commodity_Tech'].quantile(0.75),
                   industry_data['M1_Commodity_Tech'].max()],
            'M2': [len(industry_data), industry_data['M2_BEA_Official'].mean(), industry_data['M2_BEA_Official'].std(),
                   industry_data['M2_BEA_Official'].min(), industry_data['M2_BEA_Official'].quantile(0.25),
                   industry_data['M2_BEA_Official'].median(), industry_data['M2_BEA_Official'].quantile(0.75),
                   industry_data['M2_BEA_Official'].max()],
            'M3': [len(industry_data), industry_data['M3_Scaled'].mean(), industry_data['M3_Scaled'].std(),
                   industry_data['M3_Scaled'].min(), industry_data['M3_Scaled'].quantile(0.25),
                   industry_data['M3_Scaled'].median(), industry_data['M3_Scaled'].quantile(0.75),
                   industry_data['M3_Scaled'].max()]
        })

        csv_summary = summary.to_csv(index=False)
        st.download_button(
            label="📥 Download Summary Statistics (CSV)",
            data=csv_summary,
            file_name="wassily_summary_statistics.csv",
            mime="text/csv"
        )

        # Ratio statistics
        ratio_stats = pd.DataFrame({
            'Statistic': ['Mean', 'Std', 'Min', 'Max', 'CV'],
            'BEA/Commodity Ratio': [
                industry_data['BEA_to_Commodity_Ratio'].mean(),
                industry_data['BEA_to_Commodity_Ratio'].std(),
                industry_data['BEA_to_Commodity_Ratio'].min(),
                industry_data['BEA_to_Commodity_Ratio'].max(),
                industry_data['BEA_to_Commodity_Ratio'].std() / industry_data['BEA_to_Commodity_Ratio'].mean()
            ]
        })

        csv_ratio = ratio_stats.to_csv(index=False)
        st.download_button(
            label="📥 Download Ratio Statistics (CSV)",
            data=csv_ratio,
            file_name="wassily_ratio_statistics.csv",
            mime="text/csv"
        )

    st.markdown("---")

    # Data preview
    st.markdown("### Data Preview")
    st.markdown("Preview before downloading to ensure format meets your needs:")

    preview_option = st.selectbox(
        "Select data to preview",
        ["Combined Multipliers", "M1 Only", "M2 Only", "Summary Statistics", "Ratio Statistics"]
    )

    if preview_option == "Combined Multipliers":
        st.dataframe(industry_data.head(20), use_container_width=True)
    elif preview_option == "M1 Only":
        st.dataframe(industry_data[['Industry_Code', 'M1_Commodity_Tech']].head(20), use_container_width=True)
    elif preview_option == "M2 Only":
        st.dataframe(industry_data[['Industry_Code', 'M2_BEA_Official']].head(20), use_container_width=True)
    elif preview_option == "Summary Statistics":
        st.dataframe(summary, use_container_width=True)
    else:
        st.dataframe(ratio_stats, use_container_width=True)

    st.markdown("---")

    # Citation
    st.markdown("### 📝 Citation")
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    If you use Wassily data in your research or analysis, please cite:

    **Wassily (Leontief.io) Project**. (2025). *Input-Output Analysis: Methodological Comparison of
    Commodity Technology and BEA Redefinitions Approaches*. Arcanum Research.

    Data source: Bureau of Economic Analysis, 2002 Benchmark Input-Output Accounts.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Main application
## ==================== NEW TIME-SERIES TABS (1997-2024) ====================

OUTPUTS_DIR = Path(__file__).parent.parent.parent / "Outputs" / "Data"
REGIME_BREAKS = {2003: "FISIM allocation", 2007: "Supply/Use + Import split"}


def _load_ts_excel(filename):
    """Load a time-series Excel file, return DataFrame or empty."""
    path = OUTPUTS_DIR / filename
    if path.exists():
        return pd.read_excel(path, index_col=0)
    return pd.DataFrame()


def tab_timeseries_explorer():
    """Tab 7: Time Series Explorer — multipliers across 28 years."""
    st.header("Time Series Explorer (1997-2024)")

    mult = _load_ts_excel("multiplier_timeseries_1997_2024.xlsx")
    if mult.empty:
        st.warning("Multiplier time series not found. Run run_historical_analysis.py first.")
        return

    sectors = ["Aggregate Mean"] + sorted(mult.columns.tolist())
    selected = st.selectbox("Select sector", sectors)

    if selected == "Aggregate Mean":
        series = mult.mean(axis=1)
        title = "Mean Output Multiplier (all sectors)"
    else:
        series = mult[selected]
        title = f"Output Multiplier: {selected}"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines+markers", name=title))

    for year, label in REGIME_BREAKS.items():
        fig.add_vline(x=year, line_dash="dash", line_color="red", opacity=0.5,
                      annotation_text=label, annotation_position="top left")

    fig.update_layout(title=title, xaxis_title="Year", yaxis_title="Multiplier",
                      height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Data")
    if selected == "Aggregate Mean":
        st.dataframe(pd.DataFrame({"year": series.index, "mean_multiplier": series.values}))
    else:
        st.dataframe(mult[[selected]])


def tab_structural_change():
    """Tab 8: Structural Change — cosine similarity + SDA."""
    st.header("Structural Change Analysis")

    sc = _load_ts_excel("structural_change_1997_2024.xlsx")
    sda = _load_ts_excel("structural_decomposition_pairs.xlsx")

    col1, col2 = st.columns(2)

    with col1:
        if not sc.empty and "cosine_similarity" in sc.columns:
            st.subheader("Structural Similarity (Year-to-Year)")
            labels = [f"{int(sc.iloc[i].get('year_from', i))}-{int(sc.iloc[i].get('year_to', i+1))}"
                      if 'year_from' in sc.columns
                      else str(sc.index[i]) for i in range(len(sc))]
            fig = px.bar(x=labels, y=sc["cosine_similarity"].values,
                         labels={"x": "Year Pair", "y": "Cosine Similarity"},
                         title="A-Matrix Similarity Between Consecutive Years")
            fig.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Lower = more structural change. 2008-2009 shows the Great Recession disruption.")

    with col2:
        if not sda.empty and "demand_effect" in sda.columns:
            st.subheader("Structural Decomposition (SDA)")
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Demand Effect", x=sda.index, y=sda["demand_effect"]))
            fig.add_trace(go.Bar(name="Technology Effect", x=sda.index, y=sda["technology_effect"]))
            fig.update_layout(barmode="relative", title="Demand vs Technology Effects",
                              height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)


def tab_distribution_labor():
    """Tab 9: Distribution & Labor Share."""
    st.header("Income Distribution & Labor")

    true_ls = _load_ts_excel("true_labor_share_1997_2024.xlsx")
    emp = _load_ts_excel("employment_multipliers_1997_2024.xlsx")

    if not true_ls.empty and "labor_share" in true_ls.columns:
        st.subheader("Labor Share of Value Added (GDP-by-Industry)")
        fig = px.line(x=true_ls.index, y=true_ls["labor_share"],
                      labels={"x": "Year", "y": "Labor Share"},
                      title="Compensation / Value Added (1997-2024)")
        for year, label in REGIME_BREAKS.items():
            fig.add_vline(x=year, line_dash="dash", line_color="red", opacity=0.4)
        fig.update_layout(height=400, template="plotly_white",
                          yaxis_tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("2000 Labor Share", f"{true_ls.loc[2000, 'labor_share']:.1%}"
                       if 2000 in true_ls.index else "N/A")
        with col2:
            latest = true_ls.index.max()
            st.metric(f"{latest} Labor Share", f"{true_ls.loc[latest, 'labor_share']:.1%}")
        with col3:
            if 2000 in true_ls.index:
                change = true_ls.loc[latest, 'labor_share'] - true_ls.loc[2000, 'labor_share']
                st.metric("Change since 2000", f"{change:+.1%}")

    if not emp.empty:
        st.subheader("Employment (Compensation) Multipliers")
        mean_emp = emp.mean(axis=1)
        fig = px.line(x=mean_emp.index, y=mean_emp.values,
                      title="Mean Employment Multiplier (1997-2024)",
                      labels={"x": "Year", "y": "Multiplier"})
        fig.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)


def tab_structural_narratives():
    """Tab 10: Cross-cutting structural narratives."""
    st.header("Structural Narratives (1997-2024)")

    fin = _load_ts_excel("financialization_1997_2024.xlsx")
    deind = _load_ts_excel("deindustrialization_1997_2024.xlsx")
    imp = _load_ts_excel("import_dependency_1997_2024.xlsx")
    ks = _load_ts_excel("key_sector_stability.xlsx")
    covid = _load_ts_excel("covid_structural_shift.xlsx")

    col1, col2 = st.columns(2)

    with col1:
        if not fin.empty and "financial_va_share" in fin.columns:
            st.subheader("Financialization")
            fig = px.line(x=fin.index, y=fin["financial_va_share"],
                          title="Financial Sector Share of Value Added",
                          labels={"x": "Year", "y": "Share"})
            fig.update_layout(height=350, template="plotly_white", yaxis_tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if not deind.empty and "manufacturing_va_share" in deind.columns:
            st.subheader("Deindustrialization")
            fig = px.line(x=deind.index, y=deind["manufacturing_va_share"],
                          title="Manufacturing Share of Value Added",
                          labels={"x": "Year", "y": "Share"})
            fig.update_layout(height=350, template="plotly_white", yaxis_tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if not imp.empty and "import_dependency" in imp.columns:
            st.subheader("Import Dependency (Globalization)")
            fig = px.line(x=imp.index, y=imp["import_dependency"],
                          title="Import Content of Domestic Production",
                          labels={"x": "Year", "y": "Ratio"})
            fig.update_layout(height=350, template="plotly_white", yaxis_tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if not ks.empty and "years_as_key" in ks.columns:
            st.subheader("Key Sector Stability")
            top = ks.head(15)
            fig = px.bar(x=top.index, y=top["years_as_key"],
                         title="Sectors Most Frequently Classified as 'Key'",
                         labels={"x": "Sector", "y": "Years as Key Sector"})
            fig.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    if not covid.empty and "total_change" in covid.columns:
        st.subheader("COVID Structural Disruption (2019 vs 2020)")
        top20 = covid.head(20)
        fig = px.bar(x=top20.index, y=top20["total_change"],
                     title="Top 20 Most Disrupted Sectors (2019-2020)",
                     labels={"x": "Sector", "y": "Absolute A-Matrix Change"})
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main application logic."""

    # Header
    st.markdown('<p class="main-header">Wassily Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive Input-Output Analysis Explorer</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Wassily", use_column_width=True)
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        **Wassily** (Leontief.io) is a comprehensive platform for exploring Input-Output analysis
        results across three methodological approaches.

        Named after Wassily Leontief, Nobel laureate and pioneer of Input-Output economics.
        """)
        st.markdown("---")
        st.markdown("### Data Source")
        st.markdown("**BEA 2002 Benchmark I-O Tables**")
        st.markdown("- 416-426 industries")
        st.markdown("- 430 commodities")
        st.markdown("---")
        st.markdown("### Methods")
        st.markdown("**M1**: Commodity Technology")
        st.markdown("**M2**: BEA Official")
        st.markdown("**M3**: Scaled Approximation")
        st.markdown("---")
        st.markdown("### Key Finding")
        st.metric("BEA/Commodity Ratio", "1.96×")
        st.markdown("BEA multipliers are systematically **1.96×** commodity technology values")

    # Load data
    with st.spinner("Loading data..."):
        method1, method2, method3, industry_data = load_data()

    if method1 is None:
        st.error("Failed to load data. Please check that all required files are in the Output/Data directory.")
        return

    # Tabs
    tabs = st.tabs([
        "📊 Methodology Comparison",
        "🔍 Industry Explorer",
        "🧮 Impact Calculator",
        "📈 Sector Analysis",
        "⚙️ Special Industries",
        "💾 Data Export",
        "📉 Time Series (1997-2024)",
        "🔄 Structural Change",
        "💰 Distribution & Labor",
        "🏭 Structural Narratives",
    ])

    with tabs[0]:
        tab_methodology_comparison(method1, method2, method3, industry_data)

    with tabs[1]:
        tab_industry_explorer(industry_data)

    with tabs[2]:
        tab_impact_calculator(industry_data)

    with tabs[3]:
        tab_sector_analysis(industry_data)

    with tabs[4]:
        tab_special_industries(method2)

    with tabs[5]:
        tab_data_export(method1, method2, method3, industry_data)

    with tabs[6]:
        tab_timeseries_explorer()

    with tabs[7]:
        tab_structural_change()

    with tabs[8]:
        tab_distribution_labor()

    with tabs[9]:
        tab_structural_narratives()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p><strong>Wassily Platform v2.0</strong> | Leontief.io Project | Arcanum Research</p>
        <p>Built with Streamlit | Data: BEA I-O Tables 1997-2024 (28 years) + 2002 Benchmark</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
