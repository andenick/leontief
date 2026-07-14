---
title: Prices, Value, and Distribution
order: 9
summary: The dual of the quantity model — how input-output analysis traces cost-push price formation, embeds supply-chain labor, and illuminates the division between wages and profits.
---

## The Other Side of the Mirror

Every tutorial so far has asked a demand-side question: if final demand for sector $j$ rises by a dollar, how much total output does the economy need to produce? That question runs *forward* through the production network, from consumers back to raw material suppliers.

Input-output analysis has an equally powerful mirror image. Flip the question around: if wages rise in any sector, how does that cost push *forward* through every product that sector supplies to other industries? The answer is the **cost-push price model** — the [dual](/glossary#cost-push-price-model) of the quantity model, and the entry point for thinking seriously about distribution between wages and profits. [cite:pasinetti_1981]

## The Price Equation

Let $p$ be a row vector of output prices (one per sector) and $v$ a row vector of **value-added coefficients** — the amount of wages, profits, and taxes paid per dollar of output in each sector. The cost-of-production identity says:

$$p = pA + v$$

Read this right to left: the price of a good equals the cost of all its intermediate inputs ($pA$) plus the primary inputs — labor and capital — that are hired directly ($v$). Solving for $p$:

$$p = v(I - A)^{-1} = vL$$

where $L = (I-A)^{-1}$ is the familiar [Leontief inverse](/glossary#leontief-inverse). The same matrix that solves the quantity system also solves the price system — just applied to value-added coefficients instead of final demand. [cite:miller_blair_2009_ch2]

**What this means in plain English.** The price of a car embeds not just the auto assembler's wages, but also the wages of steel workers, the wages of iron miners, and the wages of the coal miners who supplied energy to the blast furnace. The Leontief inverse unravels every layer of the supply chain and adds them all up. Prices, in this framework, are *vertically integrated cost structures* made visible.

### Reading the price equation

If value-added coefficients change — say wages rise across the board — the price impact propagates in proportion to the total labor and capital content of each good. Goods made with many intermediate inputs (long supply chains) absorb cost increases from every tier; goods produced mostly with primary inputs (short supply chains) feel mainly their own wage bill. The price model makes these asymmetries quantitative.

## Vertically Integrated Labor

Leontief's framework lets us go further than prices. Suppose we replace $v$ with a vector $\ell$ of **direct labor coefficients** — the number of worker-hours (or dollars of compensation) needed per dollar of output in each sector. Then:

$$\hat{\ell} = \ell L = \ell(I - A)^{-1}$$

Each element $\hat{\ell}_j$ is the **vertically integrated labor coefficient** for sector $j$: the total hours of labor — direct in that sector *plus* all the indirect labor embodied in its intermediate inputs — required to deliver one dollar of sector $j$'s output to final demand. [cite:pasinetti_1981]

Luigi Pasinetti called this concept central to understanding economic growth precisely because it strips away the circularity of prices: instead of measuring an industry's "size" in dollars (which conflates quantity and price), you measure it in the fundamental unit of production time. An industry that looks small in dollar terms may embody enormous amounts of labor spread across a long supply chain.

The formula is identical to the **Marxian labor value** — the total socially necessary labor embodied in a commodity:

$$\lambda = \ell(I - A)^{-1}$$

This is not a coincidence. Leontief and Karl Marx were asking the same empirical question — how much labor, direct and indirect, does production require? — even if they drew different political conclusions from the answer. [cite:shaikh_capitalism_2016]

## Distribution: Wages and Profits in I-O

Once you can compute the total labor content of output, the division of income between workers and capital owners becomes measurable. In the BEA value-added rows (the VA matrix Leontief publishes for each year), the key split is:

- **Compensation of employees** ($w_j$) — wages, salaries, and employer contributions
- **Gross operating surplus** — profits, proprietors' income, and capital consumption

The **wage share** in sector $j$ is simply $w_j / x_j$ (compensation per dollar of output). Aggregated across all sectors, it tracks how labor's slice of national income has moved over time.

{{chart:structural_trend:labor_share}}

The trend line matters. When the wage share falls, more of each dollar of output flows to profit and capital income. The Leontief framework lets you trace this: a falling wage share means that $v_{\text{wages}}$ is shrinking relative to $v_{\text{profits}}$ in the value-added vector, and the full price equation tells you which industries and supply chains are most exposed to that shift.

## Financialization: A Structural Signature

One of the most striking structural changes in the U.S. economy over Leontief's 28-year window is the growing weight of finance in intermediate production. Finance, insurance, and real estate sectors are not just final services purchased by households — they are intermediate inputs bought by every other industry: manufacturers pay interest on working capital, retailers pay insurance premiums, construction firms pay real estate fees.

{{chart:structural_trend:financialization}}

When the financial sector's share of intermediate inputs rises, it reshapes the price equation: a larger fraction of every product's cost is now financial cost rather than wage or materials cost. The Godley–Lavoie sectoral balance framework, which maps I-O value-added flows onto financial claims between the household, business, government, and foreign sectors, makes this accounting precise. [cite:godley_lavoie_2007]

## Try It

```python
import pandas as pd
import numpy as np

# Load L and VA matrices for a chosen year (CSV download from /data)
L  = pd.read_csv("L_2019.csv", index_col=0)
va = pd.read_csv("VA_2019.csv", index_col=0)

# Row V001 = compensation of employees
wages = va.loc["V001"]          # Series: wages per sector
total_output = va.sum()         # proxy for total output from VA rows

# Wage share by sector
wage_share = wages / total_output
print(wage_share.sort_values().tail(10))

# Vertically integrated labor (wage) coefficients
w_vec = (wages / total_output).values          # direct wage coefficient vector
v_integrated = w_vec @ L.values               # total wage content per $ of output
print(pd.Series(v_integrated, index=L.columns).sort_values().tail(10))
```

## Where Next

The price and distribution framework sets the stage for thinking about *change over time*. Tutorial 10 — [Vintages and Pitfalls](/learn/10-vintages-and-pitfalls) — shows how to navigate Leontief's 28 annual tables responsibly: which years are directly comparable, where the methodological breaks are, and how to download the data. For deeper empirical work on wages, profits, and prices across industries, see [/studies/prices-and-distribution](/studies/prices-and-distribution).

## Further reading

- Miller &amp; Blair (2009), §2.6 — the Leontief price (cost-push) model, the dual of the quantity model. [cite:miller_blair_2009_ch2]
- Pasinetti (1981), *Structural Change and Economic Growth* — vertically integrated labor coefficients. [cite:pasinetti_1981]
- Shaikh (2016), *Capitalism: Competition, Conflict, Crises* — the labor-value reading of the I-O system. [cite:shaikh_capitalism_2016]
