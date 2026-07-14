---
title: "Mapping Supply Chains with Network Analysis"
order: 6
difficulty: intermediate
summary: "Treating the 2024 input-output A-matrix as a directed weighted network reveals which industries are genuine hubs — sectors whose output feeds everywhere and whose centrality cannot be averaged away. Eigenvector centrality computed via power iteration identifies professional services, insurance, chemicals, real estate, and primary metals as the backbone of U.S. supply chains."
---

## The Question

Standard linkage analysis (backward and forward indices) treats each sector's connections symmetrically. But supply chains are networks, and networks have a crucial property that simple averages miss: **centrality compounds**. A sector that sells to other highly-connected sectors matters more than a sector of equal size that sells to peripheral buyers. If that hub sector is hit by a shock, its disruption cannot be diversified away across many small suppliers — it propagates.

This is the core idea in Acemoglu, Carvalho, Ozdaglar, and Tahbaz-Salehi (2012): in a network economy, idiosyncratic shocks to sufficiently central sectors generate aggregate fluctuations that do not disappear as the economy grows. The technical coefficient matrix $A$ is not just a production recipe — it is a weighted directed graph, and the topology of that graph determines how shocks travel.[cite:acemoglu_2012]

---

## The Method

### The A-Matrix as an Adjacency Matrix

The 68×68 commodity-by-commodity A-matrix for 2024 has entries $a_{ij}$ = the fraction of sector $j$'s gross output purchased from sector $i$ as an intermediate input. Treating this as a directed weighted network:

- **Nodes** = 68 BEA Summary commodity sectors
- **Edges** = $a_{ij} > 0$ (sector $i$ sells to sector $j$ with weight $a_{ij}$)
- **In-strength** of sector $j$ = $\sum_i a_{ij}$ (column sum) = total intermediate-input share of $j$'s output
- **Out-strength** of sector $i$ = $\sum_j a_{ij}$ (row sum) = total intermediate sales of $i$ across all buyers

### Eigenvector Centrality via Power Iteration

Standard degree centrality (strength) treats all neighbors equally. Eigenvector centrality weights each neighbor by its own centrality — a sector is central if it sells to sectors that are themselves central. The centrality vector $v$ satisfies:

$$A \, v = \lambda_{\max} \, v$$

where $\lambda_{\max}$ is the dominant eigenvalue of $A$. We compute $v$ by power iteration (no external libraries — only `numpy.linalg`):[cite:miller_blair_2009_ch14]

$$v^{(k+1)} = \frac{A \, v^{(k)}}{\|A \, v^{(k)}\|_2}, \qquad v^{(0)} = \tfrac{1}{n}\mathbf{1}$$

until $\|v^{(k+1)} - v^{(k)}\|_2 < 10^{-12}$. The resulting vector is normalised to $[0, 1]$.

The dominant eigenvalue of the 2024 A-matrix is $\lambda_{\max} \approx 0.980$, slightly below 1, consistent with the fact that columns of $A$ do not sum to exactly 1 (value added and imports fill the gap).

---

## What the Data Show

### Eigenvector Centrality: Who are the Real Hubs?

{{chart:study:supply-chains-network:centrality}}

The top 10 sectors by eigenvector centrality in 2024:

| Sector | Centrality | Out-strength | Group |
|---|---|---|---|
| Insurance carriers & related (524) | **1.000** | 2.69 | Finance |
| Misc. professional services (5412OP) | 0.979 | **5.19** | Prof. & Business Svcs |
| Chemical products (325) | 0.950 | 3.21 | Manufacturing |
| Other real estate (ORE) | 0.797 | 5.06 | Finance |
| Administrative & support services (561) | 0.656 | 3.44 | Prof. & Business Svcs |
| Primary metals (331) | 0.460 | 1.89 | Manufacturing |
| Federal Reserve & credit intermediation (521CI) | 0.422 | 2.75 | Finance |
| Management of companies (55) | 0.380 | 2.40 | Prof. & Business Svcs |
| Computer & electronic products (334) | 0.290 | 1.56 | Manufacturing |
| Fabricated metal products (332) | 0.288 | 2.02 | Manufacturing |

