---
title: "How COVID Bent the Input-Output Structure"
order: 5
difficulty: intermediate
summary: "The pandemic reallocated spending across industries at a pace not seen in the post-war data. Structural-change metrics computed from successive BEA input-output tables reveal a 2019→2020 disruption roughly 1.8 times larger than a typical year — and a 2020→2021 partial reversal that is itself larger than most normal years."
---

## The Question

When an economy absorbs a shock, it does not contract uniformly. Some industries collapse (air transport, accommodation), others surge (online retail, health equipment), and the intermediate-goods network that links them reweights accordingly. How do we measure that reweighting precisely, and how unusual was the COVID-19 disruption?

Input-output tables give us a rigorous answer. Each year's A-matrix — the matrix of technical coefficients — encodes the economy's intermediate-production technology: how many cents of sector $i$'s output are needed to produce one dollar of sector $j$'s output. When the structural composition of the economy shifts, those coefficients shift too. Comparing successive A-matrices produces a direct measure of structural distance.[cite:bea_concepts_2009]

---

## Three Measures of Structural Change

We track three complementary metrics for each consecutive-year pair from 1997–1998 through 2023–2024.

### 1. Cosine Similarity

Flatten each A-matrix into a vector of $n^2$ coefficients. The cosine similarity between years $t$ and $t+1$ is:

$$\text{cos}(A_t, A_{t+1}) = \frac{\text{vec}(A_t) \cdot \text{vec}(A_{t+1})}{\|\text{vec}(A_t)\|\,\|\text{vec}(A_{t+1})\|}$$

Values near 1 indicate a nearly unchanged structure; departures from 1 signal reallocation. The structural distance is then $d_t = 1 - \text{cos}(A_t, A_{t+1})$.[cite:dietzenbacher_los_1998]

### 2. Mean Absolute Change

A simpler but complementary metric: the element-wise mean absolute difference between matrices,

$$\bar{d}_t = \frac{1}{n^2} \sum_{i,j} |a_{ij,t+1} - a_{ij,t}|$$

This measure is scale-free and intuitively interpretable: it tells you the average change in the fraction of output devoted to any given input pair.

### 3. Lilien Index

Adapted from labor-market dispersion analysis, the Lilien index measures the cross-industry dispersion of output growth:

$$L_t = \sqrt{\sum_i s_{it}\left(\ln\frac{x_{it+1}}{x_{it}} - \ln\frac{X_{t+1}}{X_t}\right)^2}$$

where $s_{it}$ is sector $i$'s output share and $X_t$ is total output. A high Lilien index signals that some sectors grew much faster than the aggregate while others contracted — the signature of structural reallocation rather than uniform expansion or contraction.

---

## What the Data Show

The chart below plots all three metrics for each year-pair from 1997 to 2024. The 2019→2020 and 2020→2021 transitions are highlighted.

{{chart:study:covid-structural-shift:covid_shift}}

### The 2019→2020 Shock

For the 2019→2020 transition, the three metrics are:

| Metric | Value | Typical-year mean | COVID/typical ratio |
|---|---|---|---|
| Structural distance (1 − cosine) | 0.0100 | 0.0055 | **1.82×** |
| Mean absolute change | 0.00188 | 0.00132 | **1.42×** |
| Lilien index | 0.149 | 0.095 | **1.57×** |

The structural distance of 0.010 is **1.82 times** the typical year's distance of 0.0055. By any of the three measures, 2019→2020 registers as one of the two largest single-year structural dislocations in the 1997–2024 window — the other being the 2008→2009 Great Financial Crisis, which produced a structural distance of 0.0155 (1.55 times the COVID shift, but in the same league).

### The 2020→2021 Rebound

The reversal is almost as striking. The 2020→2021 transition produces a structural distance of 0.0076 and a Lilien index of 0.114 — still **1.38× and 1.20×** above the typical year respectively. The economy did not simply snap back to its 2019 structure; it reorganized again as pandemic-era spending patterns partially unwound and supply-chain bottlenecks created new distortions.

The net result: the pandemic carved a two-year detour through the input-output structure. The 2021→2022 and subsequent transitions are closer to normal (distances of 0.0038 and 0.0040), suggesting the economy returned to a stable structural path by 2022 — though not necessarily the same path it had been on before 2020.

### Which Sectors Moved Most?

The `covid_structural_shift.xlsx` workbook (exported here as `covid_sector_shift.csv`) records, for each of the 68 commodity sectors, the absolute change in the row of A (the sector's role as *seller of inputs*), the change in the column (its role as *buyer of inputs*), and the total.

The top sectors by total structural displacement in 2019→2020:

| Sector | As buyer | As seller | Total shift |
|---|---|---|---|
| Petroleum & coal products (324) | 0.00122 | 0.01027 | **0.01150** |
| Other real estate (ORE) | 0.00340 | 0.00615 | 0.00955 |
| Air transportation (481) | 0.00565 | 0.00320 | 0.00885 |
| Management of companies (55) | 0.00179 | 0.00697 | 0.00876 |
| Rental & leasing (532RL) | 0.00158 | 0.00553 | 0.00710 |

Petroleum & coal tops the list primarily as a *seller*: oil prices collapsed in early 2020, compressing the energy-cost share of every downstream industry simultaneously. Air transportation's displacement reflects the near-total collapse in travel demand. Real estate and financial management moved as pandemic-era fiscal intervention reshaped investment flows.

---

## The Takeaway

Structural-change metrics built from consecutive I-O tables translate macroeconomic disruption into a precise geometric language: how far did the economy's production-technology vector move in one year? COVID-19 moved it roughly 1.8 times farther than a typical year — and the recovery year moved it 1.4 times farther than normal before the economy settled. That is not a uniform recession; it is a reallocation shock of historic magnitude, visible directly in the technical-coefficient matrix that encodes how industries depend on one another.

The Great Financial Crisis of 2008–2009 produced the largest shift in the sample (structural distance 0.0155), largely through the collapse of financial intermediation. COVID-19 (0.0100) was structurally comparable — driven by a different mechanism (demand collapse concentrated in contact-intensive services, energy price crash) but similarly large relative to any peacetime year.

---

## Reproduce This

Download the full replication bundle — data, code, and notebook — at:

**[/api/study/covid-structural-shift/bundle.zip](/api/study/covid-structural-shift/bundle.zip)**

```bash
unzip covid-structural-shift.zip
cd covid-structural-shift
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/structural_change.csv, outputs/fig_covid_shift.json
```

The script reads `data/structural_change.csv` (year-pair metrics exported from the BEA pipeline) and `data/covid_sector_shift.csv` (sector-level 2019→2020 displacements). It writes a Plotly JSON figure and a summary CSV to `outputs/`. The `analysis.ipynb` notebook mirrors every step for interactive exploration.

[cite:bea_concepts_2009][cite:dietzenbacher_los_1998]
