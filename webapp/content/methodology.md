---
title: Methodology
summary: How we build the matrices — BEA Supply and Use tables, derivation of A and L, vintage comparability caveats, and data provenance.
order: 10
---

## What Are Input-Output Accounts?

Input-output (I-O) accounting is a systematic way to map the flows of goods and services between every sector of an economy. For every pair of industries, an I-O table records how much of one industry's output is consumed as an intermediate input by the other. Reading down a column reveals the full supply chain behind a sector's production; reading across a row shows where that sector's output ends up. From these flows, economists can trace how a shock to one industry — say a surge in energy prices or a collapse in construction — ripples through every other sector before reaching final consumers.[cite:miller_blair_2022]

The Bureau of Economic Analysis (BEA) has published comprehensive U.S. I-O accounts since 1947. The accounts follow the international Supply-Use-Table (SUT) framework adopted by the System of National Accounts.[cite:un_handbook_2018] Leontief draws entirely from BEA's publicly available data.

## Supply and Use Tables

The BEA's I-O accounts are anchored in two rectangular tables:

**The Use Table** (also called the Make-Use "Use" table) records, for each commodity row and each industry column, the dollar value of that commodity used by that industry as an intermediate input. Additional columns record final demand categories — personal consumption, private investment, exports, and government purchases. The Use table is the workhorse for multiplier analysis and for deriving the direct-requirements matrix A.

**The Supply Table** (also called the Make table in older terminology) records, for each commodity row and each industry column, the dollar value of that commodity produced by that industry. It shows that most industries are "secondary" producers of goods outside their primary classification — a petroleum refinery produces some petrochemicals; a farm might generate rental income. The Supply table is essential for understanding the commodity composition of industry output and for constructing commodity-by-commodity or industry-by-industry total-requirements tables.

Together, Supply and Use tables underpin the full national accounting framework: they are consistent with GDP, with value added, and with the balance of trade.[cite:bea_concepts_2009]

## Our Data: Coverage and Classification

Leontief publishes matrices derived from BEA annual I-O accounts for **28 years: 1997 through 2024**. All years use the **BEA Summary 71-sector classification** — a stable, publicly documented grouping that covers all major divisions of the U.S. economy:

- Agriculture (2 sectors)
- Mining (4), Utilities (1), Construction (1)
- Manufacturing (21)
- Wholesale and Retail Trade (9)
- Transportation and Warehousing (6)
- Information (5)
- Finance and Insurance (6), Real Estate (3)
- Professional and Business Services (4)
- Educational Services, Health Care, Social Assistance (2)
- Arts, Entertainment, Recreation, Accommodation, Food Services (2)
- Other Services (2)
- Government (3)

The 71-sector annual series began in 2010 when BEA integrated annual GDP-by-Industry accounts with its benchmark I-O accounts; the series was extended backward to 1997 using the first NAICS-era benchmark. All 28 annual tables in our coverage use the identical 71-category scheme, making year-on-year comparison straightforward within this series.

{{table:2024/Use?agg=15}}

## The Matrices We Publish

For each year we publish seven matrices, available for download in CSV, Excel, JSON, and Parquet:

| Matrix | Symbol | Dimensions | Description |
|--------|--------|-----------|-------------|
| Use | — | 79 × 92 | Raw BEA Use table (commodities × industries + final demand) |
| Supply | — | 74 × 83 | Raw BEA Supply table (commodities × industries) |
| Direct Requirements | A | 70 × 71 | Technical coefficients derived from Use (see below) |
| Direct Requirements (square) | A\_square | 68 × 68 | A restricted to the row-column intersection |
| Total Requirements / Leontief Inverse | L | 71 × 71 | $(I - A_{sq})^{-1}$ extended to full 71-sector index |
| Value Added | VA | 4 × 71 | Compensation, taxes, gross operating surplus, total |
| Final Demand | FD | 70 × 19 | Final demand columns from the Use table |

## Deriving A from the Use Table

The direct-requirements matrix A (also called the technical coefficients matrix) expresses each industry's input requirements as a share of its total output. For industry $j$ and commodity $i$:

$$a_{ij} = \frac{z_{ij}}{x_j}$$

where $z_{ij}$ is the intermediate use of commodity $i$ by industry $j$ (from the Use table) and $x_j$ is the total output of industry $j$.

**An honest caveat about dimensions.** The BEA Use table has slightly more commodity rows than industry columns because the 71-sector industry classification does not map one-to-one onto the commodity classification used in the body of the Use table. After extracting the intermediate-use block and dividing by industry output, A has **70 commodity rows and 71 industry columns** — it is not square. We publish this non-square matrix as-is (key: `A`) so users have the full picture.

