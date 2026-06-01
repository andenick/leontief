---
title: "Cost-Push Prices and the Wage Share"
order: 9
difficulty: advanced
summary: "The price dual of the Leontief model shows how wage costs propagate through supply chains to raise output prices. A +10% compensation shock raises prices by 5.1–5.4% across sectors, with labor-intensive service supply chains hit hardest. The economy-wide labor share of value added has fallen from 57% in 1997 to 53% in 2024."
---

## The Question

Production costs are not confined to the sector where they originate. A wage increase in trucking raises the delivered cost of every commodity that travels by truck — and through the inter-industry network, those cost increases cascade further. Input-output analysis provides the exact arithmetic of this pass-through: the *price dual* of the Leontief quantity model.[cite:miller_blair_2022]

How much does a uniform 10% increase in labor costs raise output prices, and which sectors are most exposed through their supply-chain linkages? Separately, what has happened to the share of income going to labor across the American economy over the past three decades?

---

## The Method

### The Price Dual

The standard Leontief quantity model is $x = Ax + f$, solved as $x = (I-A)^{-1}f$. Its dual — the *cost-push price model* — runs in the opposite direction. If $v_j$ is the unit value added in sector $j$ (primary-factor cost per dollar of gross output), then equilibrium output prices satisfy:

$$p = v\,(I - A)^{-1}$$

where $p$ and $v$ are row vectors of length $n$.[cite:pasinetti_1981] Each element $p_j$ is the price of sector $j$'s output, expressed as a multiple of some numéraire. The Leontief inverse $(I-A)^{-1}$ does the work: it accumulates all rounds of inter-industry cost pass-through, exactly as it accumulates all rounds of intermediate demand in the quantity model.

**Interpreting $v$**: We decompose unit value added into two primary components:

$$v_j = \frac{\text{V001}_j + \text{V003}_j}{x_j}$$

where V001$_j$ is employee compensation and V003$_j$ is gross operating surplus (profit + interest + rent) in sector $j$, and $x_j$ is gross output. In 2024 these two rows account for the bulk of BEA basic-price value added across all 68 A_square sectors.

### Cost-Push Shock

Applying a uniform +10% shock to the compensation component gives a new primary-cost vector:

$$v' = v + \Delta v, \quad \Delta v_j = 0.10 \times \frac{\text{V001}_j}{x_j}$$

The resulting price change is:

$$\Delta p = \Delta v\,(I - A)^{-1}$$

Sectors whose *supply chains* are labor-intensive — not just those with high own-sector labor costs — experience the largest $\Delta p$. An industry that buys intensively from labor-intensive intermediaries inherits their cost increases through the $(I-A)^{-1}$ term.[cite:godley_lavoie_2007]

---

## What the Data Show (2024)

### Pass-Through Is Broad but Unequal

The mean price increase from a +10% wage shock is **+5.24%** across all 68 sectors. But the spread matters: the highest-impact sector (**Warehousing and storage**, +5.36%) exceeds the lowest-impact sector (**Housing**, +5.07%) by about 0.29 percentage points. That spread is modest in percentage-point terms but represents a real structural difference: the gap between top and bottom reflects how differently sectors are embedded in labor-intensive supply chains.

The bar chart below shows the 15 sectors with the largest price increase.

{{chart:study:prices-and-distribution:price_passthrough}}

**Warehousing and storage** leads (+5.356%) with a direct compensation coefficient of 0.646 — meaning 64.6 cents of every dollar of gross output goes directly to employees, before any indirect supply-chain effects. **Computer systems design** (+5.350%) and **Management of companies** (+5.322%) follow closely, both high-compensation service sectors whose costs propagate into nearly every downstream industry that uses professional services as inputs.

At the other end, **Housing** (+5.07%) has the smallest price response: its compensation coefficient is only 0.009 (housing is primarily imputed rent with minimal labor input), so the wage shock barely touches it directly. **Chemical products** (+5.08%) and **Farms** (+5.11%) are also relatively insulated — resource-intensive sectors where energy, raw materials, and capital costs dominate over labor.

The near-uniformity of the shock (~5.1% to ~5.4%) reflects a key theorem: in a fully-integrated economy with pervasive inter-industry trade, a wage shock spreads widely even to sectors that do little direct hiring, because they buy from sectors that do. The spread is not zero, but neither is it extreme — the American I-O structure is dense enough that no sector fully escapes a broad compensation increase.

