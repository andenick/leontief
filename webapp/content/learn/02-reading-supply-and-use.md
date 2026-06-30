---
title: Reading Supply and Use Tables
order: 2
summary: BEA builds U.S. input-output accounts from two interlocking tables — a Supply (Make) table and a Use table — that together enforce tight accounting identities across all 71 sectors.
---

## Why two tables?

In the real economy, a single industry can produce multiple commodities, and a single commodity can be produced by multiple industries. A chemical plant may supply both industrial gases *and* plastics. A logging company produces both timber *and* wood chips. Lumping all of this into one square matrix would hide these secondary-product flows.

BEA's solution — standard across modern national accounting systems [cite:bea_concepts_2009][cite:un_handbook_2018] — is to track production and consumption in two separate rectangular tables before deriving the symmetric industry-by-industry matrices used for I-O analysis.

---

## The Supply (Make) table

The **Supply table** (sometimes called the Make table) records how much of each commodity each industry produces. Rows are **industries**; columns are **commodities**. The large entries run along the diagonal — each industry primarily produces its "own" commodity — but off-diagonal entries capture secondary products.

For example, the Agriculture industry primarily supplies Farm Products, but it also supplies small amounts of Food & Beverages (on-farm processing) and even Paper Products (wood lots). The Supply table makes these secondary flows explicit rather than pretending each industry is a pure mono-product producer.

In the 2024 BEA data the Supply table has 74 rows (industries + government and rest-of-world rows) and 83 columns (commodity groups), before aggregation to the 71 BEA Summary sectors.

---

## The Use table

The **Use table** records intermediate and final consumption. Rows are **commodities**; columns are **industries** (intermediate use) plus **final demand categories** (personal consumption, investment, exports, imports, government). Each cell $u_{ij}$ says: "commodity $i$ was used by industry $j$ in this amount."

The 2024 BEA Use table has 79 rows and 92 columns before aggregation. The extra columns beyond the 71 industries contain the final demand categories — the destination of output that never re-enters the production process.

### The accounting identity

For every industry $j$, total inputs equal total output:

$$\underbrace{\sum_i u_{ij}}_{\text{intermediate inputs}} + \underbrace{VA_j}_{\text{value added}} = x_j = \underbrace{\sum_i s_{ji}}_{\text{supply (Make row)}}$$

The column sum of intermediate inputs plus value added must equal the row sum of the industry's supply contributions. This identity is what forces the two tables to balance — it is the national accounts equivalent of double-entry bookkeeping [cite:bea_concepts_2009].

---

## Value added: what's left after buying inputs

After paying for all intermediate commodities (energy, materials, services bought from other industries), what remains is **value added** — the contribution of labor and capital within that industry. BEA reports four value-added rows in the VA matrix:

| Code | Meaning |
|---|---|
| **V001** | Compensation of employees (wages + salaries + benefits) |
| **V003** | Taxes on production and imports, less subsidies |
| **VABAS** | Value added at basic prices (= V001 + V003 + gross operating surplus) |
| **VAPRO** | Value added at producer prices |

**V001 (compensation)** is the largest row in almost every industry: it captures all labor income, including employer-paid health insurance and pension contributions. **Gross operating surplus** — the difference between VABAS and (V001 + V003) — is the residual that accrues to capital owners: profits, depreciation, and proprietors' income.

The interactive table below shows 2024 value-added by sector, aggregated to 15 groups. Look at the compensation row for sectors like Health Care and Education — labor-intensive industries where V001 dwarfs every other cost category.

{{table:2024/VA?agg=15}}

---

## Final demand: where output goes

The right-hand columns of the Use table record **final demand** — output that leaves the production circuit entirely. The BEA F-codes group these into:

| Code | Category | Sign convention |
|---|---|---|
| **F010** | Personal Consumption Expenditures (PCE) | Positive |
| **F02x** | Gross Private Domestic Investment (GPDI) | Positive |
| **F04x** | Exports of goods and services | Positive |
| **F05x** | Imports of goods and services | **Negative** |
| **F06–F10x** | Federal and State/Local government spending | Positive |

Imports appear with a **negative sign** because they add to available supply without being domestically produced. Treating imports as negative final demand keeps the accounting identity intact: total uses (intermediate + final) must equal total supply (domestic output + imports).

This sign convention trips up many first-time readers. When you download the FD matrix and see large negative columns for Import rows, that is not an error — it is the correct accounting treatment [cite:un_handbook_2018].

The table below shows the 2024 final demand breakdown aggregated to 15 sector groups. Personal consumption (F010) dominates for most consumer-facing sectors; exports are relatively large for Manufacturing.

{{table:2024/FD?agg=15}}

---

## From Supply and Use to the symmetric I-O table

The raw Supply and Use tables use a commodity-by-industry layout that is not square — you cannot invert a non-square matrix. To get the Leontief inverse $L = (I - A)^{-1}$ we need a square, industry-by-industry table.

BEA applies an **industry-technology assumption**: each industry uses inputs in fixed proportions regardless of which commodity it produces. Under this assumption, the direct requirements matrix becomes:

$$A = U \hat{V}^{-1} (V \hat{q}^{-1})^{-1}$$

where $U$ is the Use matrix (commodities × industries), $V$ is the Make/Supply matrix (industries × commodities), and $\hat{q}$ is the diagonal of commodity totals [cite:miller_blair_2022]. The result is the symmetric $A_{IxI}$ (industry-by-industry) matrix that underlies the L matrix you saw in Tutorial 1.

A critical methodological note: before 2007, BEA published only a single Use table mixing domestic and imported inputs. From the 2007 benchmark onward, BEA publishes **separate** domestic and import Use tables. Multipliers computed from the total-use table overstate domestic production effects because they include import leakage. The Leontief database uses the **total** Use table for the full 1997–2024 span to maintain consistency; keep this in mind when comparing multipliers across time [cite:bea_concepts_2009].

---

## Try it: inspect value added as a share of output

```python
import pandas as pd

# Download from the Leontief API
VA = pd.read_csv("2024_VA.csv", index_col=0)  # rows: V001, V003, VABAS, VAPRO
L  = pd.read_csv("2024_L.csv",  index_col=0)

# Compensation share: V001 / total output (diagonal of L scaled by f=1)
# Use VABAS row as proxy for output (value added + intermediate = total output
# requires the Use table, but VABAS gives the pure value-added component)
comp_share = VA.loc["V001"] / VA.loc["VABAS"]
print(comp_share.sort_values(ascending=False).head(10))
```

---

## The 2003 FISIM shift: a quiet structural break

One regime change that quietly reshapes the A matrix: in 2003 BEA began allocating **FISIM** (Financial Intermediation Services Indirectly Measured — the imputed margin banks charge for loans) from a single dummy sector to the actual industries that borrow. Post-2003, every industry that uses bank credit shows higher financial-services intermediate inputs than pre-2003 data would suggest. When comparing A matrices across the 1997–2024 span, this shift can make the banking sector appear to have grown its backward linkages discontinuously [cite:bea_concepts_2009].

{{chart:structural_trend:financialization}}

---

## Where next

- **Next tutorial**: [Multipliers and Linkages](/learn/03-multipliers-and-linkages) — how to read output, income, and employment multipliers from the Leontief inverse, and what "key sector" status really means.
- **Dig into the data**: [Multipliers Explained](/studies/multipliers-explained) — a worked study tracing how the mean output multiplier fell from 1.93 in 1997 to 1.87 in 2024, and which sectors drove the change.
