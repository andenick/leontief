# U.S. Input-Output Tables: Complete Vintage Walkthrough

## Overview

This document covers 14 benchmark tables (1947-2017) and 28 years of annual data (1997-2024).

## Sector Count Evolution

| Year | Detailed | Summary | Classification |
|------|----------|---------|---------------|
| 1947 | 85 | 85 | pre_sic |
| 1958 | 85 | 85 | sic_1957 |
| 1963 | 367 | 85 | sic_1957 |
| 1967 | 484 | 85 | sic_1967 |
| 1972 | 496 | 85 | sic_1972 |
| 1977 | 537 | 85 | sic_1977 |
| 1982 | 498 | 97 | sic_1977 |
| 1987 | 498 | 97 | sic_1987 |
| 1992 | 498 | 97 | sic_1987 |
| 1997 | 491 | 71 | naics_1997 |
| 2002 | 426 | 71 | naics_2002 |
| 2007 | 389 | 71 | naics_2007 |
| 2012 | 402 | 71 | naics_2012 |
| 2017 | 405 | 71 | naics_2017 |

## Table Type Evolution

| Year | Table Types | Make/Use | Import Split | Redefinitions |
|------|------------|----------|-------------|--------------|
| 1947 | transactions | No | No | No |
| 1958 | transactions | No | No | No |
| 1963 | transactions | No | No | No |
| 1967 | transactions, make, use | Yes | No | No |
| 1972 | transactions, make, use, IxI_TR... | Yes | No | No |
| 1977 | make, use, IxI_TR, CxC_TR... | Yes | No | No |
| 1982 | make, use, IxI_TR, CxC_TR... | Yes | No | No |
| 1987 | make, use, IxI_TR, CxC_TR... | Yes | No | No |
| 1992 | make, use, IxI_TR, CxC_TR... | Yes | No | No |
| 1997 | make, use, IxI_TR, CxC_TR... | Yes | No | Yes |
| 2002 | make, use, IxI_TR, CxC_TR... | Yes | No | Yes |
| 2007 | make, use, IxI_TR, CxC_TR... | Yes | Yes | Yes |
| 2012 | make, use, IxI_TR, CxC_TR... | Yes | Yes | Yes |
| 2017 | make, use, IxI_TR, CxC_TR... | Yes | Yes | Yes |

## Classification System Timeline

- **1947-1962**: Pre-SIC / 1957 SIC — Ad hoc codes
- **1963-1966**: SIC 1957 — 367 detailed industries
- **1967-1971**: SIC 1967 — 484 industries, first Make/Use
- **1972-1976**: SIC 1972 — 496 industries, first total requirements
- **1977-1986**: SIC 1977 — 537 industries (peak SIC detail)
- **1987-1996**: SIC 1987 — 498 industries, final SIC era
- **1997-2001**: NAICS 1997 — CRITICAL BREAK from SIC
- **2002-2006**: NAICS 2002 — Minor NAICS revision
- **2007-2011**: NAICS 2007 — Supply/Use + import split begins
- **2012-2016**: NAICS 2012 — Tech sector updates
- **2017-2021**: NAICS 2017 — Retail/wholesale updates
- **2022-present**: NAICS 2022 — Most recent

## Methodological Regime Breaks

- **1996** [HIGH]: Chain-weighting — Fixed-weight to chain-type Fisher indexes for real measures. Real tables become non-additive.
- **1997** [CRITICAL]: SIC to NAICS — Complete industry reclassification. Services reorganized. New 'Information' sector created. Manufact
- **2003** [HIGH]: FISIM allocation — Financial intermediation services allocated to user industries instead of single dummy sector.
- **2004** [MEDIUM]: GDP-by-Industry integration — Annual GDP-by-Industry now consistent with I-O accounts.
- **2007** [HIGH]: Supply/Use + Import split — Adopted SNA 2008 Supply/Use terminology. Published separate domestic vs import Use tables.
- **2010** [MEDIUM]: Annual I-O tables begin — First continuous annual I-O data (71 categories, 1997+). Benchmarks integrated with annual accounts.

