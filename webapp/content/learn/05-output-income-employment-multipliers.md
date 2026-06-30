---
title: "Output, Income, and Employment Multipliers"
order: 5
summary: "The Leontief inverse delivers more than a solution to an equation — its column sums measure how much total economic activity a dollar of final demand triggers, and scaled versions trace income and employment ripples across all 71 sectors."
---

## From the Inverse to a Number the Economy Can Feel

By this point in the tutorial series you have seen how the [Leontief inverse](/glossary#leontief-inverse) $L = (I - A)^{-1}$ captures the full cascade of upstream production needs. But L is a 71×71 matrix — dense and hard to read at a glance. Multiplier analysis compresses that information into a single number per sector: how much total output does the economy generate when final demand for sector $j$ rises by one dollar?

That number is the **output multiplier**, and it lives, already computed, in the columns of L.

---

## The Output Multiplier

Each element $l_{ij}$ of L tells you how much output sector $i$ must produce — directly and through every supply-chain round — to support one additional dollar of sector $j$'s final output. Summing over all sectors $i$ in that column gives the *economy-wide* total:

$$m_j = \sum_{i=1}^{n} l_{ij}$$

This is the **Type I output multiplier** for sector $j$. If $m_j = 1.82$, then a $1 billion increase in final demand for sector $j$ generates $1.82 billion of total output across all 71 sectors — $1 billion in sector $j$ itself plus $0.82 billion spread through its suppliers and their suppliers.

The minimum possible value is 1 (a sector with no intermediate inputs at all; the diagonal element $l_{jj}$ is always at least 1). The maximum in the Leontief dataset over 1997–2024 peaked at about 3.18 in 2008, for the most deeply embedded manufacturing industries.[cite:miller_blair_2022]

{{chart:multiplier_bar?year=2024}}

The 2024 cross-section above makes the dispersion concrete: the economy-wide mean output multiplier is 1.87, with a standard deviation of 0.33 and a range from roughly 1.17 (some service sectors with few intermediate inputs) to 2.77 (industries with long, dense supply chains). High-multiplier sectors are generally those that pull heavily from domestic intermediates — manufacturing, energy, construction.

{{chart:multiplier_trend}}

Tracking the mean multiplier over the 28-year coverage reveals a mild secular compression. The average stood at 1.93 in 1997, climbed to 2.02 in 2008, then fell back to 1.87 in 2024. Part of this reflects structural change in the U.S. economy toward services (which tend to have lower multipliers) and increased import penetration (imported intermediates leak out of the domestic multiplier circuit).

---

## Income Multipliers: Scaling by Value Added

The output multiplier measures gross production. If you care about household income rather than gross output, you need to scale each column of L by **value-added coefficients** — how many cents of labor compensation are generated per dollar of output in each sector.

Let $\mathbf{v}$ be the row vector of compensation-per-dollar-of-output coefficients, one entry per sector (derived from the BEA [VA matrix](/glossary#value-added), code V001). The **income multiplier** for sector $j$ is:

$$m_j^v = \sum_{i=1}^{n} v_i \, l_{ij} = (\mathbf{v} \, L)_j$$

In matrix form, $\mathbf{v} L$ is a row vector of income multipliers for all sectors simultaneously. The interpretation: $m_j^v$ dollars of employee compensation are generated economy-wide per dollar of final demand for sector $j$, accounting for every supply-chain round.[cite:miller_blair_2022]

**Employment multipliers** work identically, substituting an employment coefficient $e_i$ (jobs per dollar of output in sector $i$) for $v_i$:

$$m_j^e = \sum_{i=1}^{n} e_i \, l_{ij}$$

Employment multipliers are especially useful for policy analysis: how many total jobs does a stimulus program in sector $j$ support, counting both the direct hires and the workers employed by suppliers all the way up the chain?

---

## Type I vs. Type II: Closing the Model on Households

All the multipliers above are **Type I** — computed from the standard open model where households appear only as a final demand column and a value-added row. The model treats household consumption as an exogenous pull on the economy.

**Type II multipliers** go a step further by *closing the model with respect to households*: household consumption of goods and services is treated as an endogenous intermediate demand, and household labor income is treated as an endogenous supply of the "household sector." This is done by augmenting A with an extra row (the [income multiplier](/glossary#multiplier-output--income--employment) vector $\mathbf{v}$, capturing how much income households earn per dollar of each sector's output) and an extra column (the household consumption bundle, normalized per dollar of income):

$$\bar{A} = \begin{bmatrix} A & \mathbf{h}_c \\ \mathbf{v} & 0 \end{bmatrix}$$

where $\mathbf{h}_c$ is the column vector of consumption coefficients. The augmented Leontief inverse $\bar{L} = (I - \bar{A})^{-1}$ then contains an additional **induced** consumption effect: when sector $j$ expands, it pays workers, who spend on consumption goods, which generates further output, which pays further workers, and so on.

Type II multipliers are uniformly larger than Type I multipliers. The gap between them reflects the strength of the induced consumption channel. Whether to use Type I or Type II depends on the question:

| Question | Preferred multiplier |
|---|---|
| Short-run output impact of a procurement shock | Type I |
| Long-run employment effect of a regional investment | Type II |
| Comparison across sectors (relative ranking) | Either — rankings are usually stable |
| Policy advocacy (e.g., stimulus justification) | Type II, with caveats about circularity |

Type II multipliers require an assumption that household spending patterns are stable and proportional to income — an assumption more defensible in the long run.[cite:miller_blair_2022]

---

## Try It

Download the 2024 L matrix (CSV) from the Leontief data page and compute Type I output multipliers yourself:

```python
import pandas as pd

# Load the 2024 Leontief inverse (71x71, rows and cols are sector labels)
L = pd.read_csv("2024_L.csv", index_col=0)

# Output multiplier for each sector = column sum of L
output_multipliers = L.sum(axis=0)

# Five highest-multiplier sectors in 2024
print(output_multipliers.nlargest(5))

# Economy-wide mean (should be ~1.87 for 2024)
print(f"Mean multiplier: {output_multipliers.mean():.4f}")
```

The column sum is literally the operation $\sum_i l_{ij}$ — no extra steps needed.

---

## Where Next

**Next tutorial:** [Tutorial 06 — Linkages and Key Sectors](/learn/06-linkages-and-key-sectors) takes the multiplier logic one step further by asking which sectors are strategically central to the whole economy — pulling from many suppliers *and* supplying to many industries at once.

**Go deeper:** See the [Multipliers study](/studies/multipliers-explained) for a worked numerical example with 2024 BEA data, including a breakdown of how the 2008 financial crisis shifted the distribution of multipliers across the 71-sector table.
