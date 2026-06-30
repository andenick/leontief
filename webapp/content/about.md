---
title: About Leontief
summary: Mission, reproducibility philosophy, audience, licensing, and how to cite this site.
order: 20
---

## What Is Leontief?

Leontief is a free public resource for exploring the structure of the U.S. economy through input-output tables. It is named after Wassily Leontief (1905–1999), the Harvard economist who invented input-output analysis and received the 1973 Nobel Prize in Economics for demonstrating that the purchases and sales linking every industry to every other industry could be expressed as a system of linear equations — and then solved.[cite:leontief_1936]

Input-output tables are one of the most powerful lenses economics has for understanding how production actually works. They answer questions that aggregate statistics cannot: What happens to steel output if auto demand falls? How much energy does a dollar of semiconductor production require? Which sectors are the true hubs of economic interdependence? Leontief exists because these tables are publicly produced, rigorously maintained, and chronically underused outside specialist circles.

## The Data

Leontief draws on 28 annual tables published by the Bureau of Economic Analysis (BEA) covering 1997 through 2024, each organized using the BEA Summary 71-sector classification. For each year we compute and publish seven matrices: the raw Use and Supply tables, the direct-requirements matrix A, a squared variant A\_square, the Leontief inverse L (total requirements), the value-added breakdown, and the final demand columns. Every matrix is available for download in CSV, Excel, JSON, and Parquet format.

The BEA data is in the public domain. Leontief adds computation, documentation, and presentation — but no proprietary content of its own.

## Our Philosophy: Reproducibility First

Every chart on this site is backed by a downloadable data file. Every downloadable data file is backed by a documented derivation. Every derivation traces to a publicly accessible BEA API call.

This is not just good practice — it is the core of what we are offering. Input-output multipliers and Leontief inverses are computed quantities, not raw measurements, and the choices made in computing them (which rows to include, how to square a non-square A matrix, whether to use total or domestic-only use tables) shape the numbers you get. By publishing the code alongside the data, Leontief lets any user verify, challenge, or extend our work. A number you cannot reproduce is a number you cannot trust.

## Who Is This For?

**Students and instructors.** The methodology page walks through the derivation of A and L from first principles, with real numbers from the actual tables. The glossary defines every term. The data downloads give students a clean, analysis-ready version of the same tables their professors cite.

**Researchers.** Every matrix is available in Parquet for direct import into Python or R. The annual 71-sector series covers 28 years with a consistent sector classification — a ready-made panel for structural decomposition, multiplier analysis, and network studies.

**Journalists, policy analysts, and the curious.** Input-output accounts are the quantitative skeleton of economic debate. Supply chains, industrial policy, carbon footprints, the "multiplier" in fiscal stimulus — these concepts all live in I-O tables. Leontief makes it possible to look things up, not just read about them.

## Licensing

The underlying BEA input-output data is a product of the United States federal government and is in the public domain. The derived matrices, documentation, and site content produced by Leontief are offered under a **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. You are free to share and adapt this material for any purpose, including commercially, provided you give appropriate credit.

## How to Cite This Site

If you use Leontief data or charts in published work, please cite it as:

> Leontief: U.S. Input-Output Tables, 1997–2024. Retrieved from https://leontief.nickanderson.us. Data sourced from the Bureau of Economic Analysis (BEA), U.S. Department of Commerce.

For the BEA methodology underlying the accounts, cite:

> Horowitz, K. J., &amp; Planting, M. A. (2009). *Concepts and Methods of the U.S. Input-Output Accounts*. Bureau of Economic Analysis.

For the standard textbook treatment of input-output methods:

> Miller, R. E., &amp; Blair, P. D. (2022). *Input-Output Analysis: Foundations and Extensions* (3rd ed.). Cambridge University Press.

## Contact and Contributions

Leontief is an open project. If you find an error in the data, a broken derivation, or a sector that doesn't add up, please open an issue or pull request. The goal is a resource the community can rely on — and that means it needs to be correctable.
