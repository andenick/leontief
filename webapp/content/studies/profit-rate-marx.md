---
title: "A Marxian Profit Rate from the Input-Output Table"
order: 10
difficulty: advanced
summary: "I-O tables allow classical economists' categories — labor values, variable capital, surplus value, and the aggregate profit rate — to be computed directly from BEA data. Using flow proxies (no fixed-capital stock is available), the aggregate profit-rate proxy r = S/(C+V) rose from 0.287 in 1997 to 0.341 in 2024, while the correlation between labor values and price proxies across sectors is moderate (r ≈ 0.48), consistent with the classical claim that prices gravitate around values but diverge due to equalized profit rates."
---

## The Question

Marx's *Capital* argues that the prices of production emerge from a redistribution of surplus value across sectors with different organic compositions of capital — and that the aggregate profit rate tends to fall as the economy grows more capital-intensive. Can we construct these classical categories directly from modern input-output data?[cite:shaikh_capitalism_2016]

The answer is yes, with important qualifications. The BEA Use table provides three of the four Marxian aggregates directly: V (variable capital, as employee compensation V001), S (surplus value, as gross operating surplus V003), and the intermediate-input structure that proxies for C (constant capital). What it *cannot* provide is the fixed-capital stock — the proper denominator for a stock-based profit rate. We proceed transparently with flow proxies and are explicit about what they can and cannot say.[cite:pasinetti_1981]

---

## The Method

### Labor Values

Following Pasinetti (1981) and the input-output value theory tradition, labor values are computed as vertically integrated labor coefficients:

$$\lambda = l\,(I - A)^{-1}$$

where $l_j = \text{V001}_j / x_j$ is direct compensation per unit gross output in sector $j$ — a proxy for the direct living-labor content of production. The Leontief inverse $(I-A)^{-1}$ accumulates all indirect labor embodied through the supply chain: to produce one unit of sector $j$'s output you need direct labor $l_j$ *plus* the labor embodied in all intermediate inputs, which themselves require labor, and so on.[cite:pasinetti_1981]

**What $l$ proxies:** In Marxian theory, living labor should be measured in hours. Here we use compensation as a scalar — a reasonable proxy under the assumption that relative wage rates roughly reflect relative skill and effort intensities, so that $l_j$ is proportional to labor-time per unit output across sectors. This is a standard maintained assumption in empirical value studies.

### Aggregate Profit Rate — Flow Proxy

The classical profit rate is $r = S/(C+V)$, where:

- $V = \sum_j \text{V001}_j$ — total compensation (variable capital)
- $S = \sum_j \text{V003}_j$ — total gross operating surplus (proxy for surplus value)
- $C = \sum_j \text{T005}_j$ — total intermediate inputs from the BEA Use table (constant capital **flow proxy**)

**Critical caveat:** In Marx's framework, $C$ is a *stock* — the value of machinery, buildings, and raw-material inventories advanced at the start of the production period. The BEA I-O table does not contain capital-stock data. We use the *flow* of intermediate inputs (T005 row of the Use table) as a proxy for the turnover component of constant capital. This overstates the denominator relative to a proper stock-based measure, so our $r$ levels are not comparable to stock-based profit-rate estimates in the empirical Marxist literature (e.g., Basu–Manolakos, Shaikh–Tonak). The **trend** in $r$ over time is informative, because the bias is consistent across years.[cite:shaikh_capitalism_2016]

For the annual trend we compute these aggregates from the parquet cache for each year 1997–2024, using each year's own A_square and VA tables.

### Value vs. Price Comparison

For the 2024 cross-section we compare, sector by sector, normalized labor values $\tilde{\lambda}_j = \lambda_j / \bar{\lambda}$ with a market-price proxy $\tilde{p}_j = ((\text{V001}_j + \text{V003}_j)/x_j) / \overline{(\cdot)}$, both normalized to mean = 1. The *transformation problem* predicts that $\tilde{p}_j \neq \tilde{\lambda}_j$ precisely because profit rates are equalized across sectors with different organic compositions — sectors with above-average capital intensity receive above-value prices; labor-intensive sectors receive below-value prices.

---

## What the Data Show

### Labor Values, 2024

Labor values cluster in a narrow band across sectors, reflecting the deep integration of the American supply network. The range of $\lambda_j$ runs from approximately 7 to 15 (in compensation units per unit gross output), with service sectors systematically at the high end. The top sectors by embodied labor content are those whose *supply chains* are labor-intensive, not necessarily their own operations:

| Sector | $\lambda_j$ |
|---|---|
| Insurance carriers and related activities | 14.69 |
| Nursing and residential care facilities | 14.21 |
| Legal services | 14.20 |
| Ambulatory health care services | 14.17 |
| Computer systems design | 14.10 |

The highest-$\lambda$ sectors are professional and personal services with long, labor-intensive upstream supply chains. Manufacturing sectors tend to have lower labor values because their supply chains include resource and capital-intensive intermediates (petroleum, metals, chemicals) that dilute the labor content.

### Value vs. Price Proxy

The scatter below plots normalized labor values (x-axis) against normalized price proxies (y-axis) for all 68 sectors in 2024. The dotted diagonal is the labor theory of value (LTV) prediction: prices should equal values. Color indicates the percentage deviation.

{{chart:study:profit-rate-marx:value_price_deviation}}

