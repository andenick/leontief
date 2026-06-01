# U.S. Input-Output Accounts: Regime Shifts and Methodological Breaks

## Purpose

This document catalogs every major methodological change in the BEA's Input-Output accounts that affects time-series comparability. Any analysis spanning multiple periods MUST account for these breaks.

---

## Critical Regime Breaks (Chronological)

### 1. First U.S. I-O Table (1947)
- **What**: Bureau of Labor Statistics produced first comprehensive I-O table
- **Sectors**: ~450 custom industry categories
- **Impact**: Origin point. No prior data exists for comparison.
- **Data**: Available from BEA historical archive (limited format)

### 2. SIC-Based Benchmark Era (1958-1992)
- **What**: Regular 5-year benchmark I-O tables using Standard Industrial Classification
- **Benchmarks**: 1958, 1963, 1967, 1972, 1977, 1982, 1987, 1992
- **Sectors**: Ranged from 370 (1958) to 537 (1977) at detailed level; ~85 at summary
- **Impact**: Relatively stable era. Cross-benchmark comparisons possible with care.
- **Key caveat**: SIC revisions occurred (1967, 1972, 1987) but were less disruptive than the later NAICS transition
- **Data availability**: 1982-1992 available as ZIP downloads from BEA; 1947-1977 from historical archive

### 3. SIC → NAICS Transition (1997) — CRITICAL BREAK
- **Severity**: **CRITICAL** — the single largest discontinuity in I-O history
- **What**: Replaced Standard Industrial Classification with North American Industry Classification System
- **Key changes**:
  - Services industries completely reorganized
  - New "Information" sector (NAICS 51) created from parts of manufacturing, communications, and services
  - Manufacturing narrowed (some activities moved to services)
  - Finance, insurance, and real estate restructured
  - Wholesale and retail trade reclassified
- **Sectors**: ~500 detailed NAICS-based industries
- **Impact on analysis**: Pre-1997 and post-1997 data are NOT directly comparable at detailed level. Summary-level concordances exist but are imperfect, especially for services.
- **Concordance**: BEA published SIC-to-NAICS bridge tables. Available in classification crosswalk files.

### 4. Chain-Weighting for Real Measures (1996 comprehensive revision)
- **Severity**: **HIGH**
- **What**: GDP and industry accounts switched from fixed-weight to chain-type Fisher indexes
- **Impact**: Real (deflated) I-O tables become non-additive. Components don't sum to totals in chained dollars. Must use contribution methodology.
- **Workaround**: Use nominal tables for structural analysis; use chain-type indexes only for growth rates.

### 5. FISIM Allocation (2003 comprehensive revision)
- **Severity**: **HIGH**
- **What**: Financial Intermediation Services Indirectly Measured (FISIM) — imputed bank service charges — were previously allocated to a single dummy sector. Now allocated to actual user industries.
- **Impact**: Intermediate consumption of financial services appears in every industry. Changes the A-matrix structure for all sectors that use banking services.
- **Affects**: 2003+ data. Retroactively applied to revised historical tables.
- **Analytical implication**: Financial sector's measured "output" changes; all sectors' intermediate input structures change.

### 6. GDP-by-Industry Integration (~2004)
- **Severity**: MEDIUM
- **What**: BEA integrated GDP-by-Industry accounts with I-O accounts for consistency
- **Impact**: Annual value-added estimates now consistent with benchmark I-O tables. Previously these were independent estimates that could diverge.
- **Benefit**: More reliable annual interpolation between benchmarks.

### 7. Supply/Use Terminology + Separate Import Tables (2007 benchmark)
- **Severity**: **HIGH**
- **What**:
  - Adopted international Supply/Use framework terminology (aligned with SNA 2008)
  - Published separate Use tables for domestic production vs imports
- **Impact**:
  - Users can now distinguish domestic intermediate flows from imported intermediates
  - The traditional "competitive imports assumption" (imports = perfect substitutes for domestic goods) is no longer the only option
  - Domestic vs total requirements tables now available
- **Analytical implication**: Multipliers calculated from domestic-only tables are smaller (and more accurate) than those from total (domestic + import) tables. Historical multipliers are overstated by the competitive imports assumption.