Because the Leontief inverse $L = (I - A)^{-1}$ requires a square matrix, we also publish `A_square`: the A matrix restricted to the **68-by-68 intersection** of rows and columns that appear in both the commodity and industry indices. L is then computed from this 68×68 square submatrix and re-indexed to the full 71-sector scheme, yielding a **71×71** Leontief inverse.

The practical implication: use `A` when you want the full commodity-to-industry structure; use `A_square` or `L` when you are computing multipliers or solving $x = Lf$.[cite:miller_blair_2022]

## The Leontief Inverse

Once A is squared, the total-requirements matrix (Leontief inverse) is:

$$L = (I - A)^{-1}$$

Each element $l_{ij}$ of L gives the total output of sector $i$ — direct and indirect — required to deliver one dollar of sector $j$'s output to final demand. The column sum $m_j = \sum_i l_{ij}$ is the **output multiplier** for sector $j$: a dollar of additional final demand for sector $j$ generates $m_j$ dollars of total economic activity.

The multiplier series can be tracked over time. Across our 28-year coverage, the economy-wide mean output multiplier has ranged from approximately 1.87 (2024) to 2.02 (2008), reflecting changing input structures, the 2008 financial crisis, and long-run shifts in the sectoral composition of output.

{{chart:multiplier_trend}}

{{table:2024/L?agg=15}}

## Vintage Comparability Caveats

Our 28-year annual series spans a period of substantial methodological change in the BEA accounts. Users who compare years across these boundaries should be aware of the following breaks:

**1997 — SIC to NAICS (CRITICAL).** The single most important discontinuity in U.S. I-O history. The 1997 accounts were the first constructed under the North American Industry Classification System (NAICS), replacing the Standard Industrial Classification (SIC) used in all prior benchmarks. The transition completely reorganized service industries: the new "Information" sector (NAICS 51) was carved from pieces of manufacturing, communications, and business services; finance, insurance, and real estate were restructured; wholesale and retail trade were reclassified. Because all 28 years in our series use NAICS-based classification, this break does not affect within-series comparisons, but it makes direct comparison with any pre-1997 BEA tables unreliable at the sector level.

**2003 — FISIM Allocation (HIGH).** Financial Intermediation Services Indirectly Measured (FISIM) — imputed charges for bank services — were previously assigned to a single dummy sector. Beginning with the 2003 comprehensive revision, they were allocated to the actual user industries. This altered the intermediate input structure of every sector that uses banking services and changed the measured size of financial sector output. The revision was applied retroactively to revised historical tables, but the change may affect sectoral comparisons around 2002–2003.

**2007 — Supply/Use Terminology and Import Split (HIGH).** The 2007 benchmark adopted the international Supply/Use framework terminology (aligned with the 2008 System of National Accounts) and published separate Use tables for domestic production and for imports. Prior to 2007, total (domestic + import) Use tables were the norm, meaning multipliers implicitly included import leakage. Our series uses total-use tables throughout for consistency; users computing domestic-only multipliers should note that pre-2007 figures are not strictly comparable to post-2007 domestic-only estimates.

**1996 comprehensive revision — Chain-Weighting (HIGH).** Real (inflation-adjusted) I-O measures switched from fixed-weight to chain-type Fisher indexes. Chain-weighted real tables are non-additive: components do not sum to totals in chained dollars. Leontief publishes nominal (current-dollar) tables, which are additive and appropriate for structural analysis.

For most year-on-year comparisons within the 1997–2024 series, these caveats matter at the margin rather than the level. The 71-sector classification is stable throughout; the main practical caution is to note the 2003 FISIM change when analyzing financial sector input structures, and to remember that multipliers including imported intermediates are somewhat larger than domestic-only multipliers.[cite:bea_concepts_2009]

## Data Provenance

All matrices are derived entirely from BEA data retrieved via the BEA API (JSON format). The three primary source series are:

- **Use tables**: `Use_IxI_Summary_YYYY.json` — the industry-by-industry summary Use table
- **Supply tables**: `Supply_IxI_Summary_YYYY.json` — the industry-by-industry summary Supply (Make) table
- **Total Requirements**: `Total_Requirements_IxI_Summary_YYYY.json` — BEA's own published Leontief inverse (used as a cross-check; Leontief's L is independently derived from A)

No proprietary data sources, licensed databases, or imputed values are used. The derivation of A and L from the raw Use tables follows standard methodology.[cite:miller_blair_2022][cite:bea_concepts_2009] The code used to fetch, parse, and compute each matrix is published alongside every download so that any user can reproduce the pipeline from scratch.

The BEA data underlying these tables is in the public domain as a product of the United States federal government.
