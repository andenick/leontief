---
title: "Technology vs Demand: Decomposing Output Change, 1997–2024"
order: 7
difficulty: intermediate
summary: "Structural decomposition analysis (SDA) splits the $39.7 trillion rise in U.S. gross output between 1997 and 2024 into a final-demand effect and a technology effect. Demand growth accounts for more than 100 percent of the total; technology change — captured by shifts in the Leontief inverse L — subtracted slightly from output, with large opposing movements across sectors."
---

## The Question

Between 1997 and 2024, U.S. gross output rose by roughly $39.7 trillion in current dollars. How much of that increase was driven by changes in *what consumers, firms, and government bought* (the final-demand effect), and how much by changes in *how industries produce* (the technology effect)? The two forces can reinforce or offset each other, and their relative weight tells us something fundamental about the character of structural change in the American economy.[cite:miller_blair_2009_ch13]

---

## The Method

Structural decomposition analysis (SDA) works directly from the Leontief output identity:

$$x = Lf$$

where $x$ is the gross-output vector, $L = (I - A)^{-1}$ is the Leontief inverse, and $f$ is the vector of final demands (aggregated across all demand categories).

Between periods 0 (1997) and 1 (2024), both $L$ and $f$ change. Writing $\Delta L = L^1 - L^0$ and $\Delta f = f^1 - f^0$, the change in output satisfies:

$$\Delta x = L^1 \Delta f \;+\; \Delta L\, f^0 \;+\; \Delta L\, \Delta f$$

The three terms are, respectively:[cite:dietzenbacher_los_1998]

- **Final-demand effect** $L^1 \Delta f$: what would output change be if only final demand shifted, holding the 2024 technology matrix fixed?
- **Technology effect** $\Delta L\, f^0$: what would output change be if only the input-output structure shifted, holding 1997 final demand fixed?
- **Interaction effect** $\Delta L\, \Delta f$: the joint contribution of simultaneous changes in both.

This is the "three-term" or "first-polar" SDA of Dietzenbacher and Los (1998). It uses $L^1$ (the end-period inverse) to weight the demand effect, so the interaction term is allocated to the demand side if one prefers the two-term decomposition. We report all three terms separately for transparency.

### Alignment

The BEA final-demand (FD) table for each year covers 70 sector rows. The Leontief inverse $L$ covers 71 sectors. The three sectors present in $L$ but absent from the FD table are retail detail rows — `441` (Motor vehicle and parts dealers), `445` (Food and beverage stores), and `452` (General merchandise stores) — which receive $f = 0$ in both periods. Two FD rows (`Other`, `Used`) have no counterpart in $L$ and are dropped. The net working intersection is 68 sectors; the remaining 3 receive zero final demand consistently in both periods, so the alignment has no material effect on the decomposition.

---

## What the Data Show

### Aggregate Decomposition

{{chart:study:structural-decomposition:sda_contributions}}

The three-term decomposition of the $39.67 trillion total output change yields:

| Effect | Contribution ($trillion) | Share of total |
|---|---|---|
| Final-demand effect ($L^1 \Delta f$) | +$41.77T | +105.3% |
| Technology effect ($\Delta L\, f^0$) | −$0.88T | −2.2% |
| Interaction effect ($\Delta L\, \Delta f$) | −$1.22T | −3.1% |
| **Total** | **+$39.67T** | **100%** |

The demand effect overshoots the total because the technology and interaction effects partially offset it. Reading technology and interaction together as "technology-related effects," they sum to roughly −$2.10 trillion, or about −5.3 percent of the total. The American economy's output roughly quadrupled in nominal terms from 1997 to 2024; nearly all of that expansion was driven by more final spending, not by changes in production structure.

### Technology Effect by Sector

The technology effect is not zero at the sector level even though its aggregate is small. Large positive and negative contributions cancel nearly perfectly in the aggregate. The sectors where technology change mattered most (by absolute value of the technology-effect term $\Delta L\, f^0$):

| Sector | Technology effect ($millions) | Direction |
|---|---|---|
| Computer and electronic products | −$203,690M | Negative (sector became more efficient) |
| Wholesale trade | +$139,016M | Positive (sector deepened upstream role) |
| Other real estate | +$118,758M | Positive |
| Textile mills and textile product mills | −$115,344M | Negative |
| Insurance carriers and related activities | +$111,148M | Positive |
| Data processing, internet publishing | +$104,980M | Positive |
| Broadcasting and telecommunications | −$98,224M | Negative |

**Computers and electronics** show the largest negative technology effect: the Leontief inverse coefficients for this sector shrank substantially between 1997 and 2024, reflecting dramatic productivity growth in semiconductor and electronics manufacturing — you need far fewer upstream-input dollars to produce a dollar of output than in 1997. **Wholesale trade** and **Other real estate** show the opposite: their role as intermediate input providers deepened, increasing their column sums in $L$.

**Textiles** had a large negative technology effect, consistent with the collapse of domestic intermediate-goods supply chains in apparel and textile production since the mid-1990s. **Broadcasting and telecommunications** also contracted in input-intensity terms, reflecting the shift from capital-intensive analog networks toward software-driven communication.

---

## The Takeaway

Final demand growth was the overwhelming engine of U.S. output expansion from 1997 to 2024. The technology effect was economically small in aggregate but conceals a rich pattern of structural change: manufacturing sectors like computers and textiles shed input-intensity while service sectors like wholesale trade, real estate, and data processing deepened their upstream role. The three-term SDA makes these offsetting movements transparent in a way that aggregate GDP accounting cannot.

The interaction term (−$1.22T) reflects the fact that the sectors where final demand grew the most were also, on net, the sectors where the Leontief inverse contracted slightly — consistent with the story that demand shifted toward services, which became somewhat leaner in intermediate-input use over the period.[cite:dietzenbacher_los_1998]

---

## Reproduce This

Download the full replication bundle at:

**[/api/study/structural-decomposition/bundle.zip](/api/study/structural-decomposition/bundle.zip)**

```bash
unzip leontief_study_structural-decomposition.zip
cd code
pip install -r requirements.txt
python analysis.py
# Outputs: outputs/sda.csv, outputs/fig_sda_contributions.json
```

The script reads `data/L_1997.csv`, `data/L_2024.csv`, `data/fd_1997.csv`, `data/fd_2024.csv`, and `data/sector_names.csv`. It implements the three-term SDA using only NumPy linear algebra — no scipy, no networkx. An `analysis.ipynb` notebook mirrors every step interactively.

[cite:miller_blair_2009_ch13][cite:dietzenbacher_los_1998]
