"""Complete catalog of all U.S. Input-Output table vintages (1947-2024).

Documents every benchmark year, its classification system, sector counts,
table types, and data availability in the Leontief.io project.

Usage:
    from vintage_catalog import ALL_BENCHMARKS, ANNUAL_SYSTEM, get_benchmark
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Benchmark:
    """Metadata for a single U.S. I-O benchmark table."""
    year: int
    producer: str                     # "BLS" or "BEA"
    classification: str               # "pre_sic", "sic_1957", "sic_1967", etc.
    detailed_industries: int          # Number of sectors at detailed level
    summary_industries: int           # Number at summary level
    table_types: list[str]            # Available table types
    has_make_use: bool                # True if Make/Use (not just transactions)
    has_imports_separate: bool        # True if domestic/import split available
    has_redefinitions: bool           # True if before/after redefinitions available
    data_in_project: bool             # True if data files exist in Leontief.io
    files: list[str] = field(default_factory=list)
    sic_version: Optional[str] = None
    naics_version: Optional[str] = None
    notes: str = ""


ALL_BENCHMARKS = [
    Benchmark(
        year=1947,
        producer="BLS",
        classification="pre_sic",
        detailed_industries=85,
        summary_industries=85,
        table_types=["transactions"],
        has_make_use=False,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        notes="First comprehensive U.S. I-O table. Produced by Bureau of Labor "
              "Statistics, later revised by BEA. Based on Leontief's 1936 methodology. "
              "~450 sectors in original working tables, published at 85-industry level.",
    ),
    Benchmark(
        year=1958,
        producer="BEA",
        classification="sic_1957",
        detailed_industries=85,
        summary_industries=85,
        table_types=["transactions"],
        has_make_use=False,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1957",
        notes="First BEA-produced benchmark. Uses 1957 SIC revision.",
    ),
    Benchmark(
        year=1963,
        producer="BEA",
        classification="sic_1957",
        detailed_industries=367,
        summary_industries=85,
        table_types=["transactions"],
        has_make_use=False,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1957",
        notes="First benchmark with detailed (367) and summary (85) levels. "
              "Major increase in sector detail.",
    ),
    Benchmark(
        year=1967,
        producer="BEA",
        classification="sic_1967",
        detailed_industries=484,
        summary_industries=85,
        table_types=["transactions", "make", "use"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1967",
        notes="First benchmark with Make and Use tables (replacing single "
              "transactions matrix). SIC 1967 revision introduces new categories.",
    ),
    Benchmark(
        year=1972,
        producer="BEA",
        classification="sic_1972",
        detailed_industries=496,
        summary_industries=85,
        table_types=["transactions", "make", "use", "IxI_TR", "CxC_TR", "IxC_TR"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1972",
        notes="First benchmark with total requirements tables (Leontief inverse). "
              "First CxC and IxC derivations. Milestone for analytical capability.",
    ),
    Benchmark(
        year=1977,
        producer="BEA",
        classification="sic_1977",
        detailed_industries=537,
        summary_industries=85,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1977",
        notes="Peak sector detail in SIC era (537 industries). "
              "Full standard table set established.",
    ),
    Benchmark(
        year=1982,
        producer="BEA",
        classification="sic_1977",
        detailed_industries=498,
        summary_industries=97,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1977",
        notes="Summary level expanded from 85 to 97 industries. "
              "Detailed level reduced from 537 to 498.",
    ),
    Benchmark(
        year=1987,
        producer="BEA",
        classification="sic_1987",
        detailed_industries=498,
        summary_industries=97,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req",
                     "six_digit_transactions"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=True,
        sic_version="1987",
        files=["TBL5-87A.DAT", "TBL5-87B.DAT", "TBL9-87.DAT",
               "sic-io.doc", "mathio.doc", "tbl5-87.fmt", "tbl9-87.fmt"],
        notes="Last major SIC revision (1987). Six-digit transactions data "
              "available. SIC-to-I-O concordance document included. "
              "Data unpacked from 1987_SixDigit_Transactions.zip.",
    ),
    Benchmark(
        year=1992,
        producer="BEA",
        classification="sic_1987",
        detailed_industries=498,
        summary_industries=97,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=False,
        data_in_project=False,
        sic_version="1987",
        notes="Last SIC-based benchmark. Same classification as 1987. "
              "Data available from BEA historical archive but not yet downloaded.",
    ),
    Benchmark(
        year=1997,
        producer="BEA",
        classification="naics_1997",
        detailed_industries=491,
        summary_industries=71,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=True,
        data_in_project=True,
        naics_version="1997",
        files=["IxI_Summary_1997.xlsx", "Make_SUT_Framework_1997.xlsx",
               "Use_SUT_Framework_1997.xlsx"],
        notes="CRITICAL BREAK: First NAICS-based benchmark. Complete industry "
              "reclassification. Services reorganized, new 'Information' sector "
              "created, manufacturing narrowed. 491 detailed industries + "
              "71 summary. Before/after redefinitions distinction begins.",
    ),
    Benchmark(
        year=2002,
        producer="BEA",
        classification="naics_2002",
        detailed_industries=426,
        summary_industries=71,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req",
                     "import_matrix", "PCE_bridge", "PDE_bridge"],
        has_make_use=True,
        has_imports_separate=False,
        has_redefinitions=True,
        data_in_project=True,
        naics_version="2002",
        files=["IxI_Summary_2002.xlsx", "Make_SUT_Framework_2002.xlsx",
               "Use_SUT_Framework_2002.xlsx", "REV_NAICSUseDetail 4-24-08.txt",
               "REV_NAICSMakeDetail 4-24-08.txt", "2002detail.zip",
               "2002summary.xls", "IndbyIndTRDetail.txt", "and more"],
        notes="Most complete benchmark in project (detailed + summary + "
              "import matrix + bridge tables). NAICS 2002 minor revision. "
              "426 detailed industries. Import matrix available but "
              "domestic/import split not yet standard.",
    ),
    Benchmark(
        year=2007,
        producer="BEA",
        classification="naics_2007",
        detailed_industries=389,
        summary_industries=71,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req",
                     "domestic_use", "import_use", "import_matrix"],
        has_make_use=True,
        has_imports_separate=True,
        has_redefinitions=True,
        data_in_project=False,
        naics_version="2007",
        notes="CRITICAL: First benchmark with separate domestic/import Use tables. "
              "Integrated with annual accounts (Supply/Use framework). "
              "Domestic-only requirements tables now standard. "
              "Internet/e-commerce industries updated. "
              "DATA NOT YET DOWNLOADED.",
    ),
    Benchmark(
        year=2012,
        producer="BEA",
        classification="naics_2012",
        detailed_industries=402,
        summary_industries=71,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req",
                     "domestic_use", "import_use"],
        has_make_use=True,
        has_imports_separate=True,
        has_redefinitions=True,
        data_in_project=False,
        naics_version="2012",
        notes="Tech/information sector refinements. 402 detailed industries. "
              "Fully integrated with annual accounts. DATA NOT YET DOWNLOADED.",
    ),
    Benchmark(
        year=2017,
        producer="BEA",
        classification="naics_2017",
        detailed_industries=405,
        summary_industries=71,
        table_types=["make", "use", "IxI_TR", "CxC_TR", "IxC_TR", "direct_req",
                     "domestic_use", "import_use"],
        has_make_use=True,
        has_imports_separate=True,
        has_redefinitions=True,
        data_in_project=False,
        naics_version="2017",
        notes="Most recent published benchmark. Retail/wholesale updates. "
              "405 detailed industries. DATA NOT YET DOWNLOADED.",
    ),
]


@dataclass
class AnnualSystem:
    """Metadata for the BEA annual I-O table system."""
    start_year: int = 1997
    end_year: int = 2024
    industries: int = 71
    level: str = "Summary"
    table_types: list[str] = field(default_factory=lambda: [
        "Supply (Make)", "Use (before redefinitions)",
        "Total Requirements IxI", "Total Requirements CxC",
        "Total Requirements IxC",
    ])
    classification: str = "NAICS (consistent 71-category mapping)"
    source: str = "BEA API (InputOutput dataset)"
    data_in_project: bool = True
    notes: str = ("Continuous annual series 1997-2024. 71-sector classification "
                  "is consistent across all years. Derived from GDP-by-Industry "
                  "accounts, calibrated to benchmarks. Published annually with "
                  "~2-year lag. First published ~2010.")


ANNUAL_SYSTEM = AnnualSystem()


# Sector-level (15 broad sectors) available via API
SECTOR_LEVEL = {
    "industries": 15,
    "level": "Sector",
    "years": "1997-2024",
    "table_ids": {"IxI_TR": 60, "Use": 258, "Supply": 261},
    "data_in_project": True,
    "notes": "Most aggregated level. 15 broad sectors roughly comparable "
             "to historical 85-industry summary groupings.",
}


# Classification timeline
CLASSIFICATION_TIMELINE = [
    {"years": "1947-1962", "system": "Pre-SIC / 1957 SIC", "notes": "Ad hoc codes"},
    {"years": "1963-1966", "system": "SIC 1957", "notes": "367 detailed industries"},
    {"years": "1967-1971", "system": "SIC 1967", "notes": "484 industries, first Make/Use"},
    {"years": "1972-1976", "system": "SIC 1972", "notes": "496 industries, first total requirements"},
    {"years": "1977-1986", "system": "SIC 1977", "notes": "537 industries (peak SIC detail)"},
    {"years": "1987-1996", "system": "SIC 1987", "notes": "498 industries, final SIC era"},
    {"years": "1997-2001", "system": "NAICS 1997", "notes": "CRITICAL BREAK from SIC"},
    {"years": "2002-2006", "system": "NAICS 2002", "notes": "Minor NAICS revision"},
    {"years": "2007-2011", "system": "NAICS 2007", "notes": "Supply/Use + import split begins"},
    {"years": "2012-2016", "system": "NAICS 2012", "notes": "Tech sector updates"},
    {"years": "2017-2021", "system": "NAICS 2017", "notes": "Retail/wholesale updates"},
    {"years": "2022-present", "system": "NAICS 2022", "notes": "Most recent"},
]


def get_benchmark(year: int) -> Benchmark:
    """Return benchmark metadata for a given year."""
    for b in ALL_BENCHMARKS:
        if b.year == year:
            return b
    raise ValueError(f"No benchmark for year {year}")


def benchmarks_with_data() -> list[Benchmark]:
    """Return only benchmarks that have data in the project."""
    return [b for b in ALL_BENCHMARKS if b.data_in_project]


def sector_count_timeline() -> list[dict]:
    """Return sector counts over time for visualization."""
    return [
        {"year": b.year, "detailed": b.detailed_industries,
         "summary": b.summary_industries, "classification": b.classification}
        for b in ALL_BENCHMARKS
    ]


def table_type_evolution() -> list[dict]:
    """Return which table types available per benchmark."""
    return [
        {"year": b.year, "types": b.table_types,
         "has_make_use": b.has_make_use,
         "has_imports_separate": b.has_imports_separate,
         "has_redefinitions": b.has_redefinitions}
        for b in ALL_BENCHMARKS
    ]
