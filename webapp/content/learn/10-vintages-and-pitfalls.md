---
title: Vintages and Pitfalls
order: 10
summary: Using Leontief's 28 annual tables responsibly — the 1997 SIC-to-NAICS break, other methodological shifts, the A matrix dimension artifact, and how to download the data.
---

## Twenty-Eight Years, One Classification

Leontief publishes input-output matrices for every year from 1997 through 2024 — 28 consecutive vintages, all using the identical BEA Summary 71-sector classification. That consistency is the site's central promise: because the sector definitions do not change from year to year within this series, you can place any two years side by side and read a genuine structural shift, not a reclassification artifact. [cite:bea_concepts_2009]

But that promise has limits, and the limits have names. This tutorial names them so you can use the data without inadvertently comparing apples to ballpark nachos.

## The Big Break: SIC to NAICS (1997)

The most important discontinuity in U.S. I-O history sits right at the beginning of Leontief's coverage window. The 1997 accounts were the first ever constructed under the **North American Industry Classification System (NAICS)**, which replaced the older Standard Industrial Classification (SIC) used in every prior BEA benchmark going back to 1947.

The transition was not cosmetic. NAICS reorganized the U.S. economy from scratch around production processes rather than the older commodity-based logic of SIC. The consequences for I-O tables were sweeping:

- A new **Information** sector (NAICS 51) was carved out of pieces of manufacturing (publishing, pre-press), communications (broadcasting, telecom), and business services (data processing, software). Under SIC, these activities lived in three different divisions with no structural connection.
- **Finance, insurance, and real estate** were restructured: new industries for securities, funds, and trusts appeared; older aggregations dissolved.
- **Manufacturing** shrank as activities that SIC classified as manufacturing (e.g. custom software production) migrated to services.
- **Wholesale and retail trade** boundaries moved, affecting how trade margins are allocated across the intermediate-use block.

The practical consequence: **no sector-level comparison between pre-1997 BEA tables and the Leontief series is valid without a concordance table**, and even concordance-adjusted comparisons are imperfect for services industries. Because all 28 years in our series use NAICS-based classification, this break does not affect within-series analysis — but it is the reason Leontief does not extend coverage backward to the rich 1958–1992 SIC benchmark era.

## Other Methodological Shifts Within the Series

Three further changes affect subsets of the 1997–2024 window:

**2003 — FISIM Allocation (significant for financial sector analysis).** Financial Intermediation Services Indirectly Measured (FISIM) — the imputed value of bank services funded by the spread between lending and deposit rates — were previously assigned to a single dummy sector. Beginning with the 2003 comprehensive revision, BEA allocated FISIM to the actual industries that use banking services. This changed the intermediate-input structure of every sector that borrows or deposits, and it altered the measured size of financial sector output. The revision was applied retroactively to revised historical tables, so the break is blurred rather than sharp — but users comparing financial-sector A-matrix entries around 2002–2003 should be aware of it.

**2007 — Domestic vs. Total Use Tables.** The 2007 benchmark introduced separate Use tables for domestic production and for imports, adopting the international Supply/Use framework terminology aligned with the 2008 System of National Accounts. Before 2007, only "total" Use tables (domestic + imported intermediates combined) were published. Leontief uses total-use tables throughout for consistency across the full 28-year span. The implication: multipliers derived from Leontief's pre-2007 tables include import leakage in the intermediate-flow structure, making them slightly larger than domestic-only multipliers. Post-2007 domestic-only multipliers are available on the BEA website but are not part of this series.

**Chain-weighting and real tables.** BEA switched to chain-type Fisher indexes for real (inflation-adjusted) measures in the 1996 comprehensive revision. Chain-weighted real tables are non-additive: components do not sum to totals in chained dollars. Leontief publishes **nominal (current-dollar) tables only**, which are fully additive and appropriate for structural analysis. Do not attempt to deflate our matrices and add the components.

## The A Matrix Dimension Artifact

One feature of Leontief's data that surprises new users: the direct-requirements matrix A is **not square**. It has 70 commodity rows and 71 industry columns.

This is not a bug. The BEA Use table has slightly more commodity rows than industry columns because the 71-sector industry classification does not map one-to-one onto the commodity classification used in the intermediate-use block. After dividing each cell by its industry's total output, the resulting A matrix is 70×71.

