---
title: "The Recipe Book: Technical Coefficients and the A Matrix"
order: 3
summary: "How the Use table is compressed into the A matrix — the economy's recipe book, where each column says exactly what inputs any industry must buy per dollar of its output."
---

## From Dollars Spent to Proportions

The [Use table](/methodology) is enormous and hard to interpret at a glance: raw dollar flows that balloon in boom years and shrink in recessions, making cross-year comparison treacherous. To get at the underlying *structure* of production — the stable technological relationships between sectors — economists divide each flow by the output of the purchasing industry.

That division is the entire story of the A matrix.

Define $z_{ij}$ as the dollar value of commodity $i$ used by industry $j$ as an intermediate input, and $x_j$ as the total output of industry $j$. The **technical coefficient** is simply:

$$a_{ij} = \frac{z_{ij}}{x_j}$$

Read it as: *for every dollar of output that industry $j$ produces, it must purchase $a_{ij}$ dollars of input from sector $i$*.[cite:miller_blair_2022] Scale up or scale down production, and — under the key assumption that proportions hold — you can read off all input requirements directly from a column of A.

Stacking all these coefficients into a matrix gives **A**, the direct requirements matrix. It is the economy's **recipe book**: each column is a recipe for one industry, listing every ingredient and its quantity per dollar of output.

## A Concrete Example

Suppose the Petroleum refining industry (a real BEA sector) has total output $x_j = \$100$ billion. Its Use table column shows it purchased $\$12$ billion of Crude oil and $\$4$ billion of Chemical products. The corresponding technical coefficients are:

$$a_{\text{crude},\,\text{petro}} = \frac{12}{100} = 0.12 \qquad a_{\text{chem},\,\text{petro}} = \frac{0.04}{100} = 0.04$$

These numbers are far more informative than the raw flows. They remain stable across years even as nominal output expands with inflation, and they let us compare the petroleum industry's input structure in 2002 versus 2024 on an equal footing.

The full A matrix for the U.S. economy in 2002 — 71 sectors — looks like this:

{{chart:heatmap:2002:A_square}}

Most cells are near zero (grey). The bright patches along certain rows reveal commodities that are truly universal inputs — energy, finance, real estate — bought in non-trivial proportion by many industries. The diagonal is not especially bright: an industry does not primarily buy from itself.

You can also inspect the matrix numerically, aggregated to 15 sectors for readability:

{{table:2002/A_square?agg=15}}

## The Constant-Returns Assumption

The formula $a_{ij} = z_{ij}/x_j$ assumes that input proportions are **fixed and constant** regardless of output scale. This is the *constant-returns-to-scale* assumption built into standard [input-output analysis](/glossary#a-matrix-direct-requirements-matrix--technical-coefficients): double $x_j$ and all inputs double proportionally.

Real production is messier — there are economies of scale, factor substitution, and technological change. For short-run analysis or for tracing supply-chain linkages, the assumption is workable. For long-run comparisons across decades, it is a simplification. This is exactly why Leontief publishes A matrices for all 28 years from 1997 to 2024: you can *see* how the recipe book changes, rather than assuming it is static.[cite:bea_concepts_2009]

## An Honest Caveat: 70 × 71 vs Square

A subtlety matters here. BEA's Use table has **commodities in rows** and **industries in columns** — these are not the same dimension. The BEA Summary classification has 71 industries but the commodity side, after netting out final-demand and other rows, yields 70 tradeable commodity rows that feed back into production.

The result: the published BEA direct-requirements matrix A is technically **70 × 71** — *not* square. This is a commodity-vs-industry alignment artifact, not an error. A 70 × 71 matrix cannot be subtracted from the identity matrix, so you cannot compute the [Leontief inverse](/learn/04-leontief-inverse) $(I - A)^{-1}$ directly from it.

To solve this, Leontief also publishes **A_square**: a square 71 × 71 version derived by applying the industry-technology assumption to allocate secondary products back to their primary industry, yielding an industry-by-industry direct requirements matrix. The heatmap above and the table above both show A_square. See our [methodology](/methodology) page for the full derivation.

```python
import requests, numpy as np

# Fetch A_square for 2002 (71x71) via the Leontief API
resp = requests.get("http://localhost:5000/api/table/2002/A_square.json")
data = resp.json()

labels = data["columns"]
A = np.array(data["data"])

# Which sector has the largest average direct requirements?
col_means = A.mean(axis=0)
top = np.argmax(col_means)
print(f"Most input-intensive sector: {labels[top]} (mean a_ij = {col_means[top]:.4f})")
```

## Why A Is Central

The A matrix is the foundation for nearly everything else on this site. [Multiplier analysis](/glossary#output-multiplier) asks: if final demand for sector $j$ rises by one dollar, how much total output does the economy generate? That question cannot be answered from A alone — it requires summing all the indirect rounds of production. That is the job of the [Leontief inverse](/learn/04-leontief-inverse), which we build directly from A.

The recipe book metaphor has one more virtue: it makes clear that the economy is not a collection of isolated industries. Every recipe calls for ingredients produced by other industries, which in turn have their own recipes. A is the compact encoding of that web of interdependence.

---

## Where Next

**Continue to:** [Tutorial 4 — The Leontief Inverse](/learn/04-leontief-inverse), where we invert $(I - A)$ to get total requirements and discover that even a small direct coefficient can imply a large economy-wide impact.

**Applied:** Explore the [Supply Chains Network study](/studies/supply-chains-network) to see how A-matrix structure reveals the most connected sectors in the U.S. economy.