The correlation between labor values and price proxies is **0.48** across sectors — positive and statistically meaningful, consistent with the broad classical claim that labor values anchor prices, but far from the perfect correspondence the LTV naively implies. This is exactly what transformation-problem theory predicts: prices of production systematically deviate from values in proportion to each sector's organic composition of capital.

Sectors most **above** the LTV diagonal (price $\gg$ value): **Housing** (+51%), **Legal services** (+42%), **Forestry** (+38%), **Computer and electronic products** (+37%). These sectors earn returns well above what their labor content alone would predict — likely reflecting either monopoly rents (housing), high-skill premia (legal services), or capital intensity (electronics) that lifts their price above simple labor-time accounting.

Sectors most **below** the LTV diagonal (price $\ll$ value): **Funds, trusts, and other financial vehicles** (−80%), **Motor vehicles** (−50%), **Food and beverage** (−48%), **Petroleum and coal products** (−41%). The extreme undervaluation of financial vehicles partly reflects the fact that GOS in finance is volatile and hard to compare with labor-value measures; motor vehicles and food are highly competitive, high-volume sectors where margins are thin.

### The Profit-Rate Proxy Trend, 1997–2024

{{chart:study:profit-rate-marx:profit_rate_trend}}

The aggregate flow-based profit rate $r = S/(C+V)$ rose from **0.287 in 1997** to **0.341 in 2024** — an increase of 5.4 percentage points over 27 years, the opposite of the classical law of the falling rate of profit (LTRPF) as stated by Marx. Several structural features explain this:

| Period | Trend | Interpretation |
|---|---|---|
| 1997–2000 | Falling (0.287 → 0.264) | Dot-com boom raised V faster than S |
| 2001–2008 | Rising (0.271 → 0.284) | Post-recession profit recovery; wage suppression |
| 2009–2010 | Sharp rise (0.284 → 0.319) | GFC crashed intermediate-input costs (C) faster than S |
| 2011–2019 | Stable (0.309–0.315) | Plateau with modest fluctuations |
| 2020 | Jump (0.334) | COVID: C (intermediate flow) collapsed as output fell |
| 2021–2024 | High plateau (0.322–0.341) | Sustained profit surge; wage share compressed |

**Caution on levels:** The measured $r \approx 0.28$–$0.34$ is not the "true" Marxian profit rate. A stock-based denominator (fixed capital + inventories) is far larger than the intermediate-input flow we use here, which would push the level of $r$ down substantially — closer to the 5–10% range reported in the empirical Marxist literature. Our flow-proxy denominator omits fixed capital entirely, so the level is upward-biased. The *trend* — a modest rise over the period — is likely qualitatively robust to the choice of C proxy.[cite:shaikh_capitalism_2016]

The rising trend contradicts the LTRPF naively applied to this data. This is consistent with findings in the empirical literature: the LTRPF is a long-run tendency, not a year-by-year law, and can be offset for decades by countervailing tendencies (rising rate of exploitation, cheapening of constant capital, globalization of production). Shaikh (2016) documents similar rises in the post-1982 era for the US economy before the longer-run tendency reasserts itself.

---

## Honest Accounting of Proxy Limitations

| What we need | What we use | Bias |
|---|---|---|
| Living labor in hours | Compensation per unit output | Assumes relative wages ≈ relative labor intensity |
| Fixed capital stock (C) | Intermediate-input flow (T005) | C understated → r overstated (level bias) |
| Prices of production | VA-per-unit proxy | Incomplete: taxes/subsidies excluded |
| Aggregate surplus value | V003 (gross operating surplus) | Includes depreciation, not net surplus |

None of these biases affect the primary analytical claims (pass-through pattern, labor-share trend) in the companion study on cost-push prices. Here they affect the level of $r$ but are consistent across years, preserving trend validity.[cite:pasinetti_1981][cite:shaikh_capitalism_2016]

---

## The Takeaway

The BEA I-O tables are sufficient to construct the skeleton of Marxian value analysis: labor values via $(I-A)^{-1}$, the tripartite decomposition $V$/$S$/$C$, and the aggregate profit rate. The cross-sectional correlation between labor values and price proxies is moderate (0.48), consistent with the transformation problem and the equalization of profit rates across sectors with different organic compositions. The aggregate profit-rate proxy has *risen* over 1997–2024, driven mainly by falling labor share and post-crisis collapses in intermediate-input costs. Whether this contradicts the LTRPF or merely represents a medium-run offsetting tendency depends on the theoretical framework — and on the proper capital-stock data that the I-O system alone cannot supply.[cite:shaikh_capitalism_2016]

---

## Reproduce This

Download the full replication bundle at:

**[/api/study/profit-rate-marx/bundle.zip](/api/study/profit-rate-marx/bundle.zip)**

```bash
unzip profit-rate-marx.zip
cd profit-rate-marx
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/marx.csv, outputs/fig_profit_rate_trend.json,
#          outputs/fig_value_price_deviation.json
```

The script reads `data/A_square_2024.csv`, `data/value_added_2024.csv`, `data/total_output_2024.csv`, `data/profit_rate_timeseries.csv`, and `data/sector_names.csv`. It uses only `numpy`, `pandas`, and `plotly`. An `analysis.ipynb` notebook mirrors every step.

[cite:shaikh_capitalism_2016][cite:pasinetti_1981]
