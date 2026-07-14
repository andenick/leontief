---
title: "Linkages and Key Sectors"
order: 6
summary: "Backward linkage measures how strongly an industry pulls from its suppliers; forward linkage measures how widely its output feeds into other industries. Rasmussen indices normalize both onto a common scale so you can spot the economy's strategic hinge-points."
---

## Two Directions of Dependence

An economy is a web, not a pipeline. Every industry depends on others for its inputs (looking *backward* up the supply chain) and is depended upon by others as a supplier of inputs (looking *forward* down the production network). [Tutorial 05](/learn/05-output-income-employment-multipliers) showed you the output multiplier — a single column-sum number summarizing backward reach. Linkage analysis keeps both directions in view simultaneously.[cite:miller_blair_2009_ch12]

The distinction matters for policy. A sector with strong **backward linkage** generates substantial upstream economic activity when it expands — good news for suppliers. A sector with strong **forward linkage** is a bottleneck: when it contracts or becomes scarce, downstream industries feel the squeeze. Albert Hirschman, in his classic work on development strategy (*The Strategy of Economic Development*, 1958), argued that planners should prioritize industries with high linkages in both directions, because those sectors would induce the widest spread of complementary investment. The formal backward/forward linkage measures used below are developed in Miller &amp; Blair (2009), ch. 12.[cite:miller_blair_2009_ch12]

---

## Reading Linkage Out of L