| Sector | Comp. coeff. | $\Delta p$ (%) |
|---|---|---|
| Warehousing and storage | 0.646 | +5.356 |
| Computer systems design | 0.614 | +5.350 |
| Management of companies | 0.564 | +5.322 |
| Forestry, fishing, and related | 0.529 | +5.320 |
| Securities, commodity contracts | 0.392 | +5.320 |
| Housing | 0.009 | +5.070 |
| Chemical products | 0.138 | +5.080 |
| Farms | 0.078 | +5.106 |
| Petroleum and coal products | 0.035 | +5.113 |

Notice that **Securities, commodity contracts, and investments** — a sector with a relatively modest direct compensation coefficient (0.39) — still experiences a +5.32% price increase. Finance buys heavily from labor-intensive professional services (law, accounting, IT), so the *indirect* channel dominates its own direct labor intensity.

### Economy-Wide Labor Share

The share of value added paid as employee compensation has declined over the 28-year sample period. The line chart below plots the ratio $\text{V001}/(\text{V001}+\text{V003})$ as a percentage for each year 1997–2024.

{{chart:study:prices-and-distribution:labor_share_trend}}

**Key facts:**

- **1997: 57.1%** — Labor enters the sample period with a majority of value added.
- **2000 peak: 59.2%** — The technology boom and tight labor markets pushed the labor share briefly to its sample-period high.
- **Post-2000 secular decline**: After the 2000–01 recession the labor share never recovered its previous peak. Each business cycle left it lower than before.
- **2023 trough: 53.0%** — The post-COVID profit surge pushed the gross-operating-surplus share to its highest level in the sample, compressing labor to its minimum.
- **2024: 53.2%** — A marginal recovery; labor's share remains near historic lows.

The 4-percentage-point decline over 27 years may appear modest, but in dollar terms it is enormous. Total value added in 2024 was approximately $27 trillion; a 4 pp shift represents roughly $1 trillion per year flowing from compensation to profits relative to the 1997 distribution.[cite:shaikh_capitalism_2016]

---

## Caveats and Limitations

**Unit value added as price proxy.** We set $v_j = (\text{V001}_j + \text{V003}_j)/x_j$. BEA basic-price value added also includes taxes less subsidies on production (rows T00TOP, T00SUB, VABAS), which we exclude for clarity. This means our baseline prices do not exactly satisfy the accounting identity $v \cdot \mathbf{1} \equiv 1$, but the *shock analysis* ($\Delta p = \Delta v \cdot L$) remains valid because the price-change computation depends only on the shock vector and the Leontief inverse, not on the level of prices.

**Static model.** The cost-push model assumes firms pass costs forward fully and immediately. In practice, competitive pressure, pricing power, and import competition all mediate the pass-through. The model gives an upper bound on price effects in a closed economy with full cost coverage.

**Labor share is V001/(V001+V003) only.** Taxes on production and imports are omitted from both numerator and denominator. The *level* of the labor share here differs slightly from NIPA labor-share estimates, but the *trend* is robust.

---

## The Takeaway

The price dual teaches two lessons. First, wage cost increases permeate the price system through inter-industry linkages — no sector is fully sheltered. But the degree of exposure varies systematically: labor-intensive service supply chains (warehousing, IT services, professional services) transmit wage shocks more intensively than resource-based or capital-intensive supply chains (petroleum, chemicals, agriculture). Second, the labor share of value added has fallen nearly 4 percentage points since 1997, with the steepest decline occurring in the post-2008 and post-2020 episodes — a structural shift in functional income distribution that the price dual helps explain mechanically.[cite:pasinetti_1981][cite:shaikh_capitalism_2016]

---

## Reproduce This

Download the full replication bundle — data, code, and notebook — at:

**[/api/study/prices-and-distribution/bundle.zip](/api/study/prices-and-distribution/bundle.zip)**

```bash
unzip prices-and-distribution.zip
cd prices-and-distribution
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/prices.csv, outputs/fig_price_passthrough.json,
#          outputs/fig_labor_share_trend.json
```

The script reads `data/A_square_2024.csv`, `data/value_added_2024.csv`, `data/total_output_2024.csv`, `data/labor_share.csv`, and `data/sector_names.csv`. It uses only `numpy`, `pandas`, and `plotly`. An `analysis.ipynb` notebook mirrors every step.

[cite:miller_blair_2022][cite:pasinetti_1981][cite:godley_lavoie_2007][cite:shaikh_capitalism_2016]
