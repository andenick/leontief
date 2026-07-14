---
title: "Total Requirements: The Leontief Inverse"
order: 4
summary: "Why inverting (I − A) reveals the full economy-wide ripple of any demand shock — and how the power-series intuition shows that even small direct coefficients compound into large total effects."
---

## The Problem With Direct Coefficients

The [A matrix](/learn/03-technical-coefficients-A) tells us what each industry purchases *directly* per dollar of output. But production is circular. To make steel, a steelmaker buys electricity. To generate that electricity, the utility buys fuel. To extract that fuel, the miner buys steel pipe. Every industry's inputs have their own inputs, which have their own inputs, in an infinite regress of indirect requirements.

Leontief's central insight was to close this loop algebraically.[cite:leontief_1941] Start from the basic identity: total output $x$ equals intermediate demand $Ax$ plus final demand $f$:

$$x = Ax + f$$

Rearranging:

$$(I - A)\,x = f$$

If $(I - A)$ is invertible — and for any real economy it is — we can solve for $x$:

$$x = (I - A)^{-1} f \equiv L\,f$$

The matrix $L = (I - A)^{-1}$ is the **Leontief inverse**, also called the **total requirements matrix**.[cite:miller_blair_2009_ch2] Each element $L_{ij}$ gives the total output of industry $i$ — direct plus all indirect rounds — required to deliver one dollar of final demand for industry $j$'s output.

## The Power-Series Intuition

Why is $L_{ij}$ always *larger* than the direct coefficient $a_{ij}$? The power-series expansion makes this transparent.

When $\|A\| < 1$ (which holds for any productive economy — it spends less than a dollar of inputs to produce a dollar of output), the matrix inverse converges as an infinite sum:

$$L = (I - A)^{-1} = I + A + A^2 + A^3 + \cdots$$

Think of it as successive rounds of spending:

- **$I$** — Round 0: the final demand itself. One dollar in, one dollar of output needed.
- **$A$** — Round 1: the *direct* inputs needed to produce that dollar.
- **$A^2$** — Round 2: the inputs needed to produce the inputs (the indirect effect, one step back in the supply chain).
- **$A^3$** — Round 3: one more step back.
- **$\cdots$** — Converging geometric decay, because each dollar of input requires less than a dollar's worth of further inputs.

Each successive power of A is smaller — the ripple attenuates — but the sum is always strictly greater than A alone. This is why total requirements always exceed direct requirements, and why industries with dense backward linkages generate large multipliers even when their own direct coefficients look modest.[cite:miller_blair_2009_ch2]

## The Leontief Inverse for the U.S., 2002

Here is L for the full 71-sector U.S. economy in 2002:

{{chart:heatmap:2002:L}}

Compare this heatmap with the [A matrix heatmap](/learn/03-technical-coefficients-A): the L matrix is visibly *brighter and denser*. Many cells that were near zero in A are now noticeably positive in L, because indirect linkages — the supply chain behind the supply chain — reach farther than direct purchases do.

The brightest columns in L identify sectors with the highest **output multipliers**: an extra dollar of final demand for them triggers the most economy-wide activity. In the U.S. data, manufacturing and energy sectors consistently show the largest column sums across all 28 years of coverage (1997–2024).

## Reading a Single Entry

Suppose $L_{\text{steel, auto}} = 0.09$. This means: to satisfy one additional dollar of final demand for automobiles, the economy must produce $0.09 of steel in total — directly (the steel the auto plant itself buys) *and* indirectly (the steel embodied in the machinery, the energy equipment, the paint, and so on that feed into auto production). The direct coefficient $a_{\text{steel, auto}}$ might be only $0.04$; the additional $0.05$ is pure indirect effect made visible by the Leontief inverse.

## Output Multipliers

The **output multiplier** for industry $j$ is the column sum of L:

$$m_j = \sum_i L_{ij}$$

It answers the practical question every policy analyst asks: if government purchases from sector $j$ rise by one dollar, by how much does total U.S. output rise?[cite:miller_blair_2009_ch6]

Across the 28 years in Leontief, the cross-sector mean output multiplier has ranged from **1.87 in 2024** to **2.02 in 2008**, with a typical spread from about 1.17 (the lowest, usually a non-manufacturing service) to about 3.18 (the highest, usually a materials or energy sector at commodity-price peaks). The 2008 peak reflects rising input intensities during the commodity boom; the 2020 trough reflects pandemic-era supply-chain disruption.

{{chart:multiplier_trend}}

## Solving for Output

The fundamental result $x = Lf$ is both a forecast tool and a thought experiment. Given any vector of final demand — consumption, investment, exports, government — you can compute the total output each of the 71 sectors must produce to satisfy it. Change one element of $f$ (say, a defense spending increase) and the matrix multiplication instantly propagates that shock through every tier of the supply chain.

```python
import numpy as np, pandas as pd

# Fetch L and final demand for 2002 as CSV (first column = sector labels -> index)
L_df  = pd.read_csv("https://leontief.heterodata.org/api/table/2002/L?fmt=csv", index_col=0)
fd_df = pd.read_csv("https://leontief.heterodata.org/api/table/2002/FD?fmt=csv", index_col=0)

L = L_df.to_numpy()

# Total final demand vector, aligned to L's 71-sector index (sum across all
# final-demand columns; sectors absent from FD contribute 0)
f = fd_df.sum(axis=1).reindex(L_df.index).fillna(0).to_numpy()

# Solve for required total output
x_required = L @ f

labels = list(L_df.columns)
top = np.argsort(x_required)[-5:][::-1]
for i in top:
    print(f"{labels[i]}: ${x_required[i]/1e9:.1f}B required output")
```

## An Important Caveat: Technology Changes

L is computed from A, which is computed from the Use table for a *specific year*. Use L_2002 to analyze 2002 conditions; use L_2024 to analyze 2024 conditions. Applying a 2002 L to 2024 final demand ignores two decades of technological change — the rise of digital services, shifts in energy sourcing, the reshaping of global supply chains.[cite:bea_concepts_2009] Leontief publishes L for all 28 years precisely so you can study how the total-requirements structure itself has shifted — which is the subject of [Structural Decomposition Analysis](/studies/structural-decomposition).

---

## Where Next

**Continue to:** Tutorial 5 — Output Multipliers and Linkage Analysis, where we turn column sums of L into sector rankings and identify the economy's key industries.

**Applied:** Explore the [Shock Propagation study](/studies/shock-propagation-hem) to see the Leontief inverse in action: how a demand shock in one sector ripples through L to affect every other industry in the U.S. economy.

## Further reading

- Miller &amp; Blair (2009), ch. 2 — the derivation of $L = (I-A)^{-1}$ and its power-series interpretation $I + A + A^2 + \cdots$. [cite:miller_blair_2009_ch2]
- Miller &amp; Blair (2009), §12.3 — the relative sizes of elements in the Leontief inverse and which coefficients matter most. [cite:miller_blair_2009_ch12]
- ten Raa (2005), *The Economics of Input-Output Analysis* — an alternative, mathematically compact derivation. [cite:ten_raa_2005]
