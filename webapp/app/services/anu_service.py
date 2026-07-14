"""Anu-framework explainer service (Code mode).

Decodes the Anu **pipeline-script phase** prefixes so the project's code reads
as an ordered method instead of noise. The phase vocabulary is the canonical
Anu "Two Namespaces" script-phase table (Council/Druck/docs/
ANU_FRAMEWORK_OVERVIEW.md § "Two Namespaces"):

    S## Setup · L## Loading · P## Processing · V## Validation ·
    M## Manual adjustment · A## Analysis · O## Output · E## Exploration

CRITICAL (Two Namespaces): these script-phase prefixes describe *what a script
does*. They are an entirely different vocabulary from the series-ID prefixes
(D / XS) that describe *what a data series is*. **P is Processing, and
Processing only** — never inferred from a series-ID first letter. This module
describes the pipeline strictly from the script-phase table; it never presents
a series-ID letter as a stage.

This module ships the short, friendly, project-specific version. Only the
phases this project actually uses are listed (no Exploration scripts ship in
the public package).
"""
from __future__ import annotations

# The canonical Anu pipeline-script phases, in pipeline order. Titles are the
# canonical script-phase meanings (Two Namespaces table); blurbs specialise
# them to this BEA I-O build. P = Processing only.
STAGES: list[dict[str, str]] = [
    {"prefix": "S", "title": "Setup",
     "blurb": "Register each upstream data source — the named publisher, series "
              "id, vintage, and retrieval method — and prepare the working "
              "environment. Every table begins from a documented source of "
              "record (here, the U.S. Bureau of Economic Analysis Annual I-O "
              "Accounts)."},
    {"prefix": "L", "title": "Loading",
     "blurb": "Fetch and read the raw source data (BEA API pulls, archived "
              "spreadsheets) and check that the fetched units and dimensions "
              "match what the source promises before anything downstream runs."},
    {"prefix": "P", "title": "Processing",
     "blurb": "Construction and transformation — and processing only. Assemble "
              "the Use and Supply tables, then derive the technical-coefficient "
              "matrix A, its square form, and the Leontief inverse "
              "L = (I − A)⁻¹, with a dimensional-analysis check whenever units "
              "differ."},
    {"prefix": "V", "title": "Validation",
     "blurb": "Check each constructed matrix and series against the published "
              "BEA benchmarks — row/column totals, balance identities, unit and "
              "scale audits. Tables only pass when they reproduce the published "
              "values."},
    {"prefix": "M", "title": "Manual adjustment",
     "blurb": "Apply and document any hand adjustment a source genuinely "
              "requires (for example a BEA redefinition or a one-off vintage "
              "fix). Each adjustment is recorded so the change is auditable, "
              "never silent."},
    {"prefix": "A", "title": "Analysis",
     "blurb": "Compute the analytic quantities built on the matrices — output "
              "multipliers, backward/forward linkage indices, and the other "
              "I-O measures the studies and charts report."},
    {"prefix": "O", "title": "Output",
     "blurb": "Write the publishable artifacts: the per-table CSV / Parquet "
              "files, the bulk archives, the catalog, the figures, and the "
              "documentation that ships with the data."},
]


def stages() -> list[dict[str, str]]:
    """Return the ordered stage explainer cards."""
    return STAGES