### 8. Annual I-O Tables Begin (~2010)
- **Severity**: MEDIUM (data availability, not a break)
- **What**: BEA began publishing annual I-O tables at the 71-industry summary level, covering 1997 onward
- **Impact**: First continuous annual I-O data. Previously, I-O data only existed for benchmark years.
- **Detail level**: 71 industries (vs 400+ in benchmarks)
  - Agriculture (2), Mining (4), Utilities (1), Construction (1)
  - Manufacturing (21), Trade (9), Transportation (6)
  - Information (5), Finance (6), Real Estate (3)
  - Professional Services (4), Education (2), Arts (2)
  - Other Services (2), Government (3)
- **Note**: "Beginning with 2007, the benchmark input-output tables are fully integrated with the annual industry accounts" (BEA website). This means 2007+ benchmarks are part of the annual system, not separate publications.

### 9. NAICS Revisions (2002, 2007, 2012, 2017, 2022)
- **Severity**: LOW to MEDIUM (each individual revision)
- **What**: NAICS updated roughly every 5 years
- **Key changes by revision**:
  - 2002: Minor adjustments
  - 2007: Internet-related industries updated (e-commerce, data processing)
  - 2012: Further tech/information sector refinements
  - 2017: Retail/wholesale trade updates; some manufacturing reclassifications
  - 2022: Most recent; affects forthcoming tables
- **Impact**: Within the 71-industry annual system, these are mostly absorbed (BEA maintains consistent 71-category classification). At detailed benchmark level, industries shift.

### 10. Treatment of Government
- **Evolution**: Government treatment has become more granular over time:
  - Federal defense vs nondefense separated
  - State and local government detail increased
  - Government enterprises treated more like businesses
- **Impact**: Affects sectoral balances calculations and government multiplier analysis.

### 11. Scrap and Secondary Products Methodology
- **Evolution**: How secondary products are "redefined" (reassigned from producing industry to primary industry) has been refined with each benchmark.
- **Impact**: Affects the "before redefinitions" vs "after redefinitions" distinction in BEA tables. The "after redefinitions" tables are more comparable across time.

---

## Regime Periods for Analysis

| Period | Classification | Annual Data? | Detail Level | Key Notes |
|--------|---------------|-------------|-------------|-----------|
| 1947-1958 | Custom/Pre-SIC | No (benchmarks only) | ~450 sectors | Historical only |
| 1958-1992 | SIC | No (benchmarks only) | 370-537 detailed, ~85 summary | Relatively stable era |
| 1997-2006 | NAICS | No (benchmark 1997, 2002) | ~500 detailed, ~70 summary | First NAICS era; no annual I-O |
| 2007-present | NAICS (integrated) | Yes (71-category annual) | 71 annual + ~400 benchmark | Modern era; annual data available |

---

## Implications for Leontief.io Analysis

1. **Pre-1997 vs Post-1997**: Cannot directly compare detailed sectors. Must use concordance tables OR aggregate to comparable summary levels.
2. **1997-2006**: Only benchmark years (1997, 2002) available. Interpolation needed for other years.
3. **2007+**: Annual 71-category data available. Benchmarks (2007, 2012, 2017) provide detailed snapshots within the annual series.
4. **Import treatment**: Pre-2007 multipliers include import leakage; post-2007 domestic-only multipliers are available and should be preferred.
5. **FISIM**: Pre-2003 financial sector structure differs from post-2003.
6. **Chain-weighting**: Don't try to add real (chained) I-O components. Use nominal for structure, chain-type for growth.

---

## Data Sources for This Document

- BEA "Concepts and Methods of the U.S. I-O Accounts" (Horowitz & Planting, 2009)
- BEA website: Historical Benchmark I-O Tables page
- BEA website: Input-Output Accounts Data page
- Miller & Blair (2009, 2022) — I-O Analysis: Foundations and Extensions (Wynne KB)
- Leontief.io research: BEA Annual IO Transition Research (2025-10-14)
- Leontief.io research: Comprehensive IO Resources Guide (2025-10-14)

*Created: 2026-03-31*
*For: Leontief.io — Regime-Aware Historical Analysis*
