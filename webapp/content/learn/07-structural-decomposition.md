---
title: Structural Decomposition Analysis
order: 7
summary: How to split a change in total output between technology shifts and demand shifts — the SDA method, illustrated with U.S. manufacturing, 1997–2024.
---

## What Changed, and Why?

Between 1997 and 2024 the U.S. economy went through a visible transformation: manufacturing's share of total output shrank while services, information, and finance expanded. But when we see output in a sector rise or fall, we face an immediate puzzle — *why*? Two very different forces can produce the same observed change:

1. **Technology changed.** Industries rewrote their recipes — they bought fewer inputs from one supplier, more from another, or automated steps that once required intermediate goods. This is captured in the [technical coefficients](/glossary#technical-coefficients) matrix $A$, and therefore in the [Leontief inverse](/glossary#leontief-inverse) $L = (I - A)^{-1}$.

2. **Final demand changed.** Households, government, and exporters simply shifted what they wanted to buy. This is captured in the [final demand](/glossary#final-demand) vector $f$.

**Structural Decomposition Analysis** (SDA) is the method that attributes a historical change in output $\Delta x$ to each of these forces separately [cite:dietzenbacher_los_1998][cite:miller_blair_2009_ch13].

## The Basic Identity

Recall the core I-O equation: $x = Lf$. For two points in time — call them period 0 (1997) and period 1 (2024) — we have:

$$x^1 = L^1 f^1 \qquad x^0 = L^0 f^0$$

The total change is $\Delta x = x^1 - x^0$. We want to split this into a piece driven by $\Delta L = L^1 - L^0$ (the technology effect) and a piece driven by $\Delta f = f^1 - f^0$ (the demand effect). Starting from $\Delta x = L^1 f^1 - L^0 f^0$ and adding and subtracting $L^1 f^0$ gives an **exact two-term decomposition**:

$$\Delta x = \underbrace{L^1 \Delta f}_{\text{demand effect}} + \underbrace{\Delta L\, f^0}_{\text{technology effect}}$$

There is no separate residual: the two terms reproduce $\Delta x$ exactly. Each term has a clear economic reading:

| Term | Name | Interpretation |
|------|------|----------------|
| $L^1 \Delta f$ | Demand effect | How much output changes from the shift in demand from $f^0$ to $f^1$, evaluated at period-1 technology $L^1$ |
| $\Delta L\, f^0$ | Technology effect | How much output changes from the evolution of technology from $L^0$ to $L^1$, evaluated at period-0 demand $f^0$ |

## The Index-Number Problem and Polar Decompositions

The two-term split above is not unique. Adding and subtracting $L^0 f^1$ instead yields the equally exact **polar alternate**:

$$\Delta x = L^0 \Delta f + \Delta L\, f^1$$

which evaluates the demand effect at period-0 technology and the technology effect at period-1 demand. The two decompositions give different answers, just as a price index using old quantities differs from one using new quantities. This is the familiar [index-number problem](/glossary#index-number-problem).

Dietzenbacher and Los (1998) showed that the most defensible approach is to **average over the two polar decompositions** [cite:dietzenbacher_los_1998]. Instead of choosing one base year, compute both exact two-term forms and take the arithmetic mean of the demand and technology pieces:

$$\Delta x_{\text{demand}} = \tfrac{1}{2}\!\left(L^0 \Delta f + L^1 \Delta f\right)$$

$$\Delta x_{\text{technology}} = \tfrac{1}{2}\!\left(\Delta L\, f^0 + \Delta L\, f^1\right)$$

These two averaged terms still sum exactly to $\Delta x$ (each polar form does, so their average does too). The averaging has an intuitive appeal: it weights each endpoint equally rather than privileging either 1997 or 2024 as the reference year. For an economy spanning 28 years and 71 sectors, this symmetry matters [cite:dietzenbacher_los_1998].

## Manufacturing Decline: 1997 to 2024

The chart below tracks deindustrialization across the full 28-year horizon covered by this dataset.

{{chart:structural_trend:deindustrialization}}

SDA applied to U.S. manufacturing over this period typically reveals that *both* forces operated, but in different proportions across sub-industries. For durable goods manufacturing:

- **Demand** shifted toward services, digital goods, and imports — a genuine preference and trade-pattern story.
- **Technology** also changed: manufacturing became more capital- and software-intensive, reducing intermediate purchases from other domestic manufacturers per dollar of output.

The relative size of these two channels is an empirical question — and answering it requires doing the computation rather than assuming an answer.

## Try It

```python
import numpy as np

def sda_polar(L0, L1, f0, f1):
    """Symmetric (averaged) SDA into demand and technology effects."""
    delta_f = f1 - f0
    delta_L = L1 - L0
    demand_effect = 0.5 * (L0 @ delta_f + L1 @ delta_f)
    tech_effect   = 0.5 * (delta_L @ f0 + delta_L @ f1)
    return demand_effect, tech_effect

# L0, L1: numpy arrays (71 x 71 Leontief inverses for 1997 and 2024)
# f0, f1: numpy arrays (71,) final demand vectors
demand, tech = sda_polar(L0, L1, f0, f1)
check = demand + tech  # should equal L1 @ f1 - L0 @ f0
```

The function above takes fewer than 10 lines of NumPy and produces a 71-vector of attributed output changes — one entry per sector [cite:miller_blair_2009_ch13].

## Caveats and Regime Breaks

One important caution: the BEA switched from the Standard Industrial Classification (SIC) to the North American Industry Classification System (NAICS) in 1997, creating a structural break that makes any comparison *before* 1997 methodologically fraught. Within the 1997–2024 window used here, the 71-sector annual summary classification is held consistent — making it the cleanest available window for SDA [cite:bea_concepts_2009]. Annual I-O tables at this 71-sector level only began with the 2007 comprehensive revision; for 1997–2006, the BEA published benchmark tables (1997 and 2002), and annual figures were interpolated.

## Where Next

- **Tutorial 08** — [The Economy as a Network](/learn/08-the-economy-as-a-network): after decomposing *changes*, the next step is to ask which industries sit at the structural core of the economy and why shocks to them propagate so widely.
- **Deep dive** — [Structural Decomposition Study](/studies/structural-decomposition): worked examples on the full 1997–2024 panel with sector-level attribution charts.

## Further reading

- Miller &amp; Blair (2009), ch. 13 — structural decomposition analysis and the polar/averaged decomposition forms. [cite:miller_blair_2009_ch13]
- Dietzenbacher &amp; Los (1998) — the canonical analysis of SDA's index-number sensitivity and the average-of-polar-forms recommendation. [cite:dietzenbacher_los_1998]
