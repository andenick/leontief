---
title: The Economy as a Network
order: 8
summary: Reframe the I-O table as a directed graph — industries are nodes, dollar flows are edges — and see why shocks to hub sectors ripple across the whole economy.
---

## A Table Is a Graph

Every input-output table is, at its core, a description of who sells to whom. The [technical coefficients](/glossary#technical-coefficients) matrix $A$ records what fraction of sector $j$'s output comes from sector $i$: each nonzero entry $a_{ij}$ is a directed edge from $i$ to $j$ weighted by the dollar value flowing along it.

Turn that framing around: the economy is a **directed, weighted graph** of 71 nodes (sectors) and up to $71 \times 71 = 5{,}041$ possible edges. Not all edges are active — in any given year most $a_{ij}$ are zero or negligibly small — but the structure of the nonzero entries is what determines how shocks and surpluses propagate.

The heatmap below shows the 2024 $A$ matrix aggregated to 15 broad groups, where cell color encodes the magnitude of intermediate purchases. Read it as an adjacency picture: a dark cell at row $i$, column $j$ means sector $j$ draws heavily on sector $i$ as a supplier.

{{chart:heatmap:2024:A_square:15}}

## Centrality: Which Sectors Are Hubs?

In network analysis, **centrality** measures how important a node is to the overall connectivity of a graph. Several measures have I-O counterparts:

**Degree centrality** — a sector with high *out-degree* supplies many others; high *in-degree* means it buys from many. In I-O terms these correspond directly to [forward linkages and backward linkages](/glossary#linkages).

**Eigenvector centrality** — a sector is important if it is connected to other important sectors. This recursive idea is exactly what the [Leontief inverse](/glossary#leontief-inverse) $L = (I - A)^{-1}$ captures: the $(i,j)$ entry of $L$ sums all direct *and* indirect paths from $i$ to $j$, weighted by their intensity. The column sum $m_j = \sum_i l_{ij}$ is the [output multiplier](/glossary#multiplier) for sector $j$ — a direct measure of how much total output the whole economy must generate to satisfy one dollar of final demand for $j$'s product [cite:miller_blair_2009_ch14].

**Betweenness centrality** — how often does a sector lie on the shortest path between two other sectors? Sectors with high betweenness are bottlenecks: disrupting them severs the most supply-chain routes simultaneously.

The scatter below plots backward linkage (total output multiplier) against forward linkage (sensitivity index) for all 71 sectors in 2024. Sectors in the upper-right quadrant are [key sectors](/glossary#key-sector) — strong hubs in both directions.

{{chart:linkage_scatter?year=2024}}

## Community Detection: Supply-Chain Neighborhoods

Real supply chains are not uniformly connected. They cluster. Automobile assembly buys heavily from steel, rubber, glass, and electronics; it buys little from restaurant services or real estate. These clusters are **communities** in the network sense — groups of nodes that trade intensively with each other and relatively little with the rest.

Formal community-detection algorithms (e.g., the Louvain method or spectral clustering applied to the weighted adjacency matrix $A$) recover these neighborhoods automatically from the data, without imposing a prior grouping. The communities they find often correspond to recognizable supply-chain archetypes:

- A manufacturing-materials cluster (metals, chemicals, plastics feeding durable goods)
- A finance-real-estate-insurance cluster (FIRE sectors with heavy mutual flows)
- A services-and-government cluster (health care, education, public administration)

These communities are not fixed: the 1997 table has a different community structure than the 2024 table, because the technology matrix $A$ itself changed — the very phenomenon Tutorial 07 quantified with SDA.

## Cascade and Contagion: Why Shocks Don't Average Out

The most consequential insight from the network view of I-O is about **aggregate volatility**. Standard macroeconomic intuition suggests that idiosyncratic shocks — a bad harvest, a factory fire, a supplier disruption — should cancel out across many sectors: positive and negative shocks average to zero.

Acemoglu, Carvalho, Ozdaglar, and Tahbaz-Salehi (2012) showed formally why this intuition fails when the supply network is skewed [cite:acemoglu_2012]. If the degree distribution of the production network has a heavy tail — a few sectors are extremely well-connected hubs while most are peripheral — then shocks to the hubs do *not* wash out. Instead:

$$\sigma_{\text{aggregate}} \sim \frac{1}{\sqrt{n}} + \lambda_{\max}(A) \cdot \sigma_{\text{sector}}$$

The first term is the familiar diversification effect that shrinks as $n \to \infty$. The second term, proportional to the **spectral radius** $\lambda_{\max}(A)$ of the technology matrix, persists. If the largest eigenvalue of $A$ is close to 1 — which it will be in an economy with tight input-output linkages — a shock to a central sector (high eigenvector centrality) propagates through the entire production network and never fully diversifies away.

This is a precise statement of why macroeconomic disasters can originate in microeconomic events: the 2011 Fukushima earthquake disrupted global automobile and electronics supply chains far beyond Japan; the 2021 semiconductor shortage cascaded from chips into cars, appliances, and medical devices. The I-O network is the transmission mechanism [cite:acemoglu_2012][cite:miller_blair_2009_ch14].

## Try It

```python
import numpy as np

def network_stats(A):
    """Compute basic network stats from a square A matrix."""
    n = A.shape[0]
    # Spectral radius (largest real eigenvalue)
    eigenvalues = np.linalg.eigvals(A)
    spectral_radius = np.max(np.abs(eigenvalues))
    # Out-strength (column sums = backward linkage proxy)
    out_strength = A.sum(axis=0)
    # In-strength (row sums = forward linkage proxy)
    in_strength = A.sum(axis=1)
    return {
        "spectral_radius": spectral_radius,
        "top_out": np.argsort(out_strength)[::-1][:5],
        "top_in": np.argsort(in_strength)[::-1][:5],
    }
```

## Data Note

All matrices here come from BEA Summary I-O tables at the 71-sector level, covering 1997–2024 (28 annual observations). The square $A$ matrix is derived from the industry-by-industry Use table after the BEA's redefinition adjustments, which reassign secondary products to their primary industry — improving structural stability across years [cite:bea_concepts_2009][cite:un_handbook_2018].

## Where Next

- **Tutorial 09** — Supply Chains and Global Value Chains: how do we extend the domestic network to include imports and track where value is *actually* created along international production chains?
- **Deep dive** — [Supply Chains as Networks](/studies/supply-chains-network): centrality rankings across all 28 years, community structure evolution, and a replication of the Acemoglu et al. cascade model on BEA data.

## Further reading

- Miller &amp; Blair (2009), §14.3 — graph theory, structural path analysis, and qualitative input-output analysis (the network view of the I-O table). [cite:miller_blair_2009_ch14]
- Acemoglu, Carvalho, Ozdaglar &amp; Tahbaz-Salehi (2012) — how aggregate fluctuations originate in the network structure of production. [cite:acemoglu_2012]