Both measures are computed from the same [Leontief inverse](/glossary#leontief-inverse) $L$ used for multipliers. The difference is whether you look down a column (backward) or across a row (forward).

### Backward Linkage (Power of Dispersion)

The raw backward linkage of sector $j$ is its output multiplier — the column sum $\sum_i l_{ij}$. To compare sectors fairly, you normalize by the economy-wide average element of L:

$$U_j^b = \frac{\dfrac{1}{n}\displaystyle\sum_{i=1}^{n} l_{ij}}{\dfrac{1}{n^2}\displaystyle\sum_{i=1}^{n}\sum_{j=1}^{n} l_{ij}}$$

The denominator is the grand mean of all $n^2$ elements of L. When $U_j^b > 1$, sector $j$'s column average exceeds the all-sector average — it pulls more from suppliers than a typical industry. When $U_j^b < 1$, it is below average. By construction, the simple average of all $U_j^b$ values across sectors equals 1.

Rasmussen (1956) called this the **power of dispersion**: how broadly does a unit of final demand for $j$ "disperse" purchasing power across the economy?[cite:miller_blair_2009_ch12]

### Forward Linkage (Sensitivity of Dispersion)

The forward linkage of sector $i$ uses the *row* sum of L, normalized the same way:

$$U_i^f = \frac{\dfrac{1}{n}\displaystyle\sum_{j=1}^{n} l_{ij}}{\dfrac{1}{n^2}\displaystyle\sum_{i=1}^{n}\sum_{j=1}^{n} l_{ij}}$$

When $U_i^f > 1$, sector $i$'s output is relied upon by many downstream industries more than average. Rasmussen called this the **sensitivity of dispersion**: how sensitive is sector $i$'s output to final demand shocks spread across the whole economy?

A high forward linkage does not mean a sector is "productive" in any normative sense — it means that many other industries depend on it as an input, so an increase in final demand anywhere in the economy tends to increase demand for sector $i$'s output too.

---

## The Four-Quadrant Map

Plotting $U_j^b$ (horizontal axis) against $U_j^f$ (vertical axis) for all 71 sectors produces a scatter plot where the average sits at the point $(1, 1)$. The four quadrants have natural economic interpretations:

{{chart:linkage_scatter?year=2002}}

| Quadrant | $U^b$ | $U^f$ | Hirschman type | Typical examples |
|---|---|---|---|---|
| **Key sector** (upper right) | > 1 | > 1 | Both strong — strategic hinge | Manufacturing, energy |
| **Forward-oriented** (upper left) | < 1 | > 1 | Supplies widely, buys narrowly | Primary metals, chemicals |
| **Backward-oriented** (lower right) | > 1 | < 1 | Buys widely, supplies narrowly | Food processing, construction |
| **Weak** (lower left) | < 1 | < 1 | Below average both ways | Many service sectors |

The 2002 cross-section plotted above (a benchmark-quality year in the Leontief dataset) illustrates the classic pattern: manufacturing sectors cluster in the upper-right key-sector quadrant, while many service industries fall in the lower-left. The horizontal and vertical lines at 1.0 are the decision boundaries.

The most important insight from the scatter plot is that the four quadrants are not equally populated. In the U.S. 71-sector table, services occupy the lower-left overwhelmingly — the U.S. economy has a relatively service-heavy structure where many industries buy and sell primarily within their own sector or directly to final demand. Manufacturing and resource sectors carry the heavy cross-industry linkage load.[cite:miller_blair_2009_ch12][cite:dietzenbacher_los_1998]

---

## A Note on Caution: Rasmussen vs. Hypothetical Extraction

Rasmussen indices are useful, transparent, and easily computed — but they can overstate forward linkages for sectors whose row sums in L are large partly because the sector has a large diagonal element $l_{ii}$ (it uses a lot of its own output). A refinement is **hypothetical extraction** ([HEM](/glossary#hypothetical-extraction-hem)): you ask how much total output the economy would lose if sector $k$ were completely removed — setting its entire row and column in A to zero and re-solving. The resulting loss $\sum_i (x_i - \bar{x}_i)$ combines backward and forward effects without double-counting, but requires solving a new system for each sector tested.

For an introductory look at which sectors dominate the linkage structure, Rasmussen indices are the standard starting point.[cite:miller_blair_2009_ch12]

---

## The Hirschman Development Logic

Albert Hirschman's *The Strategy of Economic Development* (1958) is the origin of the applied linkage literature.[cite:hirschman_1958] The core argument: in a capital-scarce developing economy, you cannot build everything at once. Choose industries with high total linkages as your investment priorities — they will exert "inducement pressure" on complementary sectors, forcing private investors to fill gaps upstream and downstream. The Leontief framework gave this intuition a precise empirical form.

Modern network economics extends this idea: Acemoglu et al. (2012) show that in an economy with an asymmetric input-output network, aggregate fluctuations can originate from purely sectoral shocks — a finding that depends critically on which sectors occupy central positions in exactly the sense Rasmussen linkages measure.[cite:acemoglu_2012]

---

## Try It

Download the 2002 L matrix and compute Rasmussen indices from scratch:

```python
import pandas as pd

L = pd.read_csv("2002_L.csv", index_col=0)
n = L.shape[0]

# Grand mean of all elements
grand_mean = L.values.mean()

# Backward linkage (column means, normalized)
backward = L.mean(axis=0) / grand_mean

# Forward linkage (row means, normalized)
forward = L.mean(axis=1) / grand_mean

# Key sectors: both > 1
key = pd.DataFrame({"backward": backward, "forward": forward})
key_sectors = key[(key["backward"] > 1) & (key["forward"] > 1)]
print(f"Key sectors in 2002: {len(key_sectors)}")
print(key_sectors.sort_values("backward", ascending=False).head(8))
```

Both vectors should have mean 1.0 across all sectors — a quick sanity check that the normalization worked correctly.

---

## Where Next

**Next tutorial:** Tutorial 07 — Structural Decomposition Analysis asks how the L matrix and the final demand vector each contributed to the *change* in total output between two years — separating technology change from demand change over the full 1997–2024 span.

**Go deeper:** See the [Key Sectors study](/studies/key-sectors) for a full 28-year time series of Rasmussen indices, showing which sectors have held their key-sector status across the whole coverage period and which have migrated between quadrants as the U.S. economy restructured.

## Further reading

- Miller &amp; Blair (2009), ch. 12 — backward and forward linkages, the power/sensitivity of dispersion, and hypothetical extraction. [cite:miller_blair_2009_ch12]
- Rasmussen (1956), *Studies in Inter-Sectoral Relations* — the original dispersion indices. [cite:rasmussen_1956]
- Hirschman (1958), *The Strategy of Economic Development* — the development-policy motivation for prioritizing high-linkage sectors. [cite:hirschman_1958]
