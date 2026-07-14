---
title: "If One Sector Vanished: Hypothetical Extraction"
order: 3
difficulty: intro
summary: "The Hypothetical Extraction Method (HEM) ranks every sector by the gross output the economy would lose if that sector disappeared entirely — as buyer and as supplier simultaneously. The answer is not always who you expect."
---

## The Question

Which sectors are truly indispensable? One answer comes from linkage indices — which sector has the longest supply chain or the broadest downstream reach? But linkage indices normalize out absolute scale. A fuller question is: *if this sector simply vanished, taking with it both its purchases from other industries and its sales to them, how much total output would the rest of the economy lose?*

That is the Hypothetical Extraction Method (HEM).[cite:miller_blair_2009_ch12]

---

## The Method

Start with the 2024 direct-requirements matrix $A$ — the clean square 71x71 matrix whose entries $a_{ij}$ record how many cents of sector $i$'s output are needed per dollar of sector $j$'s output. This is the *square* $A$, derived from the published Leontief inverse as $A = I - L^{-1}$; it is not the raw asymmetric BEA A matrix.

For each sector $k$, construct a modified matrix $A'$ by zeroing the entire $k$th row and $k$th column:

$$a'_{ij} = \begin{cases} 0 & \text{if } i = k \text{ or } j = k \\ a_{ij} & \text{otherwise} \end{cases}$$

Zeroing column $k$ removes sector $k$'s purchases from all other industries (its backward linkages — it stops buying inputs). Zeroing row $k$ removes sector $k$'s sales to all other industries as an intermediate (its forward linkages — it stops supplying inputs). Both are removed simultaneously: a complete extraction.

Recompute the modified Leontief inverse:

$$L' = (I - A')^{-1}$$

The extraction impact of sector $k$ is the difference in total economy-wide gross output:

$$\text{impact}_k = \mathbf{1}^\top L f - \mathbf{1}^\top L' f$$

where $f$ is the vector of aggregated final demand (sum of all BEA final-demand categories per sector). Sectors with larger $\text{impact}_k$ are more structurally critical.

Note: the impact is an *upper bound* on the disruption from sector $k$'s loss, because it assumes no substitution and no re-routing of demand through other sectors. It measures structural position, not welfare cost.

---

## What the Data Show (2024)

The baseline total gross output with all 71 sectors is **$59.3 trillion**. The chart below shows the top 15 sectors by extraction impact.

{{chart:study:shock-propagation-hem:hem_ranking}}

**Wholesale trade** (sector 42) tops the ranking with an extraction impact of **$3.46 trillion**, or 5.83% of baseline output. This is not surprising: wholesale is the economy's logistical connective tissue — it sits between manufacturing and retail, between importers and distributors, between producers and business buyers. Its forward linkages run to virtually every downstream sector; its backward linkages pull from transportation, warehousing, real estate, and financial services.

Second is **Food and beverage and tobacco products** ($3.39 trillion, 5.72%). Food processing is the economy's largest manufacturing subsector by output, buying heavily from agriculture, packaging, chemicals, and energy, and supplying retail, food services, and government.

**Other real estate** ranks third ($3.19 trillion, 5.38%). Real-estate services are an input to nearly every productive activity — offices, factories, warehouses, retail space — so a forward-linkage-dominant sector like real estate scores high even though its own intermediate purchases are modest.

**Miscellaneous professional services** ($3.07 trillion, 5.18%) and **Construction** ($2.75 trillion, 4.64%) round out the top five. Construction's high rank reflects both its enormous backward reach into primary metals, cement, wood, and mechanical systems, and the fact that nearly every expanding sector needs new capacity.

| Sector | Extraction Impact | % of Total |
|---|---|---|
| Wholesale trade | $3,457B | 5.83% |
| Food & beverage & tobacco | $3,390B | 5.72% |
| Other real estate | $3,191B | 5.38% |
| Misc. professional services | $3,068B | 5.18% |
| Construction | $2,748B | 4.64% |
| Motor vehicles & parts | $2,589B | 4.37% |
| Chemical products | $2,442B | 4.12% |
| State & local government | $2,023B | 3.41% |
| Admin & support services | $1,989B | 3.36% |
| Farms | $1,776B | 3.00% |

A notable feature of the top 10: not one of the sectors with the highest output multipliers in the [multipliers study](/studies/multipliers-explained) appears here undiluted. Motor vehicles, which has the highest output multiplier (2.77), ranks **sixth** in the HEM. Why? The multiplier measures supply-chain depth per dollar of final demand; the HEM measures total output supported in absolute terms. Wholesale trade has a modest multiplier (near the economy average) but enormous throughput — it handles a huge volume of final demand, so its absolute extraction impact is correspondingly large.

---

## The Takeaway

HEM reframes the question of sector importance from *how deep is your supply chain?* to *how much of the economy would stop working if you disappeared?* The two questions have different answers.

Backward-linkage leaders like motor vehicles score high on both lists. But the HEM additionally rewards sheer scale and indispensability as an intermediary — which is why wholesale trade, real estate services, and food processing displace the manufacturing champions of the multiplier rankings.

For economic policy, the HEM ranking suggests where systemic disruptions are most costly. A shock to wholesale distribution (think port closures, supply-chain blockages) or food processing (drought, processing-plant failures) propagates more broadly than a shock to any single manufacturing subsector. The HEM gives a concrete, matrix-grounded number for these propagation magnitudes.

---

## Reproduce This

Download the full replication bundle at:

**[/api/study/shock-propagation-hem/bundle.zip](/api/study/shock-propagation-hem/bundle.zip)**

```bash
unzip shock-propagation-hem.zip
cd shock-propagation-hem
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/hem_2024.csv, outputs/fig_hem_ranking.json
```

The script reads `data/A_square_2024.csv` (71x71 direct-requirements matrix, derived from the BEA Leontief inverse as $A = I - L^{-1}$), `data/fd_agg_2024.csv` (aggregated final demand per sector), and `data/sector_names.csv`. It uses only `numpy.linalg.inv` — no scipy or networkx. An `analysis.ipynb` notebook mirrors every step interactively.

[cite:miller_blair_2009_ch12]