Because the Leontief inverse $L = (I-A)^{-1}$ requires a square matrix, Leontief also publishes `A_square`: A restricted to the **68×68 intersection** of row and column labels that appear in both indices. L is then computed from A_square and re-indexed to the full 71-sector scheme, yielding a **71×71** Leontief inverse. The methodology page at [/methodology](/methodology) explains the derivation in full.

**Practical rule:** use `A` when you want the complete commodity-to-industry input structure; use `A_square` or `L` when you are computing multipliers or solving $x = Lf$.

## Multipliers Over Time — With Regime Context

Output multipliers — the column sums of L, measuring total economic activity triggered by one dollar of final demand — vary meaningfully across our 28 vintages. The chart below shows the economy-wide mean multiplier for each year.

{{chart:multiplier_trend}}

A few anchors from the actual data:

| Year | Mean multiplier | Median | Notes |
|------|----------------|--------|-------|
| 1997 | 1.931 | 1.834 | First NAICS vintage |
| 2008 | 2.021 | 1.901 | Pre-crisis peak |
| 2009 | 1.890 | 1.780 | Post-crisis trough |
| 2020 | 1.880 | 1.822 | COVID shock |
| 2024 | 1.872 | 1.793 | Most recent |

These figures come directly from the VINTAGE_WALKTHROUGH data; no extrapolation or rounding beyond the published precision. Year-on-year movements reflect genuine changes in the intermediate-input structure of the U.S. economy — rising global supply chain integration, sectoral composition shifts, and the 2003 FISIM reallocation — as well as cyclical swings in capacity utilization that alter measured technical coefficients.

## Comparing 1997 and 2024: Two Leontief Inverses

The most direct way to see structural change is to look at L itself — the full matrix of total requirements — for two end-points of the series. Leontief's [Table Explorer](/tables) renders any matrix at any aggregation level.

The 1997 Leontief inverse (15-sector aggregation):

{{table:1997/L?agg=15}}

The 2024 Leontief inverse (15-sector aggregation):

{{table:2024/L?agg=15}}

Reading the two tables: entries that have grown signal deepening supply-chain integration between those sector pairs; entries that have shrunk signal substitution or domestic disintegration. The Finance row and column are among the most visibly changed over the 27-year span — consistent with the financialization trend documented in Tutorial 9.

## How to Download the Data

All matrices are available in three formats: **CSV**, **Excel (XLSX)**, and **Parquet**. For most analytical purposes CSV or Parquet are easiest. Parquet is recommended for bulk work — it preserves column types and reads roughly 10× faster than CSV in pandas or R.

**Single-matrix downloads** are available from the [Table Explorer](/tables): navigate to any year and matrix, then click the download link for your preferred format. The direct API path is `/api/table/YEAR/MATRIX.FORMAT` — for example `/api/table/2019/L.csv`.

**Bulk downloads** (all matrices for all years) are available from the [Data page](/data), which provides pre-packaged ZIP archives organized by matrix type and format. If you are building a time-series dataset spanning multiple years, bulk download is significantly faster than fetching year by year.

The complete list of matrices for each year (with dimensions, provenance, and download links) is in `site_data/site_manifest.json`, which is published alongside the site.

## Try It

```python
import pandas as pd

# Download two vintages of L (adjust URLs or use local CSV paths)
L1997 = pd.read_csv("L_1997.csv", index_col=0)
L2024 = pd.read_csv("L_2024.csv", index_col=0)

# Economy-wide mean multiplier (column sums of L)
m1997 = L1997.sum(axis=0).mean()
m2024 = L2024.sum(axis=0).mean()
print(f"1997 mean multiplier: {m1997:.4f}")  # expect ~1.931
print(f"2024 mean multiplier: {m2024:.4f}")  # expect ~1.872

# Sector-level change in total backward requirements
delta = L2024.sum() - L1997.sum()
print("Sectors with largest multiplier increase:")
print(delta.sort_values(ascending=False).head(5))
```

## Where Next

You now have the conceptual toolkit and the data-hygiene rules to work with the full Leontief series. The [Studies](/studies) section applies these tools to concrete empirical questions — labor share trends, financialization, supply-chain resilience, and structural decomposition of U.S. growth. The [Data page](/data) has bulk downloads and the API reference for programmatic access.

## Further reading

- Horowitz &amp; Planting (2009), *Concepts and Methods of the U.S. Input-Output Accounts* — BEA's documentation of vintages, revisions, and classification changes. [cite:bea_concepts_2009]
- Miller &amp; Blair (2009), ch. 4 — organization of basic data, valuation, imports, and the aggregation problem. [cite:miller_blair_2009_ch4]
