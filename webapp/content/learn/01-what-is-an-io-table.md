---
title: What Is an Input-Output Table?
order: 1
summary: An input-output table maps every dollar of sales and purchases across all industries simultaneously, turning the economy into an accountable grid.
---

## The economy as a grid

Every industry both buys and sells. A car manufacturer buys steel, electricity, and software; it sells vehicles to households, to the government, and to export markets. An input-output (I-O) table records all of these transactions — for every industry, in the same year, in a single rectangular grid.

Leontief built the first comprehensive table for the U.S. economy in the 1930s [cite:leontief_1936][cite:leontief_1941]. The idea was simple but powerful: if you know *who sells to whom*, you can trace a spending shock — a new highway project, an export boom — as it ripples across the whole economy. Leontief received the 1973 Nobel Prize in Economic Sciences for this framework [cite:leontief_1973].

The Leontief site carries 28 years of annual U.S. I-O data (1997–2024) at the BEA Summary level of **71 sectors** — everything from Farms (sector 1) to Federal Reserve Banks to Computer Systems Design.

---

## The basic structure: a toy example

Imagine a three-sector economy: **Farms**, **Food Processing**, and **Households** (as final buyers). All values are in millions of dollars.

| Selling \ Buying | Food Processing | Households (final demand) | Total output |
|---|---|---|---|
| **Farms** | 60 | 40 | 100 |
| **Food Processing** | 0 | 120 | 120 |
| **Value Added** | 60 | — | — |
| **Total input** | 120 | — | — |

Reading **across a row**: Farms sells \$60m of grain to Food Processing, and \$40m of fresh produce directly to Households. Total farm output = \$100m.

Reading **down a column**: Food Processing buys \$60m from Farms and generates \$60m of value added (wages + profits). Total inputs = \$120m = total output. Columns must balance — every dollar of output came from somewhere.

This double-entry logic holds for all 71 BEA sectors. The table is essentially a national accounting identity expressed as a matrix.

---

## From transactions to "recipes": the A matrix

The raw transactions table $Z$ tells us *how much* each industry bought from each other. But we want to know the technology — the *proportional recipe* each industry uses. We divide each cell by the purchasing industry's total output:

$$a_{ij} = \frac{z_{ij}}{x_j}$$

Here $z_{ij}$ is the dollar flow from sector $i$ to sector $j$, and $x_j$ is sector $j$'s total output. The resulting matrix $A$ is the **direct requirements matrix** ([glossary: direct-requirements](/glossary#direct-requirements)): each column tells you how many cents of each input are needed to produce one dollar of output in that industry.

In the toy example, Food Processing spends \$60m on Farms out of \$120m total output, so $a_{\text{Farms},\text{FoodProc}} = 0.50$. Half of every dollar of processed food comes (directly) from the farm sector.

The live heatmap below shows the A matrix for 2024, aggregated to 15 sectors. Darker cells mean a stronger direct input link. Notice the bright diagonal block for Manufacturing — manufacturers buy heavily from other manufacturers — and the relative sparseness of service sectors, which draw more from labor (value added) than from intermediate goods.

{{chart:heatmap:2024:A_square:15}}

---

## Going deeper: total requirements and the Leontief inverse

Direct requirements miss the cascade. Food Processing buys from Farms; Farms buys tractors from Manufacturing; Manufacturing buys fuel from Petroleum Refining; Petroleum Refining buys from Mining. A demand shock propagates through all these layers simultaneously.

Leontief showed that the total (direct + all indirect) requirements can be computed in one matrix operation. If $f$ is the vector of **final demand** — what households, government, and exporters want — then total output required is:

$$x = (I - A)^{-1} f = L f$$

The matrix $L = (I - A)^{-1}$ is the **Leontief inverse** ([glossary: leontief-inverse](/glossary#leontief-inverse)), also called the **total requirements matrix**. Each entry $l_{ij}$ tells you: *to deliver one additional dollar of final demand for sector $j$, how much total output must sector $i$ produce?*

The power series $L = I + A + A^2 + A^3 + \cdots$ reveals the intuition: the first term is the direct delivery ($I$), the next is the first round of inputs ($A$), then inputs to those inputs ($A^2$), and so on [cite:miller_blair_2009_ch2].

The interactive table below shows the 2024 Leontief inverse $L$, aggregated to 15 sectors. Values on the diagonal are always ≥ 1 (an industry needs at least its own direct output to satisfy demand), and off-diagonal entries capture the cross-sector support each industry provides.

{{table:2024/L?agg=15}}

---

## Multipliers: what the inverse tells us

Sum down a column of $L$ and you get the **output multiplier** for that sector: the total dollars of production required economy-wide for each dollar of final demand delivered by that industry. Across the 71 BEA sectors, these multipliers ranged from **1.17 to 2.77** in 2024 (mean 1.87). They peaked around 2008 (mean 2.02) when energy prices inflated cross-industry costs, and compressed during the 2020 pandemic disruption (mean 1.88).

{{chart:multiplier_bar?year=2024}}

High-multiplier sectors — think Petroleum Refining or Construction — trigger long input chains. Low-multiplier sectors — Real Estate, some Finance — buy relatively little from other industries and instead generate value added almost entirely from labor and capital.

---

## Try it: load a year and compute output multipliers

```python
import pandas as pd

# Download from the Leontief API or export button
L = pd.read_csv("2024_L.csv", index_col=0)

# Output multiplier = column sum of L
multipliers = L.sum(axis=0).rename("output_multiplier")
print(multipliers.sort_values(ascending=False).head(10))
```

---

## Where next

- **Next tutorial**: [Reading Supply and Use Tables](/learn/02-reading-supply-and-use) — how BEA actually constructs the I-O accounts from two separate tables, and what the value-added and final-demand rows contain.
- **Dig into the data**: [Key Sectors: Backward and Forward Linkages](/studies/key-sectors) — which of the 71 BEA sectors sit at the center of the U.S. production network, and how that has shifted from 1997 to 2024.

## Further reading

- Miller &amp; Blair (2009), ch. 2 — the foundations: notation, the transactions table, and the derivation of the Leontief inverse. [cite:miller_blair_2009_ch2]
- Leontief (1986), *Input-Output Economics* — the framework in its originator's own words. [cite:leontief_1986]
- ten Raa (2005), *The Economics of Input-Output Analysis* — a compact, rigorous modern treatment. [cite:ten_raa_2005]