The top position — **Insurance carriers** (524, centrality = 1.000) — reflects a structural fact: insurance services are purchased as an intermediate by nearly every sector in the economy, from manufacturing to retail to construction. Insurance flows are embedded in almost every business's cost structure. A sector that sells to everyone, and sells to sectors that themselves sell to everyone, rises to the top of the centrality ranking even if its gross out-strength is not the largest.

**Miscellaneous professional services** (5412OP) has the largest raw out-strength (row sum = 5.19), meaning its output is diffused most widely across buyer industries. Its centrality of 0.979 confirms that it also sells heavily to other hub sectors.

**Chemical products** (325) is the manufacturing hub: inputs from chemicals — adhesives, plastics intermediates, specialty chemicals — permeate food processing, pharmaceuticals, rubber, textiles, and dozens of other upstream-intensive industries.

### In-Strength vs Out-Strength

{{chart:study:supply-chains-network:strength_scatter}}

The scatter of in-strength versus out-strength separates four structural types:

- **High in, high out** (upper right): genuine intermediary sectors — they both buy extensively from others and sell extensively into the network. Misc. professional services, chemicals, administrative services, and real estate cluster here. These are the economy's circulatory arteries.
- **High in, low out** (upper left): would appear here if out-strength is near zero while absorbing large intermediates. Largely empty — few sectors absorb a lot without selling much to others.
- **Low in, high out** (lower right): sellers that add little value from purchased intermediates. Not prominent in the 2024 data — most large-out-strength sectors also have substantial in-strength.
- **Low in, low out** (lower left): peripheral sectors — government enterprises, housing, some public services — with limited intermediate linkages in both directions.

The diagonal (in = out) is a reference: sectors above it sell *more* to others than they absorb, making them net suppliers to the intermediate-goods network.

---

## Connecting to Aggregate Fluctuations

Acemoglu et al. (2012) show that in an economy with $n$ sectors, idiosyncratic shocks average out at rate $1/\sqrt{n}$ only if the network is symmetric. When the network has "star" structure — a few highly-central sectors connected to many peripheral ones — aggregate volatility decays at the slower rate $1/\log(n)$, and in the limit a shock to the top hub propagates at full force.[cite:acemoglu_2012]

The 2024 U.S. A-matrix is not a star, but it is far from uniform. The top 5 sectors by eigenvector centrality account for a disproportionate share of the network's aggregate influence. A sustained disruption to chemical supply chains (think a major facility closure, a trade restriction on specialty chemicals), or a broad contraction in professional and business services (think a credit-driven slump in B2B outsourcing), would not diversify away. It would propagate through the supply-chain network to every sector that depends on those intermediates.

This is why network topology matters for macroeconomic stability — and why the input-output table, properly read as an adjacency matrix, is a tool for identifying systemic risk in the production network, not merely for computing multipliers.[cite:miller_blair_2009_ch14]

---

## Reproduce This

Download the full replication bundle — data, code, and notebook — at:

**[/api/study/supply-chains-network/bundle.zip](/api/study/supply-chains-network/bundle.zip)**

```bash
unzip supply-chains-network.zip
cd supply-chains-network
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/centrality_2024.csv, outputs/fig_centrality.json,
#          outputs/fig_strength_scatter.json
```

The script reads `data/A_square_2024.csv` (68×68 BEA commodity-by-commodity A-matrix), `data/sector_agg15.csv` (sector codes, names, and 15-group aggregation). All computation uses only `numpy` and `pandas` — no network libraries. The `analysis.ipynb` notebook mirrors every step for interactive exploration.

[cite:acemoglu_2012][cite:miller_blair_2009_ch14]
