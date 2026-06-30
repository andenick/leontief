---
title: "The Long Decline of U.S. Manufacturing, 1997–2024"
order: 4
difficulty: intermediate
summary: "U.S. manufacturing's share of GDP fell from 16.5% in 1997 to 10.0% in 2024 — a 6.5 percentage-point drop, or 39% of its starting weight. Gross output share fell even more sharply, from 36.9% to 19.8%. This study traces the trajectory, marks the crisis inflection points, and connects the decline to the structural facts visible in the I-O tables."
---

## The Question

Every year from 1997 to 2024 the BEA publishes Use tables that record — in billions of dollars — who buys what from whom. Across those 28 tables, one structural fact is unmistakable: manufacturing shrinks. Not in absolute terms (manufacturing output has grown) but as a *share* of total economic activity. The economy around it grew faster.

Deindustrialization is the word economists use for this relative decline.[cite:bea_concepts_2009] Understanding it quantitatively is a prerequisite for any I-O analysis that spans multiple years: if manufacturing's intermediate linkages were as heavy in 2024 as in 1997, the average output multiplier would be much higher, the structure of key sectors very different, and the HEM ranking rearranged. The decline is not a background fact — it is written into the matrices themselves.

---

## Two Measures of Manufacturing's Weight

The BEA's national accounts provide two conceptually distinct measures:[cite:dietzenbacher_los_1998]

**Value-added share of GDP** measures manufacturing's contribution to national income — wages, profits, and net taxes on production, after subtracting intermediate inputs. This is the "thin" measure: it strips out the purchased materials that flow through factories and counts only what manufacturing *creates*.

**Gross output share** is the broader measure: manufacturing's total revenues from production as a share of total economy-wide revenues. It includes all intermediate inputs purchased from other sectors plus value added. The gross output share is much larger than the VA share, and it captures manufacturing's role as a *buyer* in intermediate markets — the linkages that drive output multipliers.

Both are shown below.

{{chart:study:deindustrialization:deindustrialization_trend}}

---

## The Numbers

In 1997 manufacturing accounted for **16.5%** of GDP (value added) and **36.9%** of gross output. By 2024 those figures had fallen to **10.0%** and **19.8%** respectively:

| Measure | 1997 | 2024 | Drop | Relative decline |
|---|---|---|---|---|
| VA share of GDP | 16.5% | 10.0% | −6.5 pp | −39% |
| Gross output share | 36.9% | 19.8% | −17.1 pp | −46% |

The output-share decline is nearly three times as large in percentage-point terms as the VA-share decline. This asymmetry reflects the import penetration story: as U.S. manufacturers outsourced intermediate production — components, subassemblies, raw materials — the domestic intermediate-goods network that generated gross output share thinned out, even as value-added per unit of domestic output did not fall proportionately.

Two inflection points stand out in the chart. The 2008–09 financial crisis and its immediate aftermath produced the sharpest single-year declines on record: the VA share fell from 13.0% in 2007 to 11.9% in 2008 and to 11.9% again in 2009 (gross output share dropped from 30.2% to 26.9% in a single year). The recovery from 2010–2012 was partial and brief; the long trend reasserted itself.

The COVID shock of 2020 produced a second dip — VA share fell from 10.7% in 2019 to 10.2% in 2020, gross output from 22.8% to 21.2% — followed by a brief rebound in 2021–2022 as goods demand surged. By 2024 both series had resumed their declining trajectory, with the gross output share at its sample-period minimum.

---

## Why Both Measures Matter for I-O Analysis

The multiplier decline documented in the [multipliers study](/studies/multipliers-explained) is not independent of this chart. In the I-O framework, the mean output multiplier equals the grand mean of $L = (I - A)^{-1}$. A more manufacturing-intensive economy — where many sectors buy from many other domestic sectors — has a denser, higher-valued $L$. Deindustrialization thins $L$ by removing the heavy intermediate flows that manufacturing generates.

The gross output share is the more relevant measure here: it tracks not just what manufacturing produces but how deeply it is embedded as an *intermediate-goods buyer*. A 17-percentage-point shrinkage in that share, sustained over 28 years, is consistent with the 0.15-point decline in the mean output multiplier observed from 2008 to 2024.

For structural decomposition — see the upcoming study on growth-accounting with I-O matrices — deindustrialization enters through changes in both the coefficient matrix $A$ and the final-demand composition. Separating the two contributions requires exactly the kind of two-date comparison the Leontief data makes straightforward.[cite:dietzenbacher_los_1998]

---

## The Takeaway

Manufacturing's decline in U.S. GDP share is not a cyclical blip or a measurement artifact. It is a structural shift that runs from 1997 through 2024 with only brief, crisis-induced interruptions. The gross output share — down 17 percentage points over 28 years — captures more of the economic significance than the often-cited VA share: it reflects the thinning of intermediate linkages that is the supply-chain face of deindustrialization.

For the I-O analyst, this matters practically: a model calibrated to 1997 coefficients will overstate the average multiplier by roughly 8–10% if applied to 2024 final demand. The structure of the American economy has changed — and the Use tables record every step of that change.

---

## Reproduce This

Download the full replication bundle at:

**[/api/study/deindustrialization/bundle.zip](/api/study/deindustrialization/bundle.zip)**

```bash
unzip deindustrialization.zip
cd deindustrialization
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/deindustrialization.csv, outputs/fig_deindustrialization_trend.json
```

The script reads `data/deindustrialization.csv` (exported from the BEA-verified `deindustrialization_1997_2024.xlsx`). An `analysis.ipynb` notebook mirrors every step interactively.

[cite:bea_concepts_2009][cite:dietzenbacher_los_1998]
