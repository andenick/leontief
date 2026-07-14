---
title: "Which Government Spending Creates the Most Output?"
order: 8
difficulty: advanced
summary: "Using the 2024 Leontief inverse and the BEA final-demand matrix, we compute an output multiplier for each of the twelve government spending categories: normalize the category's sectoral spending vector to one dollar and sum the induced economy-wide output (L·f_unit). Defense equipment and nondefense equipment top the rankings at 2.19 and 2.59 respectively; consumption-heavy categories cluster near 1.55–1.74."
---

## The Question

Government spending is not monolithic. Federal defense spending on weapons systems flows into a different set of industrial sectors than state and local spending on school construction or federal nondefense spending on social services. Because each spending pattern triggers a different chain of intermediate-goods purchases through the Leontief inverse, different categories of government spending have different macroeconomic multipliers — even if their dollar totals are the same.[cite:miller_blair_2009_ch6]

This study quantifies those differences for 2024 using the BEA's official twelve government final-demand columns and the 71-sector Leontief inverse.

---

## The Method

### Government Final-Demand Categories

The BEA final-demand (FD) matrix for 2024 contains twelve government columns, grouped into three agencies and four spending types:

| Agency | Consumption | Equipment | Structures | Software/IP |
|---|---|---|---|---|
| Federal defense | F06C | F06E | F06N | F06S |
| Federal nondefense | F07C | F07E | F07N | F07S |
| State & local | F10C | F10E | F10N | F10S |

These codes are taken directly from `site_data/sectors.json` (`fd_cols` field), which documents the BEA Use-table column scheme.[cite:godley_lavoie_2007]

### Computing the Output Multiplier

For each category $c$ with spending vector $f_c$ (sector allocations in millions of dollars), we define:

$$f_c^{\text{unit}} = \frac{f_c}{\sum_i f_{c,i}}$$

This normalizes total spending to exactly $1. The **output multiplier** is then:

$$m_c = \mathbf{1}' \cdot L \cdot f_c^{\text{unit}} = \sum_i (L\, f_c^{\text{unit}})_i$$

This answers: *For every dollar spent by the government in category $c$, how many dollars of total gross output — across all 71 sectors — are induced, including the direct sector plus all upstream intermediate-goods chains?*

Because $L$ already embeds every round of indirect effects (Sector A buys from B which buys from C…), no additional "rounds" calculation is needed. The multiplier is exact for the BEA's intermediate-goods network and is the same Type I multiplier (without income endogenization) used in the output-multiplier studies of Miller & Blair (2022, Ch. 6).

### Alignment

The BEA FD table has 70 sector rows; $L$ has 71. Three sectors present in $L$ are absent from the FD table: `441` (Motor vehicle and parts dealers), `445` (Food and beverage stores), and `452` (General merchandise stores). These retail detail sectors receive $f = 0$ across all government categories — they have no row in the BEA FD table and receive no direct government final demand. Two FD rows (`Other`, `Used`) have no counterpart in $L$ and are excluded from the multiplier calculation. Net working intersection: 68 sectors. The 3 missing retail sectors are included in the $L$ matrix used for multiplication; since their $f = 0$, they contribute through $L$'s off-diagonal elements only (their upstream suppliers still count) but receive no direct government allocation.

---

## What the Data Show

{{chart:study:fiscal-multipliers:fiscal_mult}}

### Individual Category Multipliers (2024)

| Spending category | Output multiplier | 2024 spending ($B) |
|---|---|---|
| Federal nondefense — equipment (F07E) | **2.592** | 25.1 |
| State & local — equipment (F10E) | **2.584** | 83.5 |
| Federal defense — equipment (F06E) | **2.186** | 108.6 |
| Federal nondefense — software/IP (F07S) | 1.904 | 19.2 |
| State & local — software/IP (F10S) | 1.904 | 463.9 |
| Federal defense — software/IP (F06S) | 1.904 | 17.1 |
| Federal defense — consumption (F06C) | 1.737 | 854.8 |
| State & local — consumption (F10C) | 1.728 | 2,550.4 |
| Federal defense — structures (F06N) | 1.578 | 102.3 |
| State & local — structures (F10N) | 1.570 | 73.9 |
| Federal nondefense — structures (F07N) | 1.566 | 178.6 |
| Federal nondefense — consumption (F07C) | 1.545 | 586.7 |

