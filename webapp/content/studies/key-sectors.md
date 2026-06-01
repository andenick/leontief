---
title: "Which Industries Are the Economy's Hubs?"
order: 1
difficulty: intro
summary: "Rasmussen linkage indices measure every sector's pull on suppliers (backward linkage) and push into downstream users (forward linkage). Sectors above average on both are the economy's strategic hinges — its key sectors."
---

## The Question

Every industry buys inputs from suppliers and sells outputs to other producers. Some industries do both intensively; others specialize in one direction. To spot the economy's structural hubs — the sectors where a disruption or stimulus reverberates most widely — we need a way to measure both directions of dependence at once.

That tool is **Rasmussen's linkage indices**, computed directly from the Leontief inverse $L = (I - A)^{-1}$.[cite:miller_blair_2022]

---

## The Method

### Backward Linkage (Power of Dispersion)

The *output multiplier* of sector $j$ is its column sum in $L$: $\sum_i l_{ij}$. To compare sectors on a common scale, normalize by the grand mean of all $n^2$ elements of $L$:

$$U_j^b = \frac{\dfrac{1}{n}\displaystyle\sum_{i=1}^{n} l_{ij}}{\dfrac{1}{n^2}\displaystyle\sum_{i=1}^{n}\sum_{j=1}^{n} l_{ij}}$$

When $U_j^b > 1$, sector $j$ pulls more from its suppliers than the typical industry. When $U_j^b < 1$, it pulls less. By construction the simple average across all 71 sectors equals exactly 1.

Rasmussen called this the **power of dispersion**: how broadly does a unit of final demand for $j$ disperse purchasing power across the economy?

### Forward Linkage (Sensitivity of Dispersion)

The mirror measure uses the *row* sum of $L$, normalized identically:

$$U_i^f = \frac{\dfrac{1}{n}\displaystyle\sum_{j=1}^{n} l_{ij}}{\dfrac{1}{n^2}\displaystyle\sum_{i=1}^{n}\sum_{j=1}^{n} l_{ij}}$$

When $U_i^f > 1$, sector $i$'s output feeds more than average into other industries as an intermediate input. Rasmussen called this the **sensitivity of dispersion**: how sensitive is sector $i$ to a general rise in final demand across the whole economy?[cite:dietzenbacher_los_1998]

### Key Sectors

Albert Hirschman's development-strategy insight, formalized by Rasmussen, is that the economy's strategic sectors are those with **both** $U^b > 1$ and $U^f > 1$. They sit in the upper-right quadrant of the linkage scatter — simultaneously strong pullers of upstream activity and strong feeders of downstream production.

---

## What the Data Show (2024)

The scatter below plots all 71 BEA Summary sectors for 2024. The dotted lines are the unit-average boundaries. Red dots are key sectors.

{{chart:study:key-sectors:linkage_scatter}}

In 2024, **13 sectors** qualify as key sectors (down from 14 in 2002). The standouts are:

| Sector | Backward $U^b$ | Forward $U^f$ |
|---|---|---|
| Motor vehicles, bodies & trailers | 1.482 | 1.144 |
| Primary metals | 1.414 | 1.813 |
| Food & beverage & tobacco products | 1.369 | 1.001 |
| Paper products | 1.270 | 1.097 |
| Fabricated metal products | 1.245 | 1.450 |
| Petroleum & coal products | 1.234 | 1.041 |
| Other real estate | 1.110 | 2.735 |
| Chemical products | 1.006 | 2.046 |

**Motor vehicles** leads on backward linkage (1.48): every dollar of cars assembled fans out across steel, rubber, glass, electronics, and a long tail of component suppliers. **Primary metals** leads among key sectors on forward linkage (1.81): when final demand rises anywhere in the economy, metals are pulled in disproportionately as a universal intermediate. **Other real estate** has the highest forward linkage of any key sector (2.74) — nearly all productive activities require premises, so real-estate services are deeply embedded in downstream cost structures.

The bar chart below ranks the top 15 sectors by combined linkage ($U^b + U^f$). A sector at the average on both indices scores exactly 2.0; sectors to the right of the dotted line exceed the average in sum.

{{chart:study:key-sectors:key_sectors_bar}}

Notably, **Wholesale trade** (FL = 2.84) and **Miscellaneous professional services** (FL = 2.55) have the highest forward linkages in the entire economy — but their backward linkage falls below 1, placing them in the "forward-oriented" quadrant rather than among key sectors.

{{table:2024/L}}

---

## The Takeaway

Linkage analysis gives economic policy a spatial language. A backward-dominant sector (lower-right quadrant) generates upstream ripples when stimulated but does not bottleneck downstream producers. A forward-dominant sector (upper-left quadrant) is a potential chokepoint: if it contracts, many industries feel input scarcity. A true key sector multiplies in both directions — the kind of hub that classical development economists argued should anchor industrialization strategies.

Between 2002 and 2024 the number of key sectors fell from 14 to 13. The most persistent members of the key-sector club are durable-goods manufacturing (motor vehicles, primary metals, fabricated metals), food processing, and a handful of infrastructure-like intermediaries (real estate, petroleum products). Services-sector growth has, on net, thinned the ranks of sectors with unusually strong backward pull.

---

## Reproduce This

Download the full replication bundle — data, code, and notebook — at:

**[/api/study/key-sectors/bundle.zip](/api/study/key-sectors/bundle.zip)**

```bash
unzip key-sectors.zip
cd key-sectors
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/linkages_2024.csv, outputs/fig_linkage_scatter.json, outputs/fig_key_sectors_bar.json
```

The script reads `data/L_2024.csv` and `data/L_2002.csv` (Leontief inverses exported from the BEA cache) and `data/sector_names.csv`. It writes result tables and Plotly JSON figures to `outputs/`. An `analysis.ipynb` notebook mirrors every step for interactive exploration.

[cite:miller_blair_2022][cite:dietzenbacher_los_1998]