## Annual Multiplier Statistics (71-sector, 1997-2024)

| Year | Mean | Median | Std | Min | Max |
|------|------|--------|-----|-----|-----|
| 1997 | 1.9313 | 1.8338 | 0.3638 | 1.1876 | 2.7984 |
| 1998 | 1.9277 | 1.8718 | 0.3611 | 1.1974 | 2.7272 |
| 1999 | 1.9368 | 1.8880 | 0.3468 | 1.1909 | 2.7553 |
| 2000 | 1.9772 | 1.9665 | 0.3619 | 1.1948 | 2.7512 |
| 2001 | 1.9254 | 1.8436 | 0.3453 | 1.1866 | 2.7213 |
| 2002 | 1.9010 | 1.8214 | 0.3368 | 1.1805 | 2.6952 |
| 2003 | 1.9080 | 1.8675 | 0.3314 | 1.1909 | 2.6363 |
| 2004 | 1.9273 | 1.8517 | 0.3380 | 1.1522 | 2.7259 |
| 2005 | 1.9699 | 1.8952 | 0.3593 | 1.1987 | 2.8219 |
| 2006 | 1.9693 | 1.8872 | 0.3588 | 1.1994 | 2.8278 |
| 2007 | 1.9880 | 1.8433 | 0.3733 | 1.2026 | 2.9051 |
| 2008 | 2.0209 | 1.9008 | 0.4167 | 1.1725 | 3.1836 |
| 2009 | 1.8903 | 1.7801 | 0.3657 | 1.1454 | 3.1068 |
| 2010 | 1.9370 | 1.8129 | 0.3714 | 1.1711 | 2.9787 |
| 2011 | 1.9903 | 1.8883 | 0.4030 | 1.1716 | 3.0258 |
| 2012 | 1.9788 | 1.9045 | 0.3909 | 1.1816 | 2.9671 |
| 2013 | 1.9797 | 1.8660 | 0.3825 | 1.1976 | 2.9713 |
| 2014 | 1.9937 | 1.8816 | 0.3831 | 1.1965 | 2.9920 |
| 2015 | 1.9331 | 1.8429 | 0.3618 | 1.1990 | 2.8975 |
| 2016 | 1.9135 | 1.8353 | 0.3546 | 1.2063 | 2.8226 |
| 2017 | 1.9211 | 1.8347 | 0.3511 | 1.2120 | 2.7743 |
| 2018 | 1.9407 | 1.8677 | 0.3529 | 1.2032 | 2.8257 |
| 2019 | 1.9211 | 1.8604 | 0.3442 | 1.1927 | 2.7880 |
| 2020 | 1.8802 | 1.8218 | 0.3345 | 1.2025 | 2.7357 |
| 2021 | 1.9091 | 1.8642 | 0.3369 | 1.2028 | 2.9140 |
| 2022 | 1.9335 | 1.8722 | 0.3389 | 1.1829 | 2.8613 |
| 2023 | 1.8857 | 1.8097 | 0.3295 | 1.1776 | 2.8061 |
| 2024 | 1.8720 | 1.7931 | 0.3314 | 1.1670 | 2.7737 |

## Annual Sector Consistency Check

All 28 years use identical 71-sector classification.

## Data Availability in Leontief.io

| Benchmark | Data? | Files |
|-----------|-------|-------|
| 1947 | No | — |
| 1958 | No | — |
| 1963 | No | — |
| 1967 | No | — |
| 1972 | No | — |
| 1977 | No | — |
| 1982 | No | — |
| 1987 | Yes | TBL5-87A.DAT, TBL5-87B.DAT, TBL9-87.DAT... |
| 1992 | No | — |
| 1997 | Yes | IxI_Summary_1997.xlsx, Make_SUT_Framework_1997.xlsx, Use_SUT_Framework_1997.xlsx |
| 2002 | Yes | IxI_Summary_2002.xlsx, Make_SUT_Framework_2002.xlsx, Use_SUT_Framework_2002.xlsx... |
| 2007 | No | — |
| 2012 | No | — |
| 2017 | No | — |
