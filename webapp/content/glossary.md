---
title: Glossary
summary: Definitions of input-output terms used throughout Leontief, from A matrix to vertically integrated labor.
order: 30
---

A reference guide to the terms used in input-output analysis. Entries are alphabetical; cross-references are noted where terms build on one another.

---

### A Matrix (Direct Requirements Matrix / Technical Coefficients)

The core object of input-output analysis. Each element $a_{ij}$ gives the amount of commodity $i$ required as an intermediate input to produce one dollar of output in industry $j$: $a_{ij} = z_{ij} / x_j$, where $z_{ij}$ is intermediate use and $x_j$ is total industry output. The A matrix encodes the technology of production and is derived from the [Use table](#use-table). See also: [Leontief inverse](#leontief-inverse), [Direct requirements](#direct-requirements).

### Backward Linkage

A measure of how intensively a sector purchases inputs from the rest of the economy. A sector with strong backward linkages generates significant upstream activity when its output expands. Formally captured by [Rasmussen indices](#rasmussen-indices): the backward linkage (power of dispersion) for sector $j$ is the normalized column sum of the [Leontief inverse](#leontief-inverse). Compare: [Forward linkage](#forward-linkage).

### BEA Summary Classification

The Bureau of Economic Analysis grouping of the U.S. economy into 71 industries used in the annual Supply-Use accounts. The classification is based on the North American Industry Classification System (NAICS) and has been stable since the first NAICS-era benchmark in 1997, making it the standard framework for time-series analysis of U.S. I-O data. Leontief uses the BEA Summary classification exclusively.

### Commodity vs. Industry

In BEA accounting, a **commodity** is a good or service defined by what it is, while an **industry** is defined by the establishment that produces it. An industry can produce multiple commodities (secondary products), and a commodity can be produced by multiple industries. The [Use table](#use-table) has commodities in rows and industries in columns; the [Supply table](#supply-table) maps which industries produce which commodities. The distinction matters because the [A matrix](#a-matrix-direct-requirements-matrix--technical-coefficients) derived from the Use table is commodity-by-industry, not square.

### Cost-Push Price Model

A dual to the quantity model. If value-added coefficients change (e.g., wages rise), the price model traces how cost increases propagate forward through production chains. The price vector satisfies $p' = v'(I - A)^{-1}$, where $v'$ is the vector of value-added coefficients per unit of output. This is the transpose of the [Leontief inverse](#leontief-inverse) applied to cost shocks rather than demand shocks. See also: [Leontief inverse](#leontief-inverse).

### Direct Requirements

The immediate, first-round input needs of a sector: the elements of the [A matrix](#a-matrix-direct-requirements-matrix--technical-coefficients). If auto manufacturing requires $a_{steel, auto} = 0.08$, then $0.08 of steel is needed directly per dollar of auto output. Direct requirements ignore the inputs needed to produce the steel itself — that full accounting is captured by the [Leontief inverse](#leontief-inverse) (total requirements). Compare: [Total requirements](#total-requirements).

### Final Demand

The portion of output that goes to end-users rather than further production: personal consumption expenditure, private fixed investment, changes in inventories, exports, and federal and state/local government purchases. In the standard I-O identity, total output equals intermediate demand plus final demand: $x = Ax + f$, which rearranges to $x = (I-A)^{-1}f = Lf$. The **FD** matrix on Leontief contains the final demand columns extracted from the BEA Use table (19 F-code categories).

### Forward Linkage

A measure of how intensively a sector supplies inputs to the rest of the economy. A sector with strong forward linkages sees its output used widely as an intermediate input; disruptions to it propagate broadly downstream. Formally, the forward linkage (sensitivity of dispersion) for sector $i$ is the normalized row sum of the Leontief inverse. Compare: [Backward linkage](#backward-linkage). See also: [Rasmussen indices](#rasmussen-indices), [Hypothetical extraction](#hypothetical-extraction-hem).

### Ghosh Inverse

The supply-side counterpart to the [Leontief inverse](#leontief-inverse). Where L answers "how much total output is needed to satisfy a unit of final demand?", the Ghosh inverse answers "how much total output is generated if primary inputs to sector $j$ expand by one unit?" It is defined as $G = (I - B)^{-1}$ where $B$ is the output-coefficient matrix (the row-normalized version of the intermediate flow matrix). The Ghosh model is most useful for analyzing supply shocks and [forward linkages](#forward-linkage).

### Hypothetical Extraction (HEM)

A method for measuring the total importance of a sector by asking what would happen if it were removed from the economy entirely — its row and column in A set to zero. The counterfactual output vector $\bar{x} = (I - \bar{A})^{-1}f$ gives what the rest of the economy could produce without sector $k$. The difference $x - \bar{x}$ measures the total linkage of sector $k$, combining both its [backward](#backward-linkage) and [forward](#forward-linkage) effects into a single quantity. This avoids the double-counting problems that can affect simple Rasmussen indices.

### Industry vs. Commodity

See: [Commodity vs. Industry](#commodity-vs-industry).

### Key Sector

A sector that scores above average on both [backward linkage](#backward-linkage) and [forward linkage](#forward-linkage) by the [Rasmussen](#rasmussen-indices) criterion — i.e., both its power of dispersion and its sensitivity of dispersion exceed 1. Key sectors are economically central in both directions: they depend heavily on the rest of the economy and are heavily depended upon by it. Typical key sectors include heavy manufacturing, energy, and transportation.

### Leontief Inverse (Total Requirements Matrix)

The central object of input-output analysis, defined as $L = (I - A)^{-1}$. Each element $l_{ij}$ gives the total output of sector $i$ required — directly and through all indirect supply-chain rounds — to deliver one unit of sector $j$'s output to final demand. The Leontief inverse can be expressed as a convergent power series: $L = I + A + A^2 + A^3 + \cdots$, where the first term is direct output, the second is first-round indirect requirements, and so on. Column sums of L give [output multipliers](#multiplier-output--income--employment). Named after Wassily Leontief.[cite:leontief_1936][cite:miller_blair_2022]

### Make Table

See: [Supply table](#supply-table). (Older BEA terminology; "Supply table" is now standard.)

### Multiplier (Output / Income / Employment, Type I / Type II)

**Output multiplier** for sector $j$: $m_j = \sum_i l_{ij}$, the column sum of the [Leontief inverse](#leontief-inverse). It gives the total economy-wide output generated per dollar of final demand for sector $j$.

**Income multiplier**: $m_j^v = v'L$ where $v$ is the vector of value-added (or wage) coefficients per unit of output. Gives the total income generated per dollar of demand.

**Employment multiplier**: analogous to income, using employment per unit of output rather than wages.

**Type I multiplier** uses the open model — households are final demand, not producers. **Type II multiplier** closes the model with respect to households, adding a row and column for household consumption and labor income, which amplifies the multiplier by adding an induced consumption effect. Type II multipliers are larger and more appropriate for long-run analysis; Type I multipliers are more conservative and preferred for short-run or policy work.

### NAICS

The North American Industry Classification System. Replaced the Standard Industrial Classification (SIC) beginning with the 1997 BEA benchmark I-O accounts. The transition from SIC to NAICS is the largest single methodological break in U.S. I-O history; pre- and post-1997 data are not directly comparable at the sector level. All Leontief data uses NAICS classification.

### Rasmussen Indices

Standardized measures of [backward](#backward-linkage) and [forward](#forward-linkage) linkage developed by Rasmussen (1956) and elaborated in Miller and Blair. The **power of dispersion** (backward linkage index) for sector $j$ is the average column element of L divided by the grand mean of all L elements: $U_j^b = \frac{(1/n)\sum_i l_{ij}}{(1/n^2)\sum_i\sum_j l_{ij}}$. The **sensitivity of dispersion** (forward linkage index) is the analogous row-normalized quantity $U_i^f$. Values above 1 indicate above-average linkage strength. See also: [Key sector](#key-sector).[cite:miller_blair_2022]

### Sector (BEA Summary)

See: [BEA Summary Classification](#bea-summary-classification). In Leontief, "sector" always means one of the 71 BEA Summary industries unless specified otherwise.

### Structural Decomposition Analysis (SDA)

A technique for attributing the change in total output between two periods to its sources: changes in technology (the A matrix) versus changes in final demand (the f vector). The standard two-polar decomposition expresses $\Delta x = \frac{1}{2}[L^0 \Delta f + \Delta L \cdot f^1] + \frac{1}{2}[L^1 \Delta f + \Delta L \cdot f^0]$, averaging two polar forms to avoid path-dependence. SDA is more powerful than simple growth accounting because it can attribute output changes at the sector level to specific final demand categories or specific technology changes.[cite:dietzenbacher_los_1998]

### Supply Table (Make Table)

One of the two foundational BEA tables. The Supply table records, for each commodity and each industry, the value of that commodity produced by that industry. It shows that industries often produce goods outside their primary classification (secondary products). Together with the [Use table](#use-table), the Supply table allows construction of either commodity-by-commodity or industry-by-industry total-requirements tables. The BEA publishes Supply tables at the 71-sector summary level annually. Older BEA publications call this the "Make" table.[cite:bea_concepts_2009]

### Technical Coefficients

See: [A matrix](#a-matrix-direct-requirements-matrix--technical-coefficients). The term "technical" reflects the assumption that input proportions are determined by technology and are fixed in the short run — a key assumption of the standard Leontief model.

### Total Requirements

The full direct-plus-indirect input needs of a sector, as captured by the [Leontief inverse](#leontief-inverse) $L = (I-A)^{-1}$. An element $l_{ij}$ includes not just the direct inputs from sector $i$ to sector $j$, but also the inputs needed to produce those inputs, and the inputs needed to produce those, and so on through all supply-chain rounds. Compare: [Direct requirements](#direct-requirements).

### Use Table

One of the two foundational BEA tables. The Use table records, for each commodity and each industry, the value of that commodity used by that industry as an intermediate input. It also includes final demand columns. The intermediate-use block of the Use table is the starting point for deriving the [A matrix](#a-matrix-direct-requirements-matrix--technical-coefficients). Rows represent commodity supply; columns represent industry demand plus final demand. The BEA publishes Use tables at the 71-sector summary level annually.[cite:bea_concepts_2009]

### Value Added

The contribution of an industry to GDP: total industry output minus the cost of intermediate inputs. In BEA I-O accounts, value added is decomposed into employee compensation (wages and benefits), taxes on production, gross operating surplus (profits and depreciation), and occasionally other adjustments. The **VA** matrix on Leontief contains the four V-code rows from the BEA Use table — V001 (compensation), V003 (taxes on production), VABAS (value added at basic prices), and VAPRO (value added at producers' prices) — for all 71 industries.

### Vertically Integrated Labor (Pasinetti)

A concept from Luigi Pasinetti's structural economics: the total labor embodied in one unit of a sector's final output, including all the labor used up the supply chain. Formally, $v_j = \sum_i l_{ij} \cdot e_i$, where $e_i$ is the direct labor requirement per unit of output in sector $i$ and $l_{ij}$ are elements of the [Leontief inverse](#leontief-inverse). Vertically integrated labor coefficients answer: how much total work — across all sectors — goes into a dollar's worth of final output from sector $j$? Pasinetti used this framework to analyze structural change and growth dynamics across industries.[cite:pasinetti_1981]