### Aggregate Category Multipliers

Summing across all four sub-types per agency:

| Aggregate category | Output multiplier | 2024 total spending ($B) |
|---|---|---|
| State & local government | 1.773 | 3,165.8 |
| Federal defense | 1.770 | 1,082.7 |
| Federal nondefense | 1.591 | 810.7 |

### Why Equipment Spending Leads

The equipment categories (F06E, F07E, F10E) achieve multipliers of 2.19–2.59 because their spending vectors are heavily concentrated in manufacturing sectors with deep intermediate-goods supply chains. The 2024 BEA defense-equipment vector (F06E) has large allocations to `3361MV` (Motor vehicles — $42.3B), `3364OT` (Other transportation equipment, including aircraft — $39.9B), `334` (Computer and electronic products — $21.8B), and `333` (Machinery — $2.5B). These are sectors near the top of the Rasmussen backward-linkage ranking; each dollar they receive fans out through steel, aluminum, semiconductors, chemicals, and logistics.

The consumption categories (F06C, F07C, F10C) each have a single dominant sector — `GFGD` (Federal general government — defense) absorbs all of defense consumption, `GFGN` takes all of nondefense consumption, and `GSLG` takes all of state-and-local consumption. These government output rows in $L$ have lower average column sums than goods-producing sectors, so their multipliers are lower.

Software/IP spending (F06S, F07S, F10S) is concentrated in construction (`23`) and produces identical multipliers across agency categories (1.904) because the sector allocation pattern is the same.

### Clean-Input Caveat

All calculations use the **square 71×71 Leontief inverse** from the BEA pipeline, not the raw 70×71 A matrix. The three missing retail sectors (441, 445, 452) are explicitly set to $f = 0$ — they are not silently dropped from $L$, so their upstream-supplier effects remain active. The FD rows `Other` and `Used` (bookkeeping rows in the BEA Use table) are excluded from $f_c$ with no loss of economic content.[cite:miller_blair_2009_ch6]

---

## The Takeaway

The ranking is not politically obvious: federal *defense* spending on equipment produces a larger multiplier (2.19) than federal *nondefense* consumption (1.55) because the equipment purchase pattern is tilted toward high-multiplier manufacturing sectors. State and local spending, dominated by consumption of government services ($2.55 trillion in F10C), has a higher aggregate multiplier (1.77) than federal nondefense (1.59) primarily because of state-and-local equipment and software allocations.

The policy implication depends on what question you are asking. If the goal is maximum short-run output amplification, equipment-intensive government spending dominates. If the goal is service delivery (health care, education, social programs), the sectoral composition necessarily shifts toward lower-multiplier sectors — and comparing multipliers across categories with different social purposes is a category error. The I-O model is neutral on that normative question; it simply maps each spending pattern to its gross-output implications.[cite:godley_lavoie_2007]

---

## Reproduce This

Download the full replication bundle at:

**[/api/study/fiscal-multipliers/bundle.zip](/api/study/fiscal-multipliers/bundle.zip)**

```bash
unzip leontief_study_fiscal-multipliers.zip
cd code
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/fiscal.csv, outputs/fig_fiscal_mult.json
```

The script reads `data/L_2024.csv`, `data/fd_2024.csv`, `data/fd_cols.csv`, and `data/sector_names.csv`. It uses only pandas and NumPy (no networkx, no scipy). The alignment of FD rows to L's index is performed explicitly and logged to stdout on every run. An `analysis.ipynb` notebook mirrors every step.

[cite:miller_blair_2009_ch6][cite:godley_lavoie_2007]
