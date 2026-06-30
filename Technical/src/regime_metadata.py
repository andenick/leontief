"""Regime metadata for U.S. Input-Output accounts.

Defines methodological periods, classification systems, and break points
for regime-aware historical analysis. Every time-series analysis should
consult this module to annotate regime boundaries.

Reference: Technical/research/REGIME_SHIFTS.md
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RegimePeriod:
    """A distinct methodological period in BEA I-O history."""
    name: str
    start_year: int
    end_year: Optional[int]  # None = ongoing
    classification: str  # "custom", "sic", "naics"
    naics_version: Optional[str]  # "1997", "2002", "2007", etc.
    has_annual_io: bool
    annual_sectors: Optional[int]  # Number of sectors in annual tables
    benchmark_years: list[int] = field(default_factory=list)
    benchmark_sectors: Optional[int] = None  # Detailed sector count
    has_separate_imports: bool = False
    has_fisim_allocation: bool = False
    chain_weighted: bool = False
    notes: str = ""


# Define all regime periods
REGIMES = [
    RegimePeriod(
        name="Pre-SIC Era",
        start_year=1947,
        end_year=1957,
        classification="custom",
        naics_version=None,
        has_annual_io=False,
        annual_sectors=None,
        benchmark_years=[1947],
        benchmark_sectors=450,
        notes="First U.S. I-O table. Bureau of Labor Statistics production.",
    ),
    RegimePeriod(
        name="SIC Era",
        start_year=1958,
        end_year=1996,
        classification="sic",
        naics_version=None,
        has_annual_io=False,
        annual_sectors=None,
        benchmark_years=[1958, 1963, 1967, 1972, 1977, 1982, 1987, 1992],
        benchmark_sectors=537,  # max (1977)
        notes="Standard Industrial Classification. Relatively stable methodology.",
    ),
    RegimePeriod(
        name="Early NAICS Era",
        start_year=1997,
        end_year=2006,
        classification="naics",
        naics_version="1997",
        has_annual_io=False,
        annual_sectors=None,
        benchmark_years=[1997, 2002],
        benchmark_sectors=500,
        has_fisim_allocation=False,  # Pre-2003 revision
        chain_weighted=True,
        notes="SIC->NAICS transition (CRITICAL BREAK). No annual I-O data yet.",
    ),
    RegimePeriod(
        name="Integrated Annual Era",
        start_year=2007,
        end_year=None,  # ongoing
        classification="naics",
        naics_version="2007+",
        has_annual_io=True,
        annual_sectors=71,
        benchmark_years=[2007, 2012, 2017],
        benchmark_sectors=405,
        has_separate_imports=True,
        has_fisim_allocation=True,
        chain_weighted=True,
        notes="Annual 71-category I-O + integrated benchmarks. Domestic/import split available.",
    ),
]


@dataclass
class RegimeBreak:
    """A specific methodological discontinuity."""
    year: int
    name: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    affects: str  # What metrics/tables are affected


BREAKS = [
    RegimeBreak(1997, "SIC to NAICS", "CRITICAL",
                "Complete industry reclassification. Services reorganized. "
                "New 'Information' sector created. Manufacturing narrowed.",
                "All sector-level comparisons across this boundary"),
    RegimeBreak(1996, "Chain-weighting", "HIGH",
                "Fixed-weight to chain-type Fisher indexes for real measures. "
                "Real tables become non-additive.",
                "All real/deflated I-O tables and growth calculations"),
    RegimeBreak(2003, "FISIM allocation", "HIGH",
                "Financial intermediation services allocated to user industries "
                "instead of single dummy sector.",
                "Financial sector output, all sectors' intermediate inputs"),
    RegimeBreak(2007, "Supply/Use + Import split", "HIGH",
                "Adopted SNA 2008 Supply/Use terminology. Published separate "
                "domestic vs import Use tables.",
                "Multiplier calculations, import dependency analysis"),
    RegimeBreak(2010, "Annual I-O tables begin", "MEDIUM",
                "First continuous annual I-O data (71 categories, 1997+). "
                "Benchmarks integrated with annual accounts.",
                "Data availability (not a methodological break per se)"),
    RegimeBreak(2004, "GDP-by-Industry integration", "MEDIUM",
                "Annual GDP-by-Industry now consistent with I-O accounts.",
                "Annual value-added estimates, interpolation quality"),
]


# 71-category industry mapping (post-2007 annual tables)
ANNUAL_71_SECTORS = {
    # Agriculture
    "111CA": "Farms",
    "113FF": "Forestry, fishing, and related activities",
    # Mining
    "211": "Oil and gas extraction",
    "212": "Mining, except oil and gas",
    "213": "Support activities for mining",
    # Utilities
    "22": "Utilities",
    # Construction
    "23": "Construction",
    # Manufacturing (21 sectors)
    "321": "Wood products",
    "327": "Nonmetallic mineral products",
    "331": "Primary metals",
    "332": "Fabricated metal products",
    "333": "Machinery",
    "334": "Computer and electronic products",
    "335": "Electrical equipment, appliances, and components",
    "3361MV": "Motor vehicles, bodies and trailers, and parts",
    "3364OT": "Other transportation equipment",
    "337": "Furniture and related products",
    "339": "Miscellaneous manufacturing",
    "311FT": "Food and beverage and tobacco products",
    "313TT": "Textile mills and textile product mills",
    "315AL": "Apparel and leather and allied products",
    "322": "Paper products",
    "323": "Printing and related support activities",
    "324": "Petroleum and coal products",
    "325": "Chemical products",
    "326": "Plastics and rubber products",
    # Trade (9 sectors)
    "42": "Wholesale trade",
    "44RT": "Retail trade",
    # Transportation (6 sectors)
    "481": "Air transportation",
    "482": "Rail transportation",
    "483": "Water transportation",
    "484": "Truck transportation",
    "485": "Transit and ground passenger transportation",
    "486": "Pipeline transportation",
    "487OS": "Other transportation and support activities",
    "493": "Warehousing and storage",
    # Information (5 sectors)
    "511": "Publishing industries, except internet",
    "512": "Motion picture and sound recording industries",
    "513": "Broadcasting and telecommunications",
    "514": "Data processing, internet publishing, and other information services",
    # Finance (6 sectors)
    "521CI": "Federal Reserve banks, credit intermediation, and related activities",
    "523": "Securities, commodity contracts, and investments",
    "524": "Insurance carriers and related activities",
    "525": "Funds, trusts, and other financial vehicles",
    # Real estate (3 sectors)
    "531": "Real estate",
    "532RL": "Rental and leasing services and lessors of intangible assets",
    # Professional services (4 sectors)
    "5411": "Legal services",
    "5415": "Computer systems design and related services",
    "5412OP": "Miscellaneous professional, scientific, and technical services",
    "55": "Management of companies and enterprises",
    # Administrative (1 sector)
    "561": "Administrative and support services",
    "562": "Waste management and remediation services",
    # Education (2 sectors)
    "61": "Educational services",
    # Health (2 sectors)
    "621": "Ambulatory health care services",
    "622HO": "Hospitals and nursing and residential care facilities",
    "624": "Social assistance",
    # Arts (2 sectors)
    "711AS": "Performing arts, spectator sports, museums, and related activities",
    "713": "Amusements, gambling, and recreation industries",
    "721": "Accommodation",
    "722": "Food services and drinking places",
    # Other services (2 sectors)
    "81": "Other services, except government",
    # Government (3 sectors)
    "GFGD": "Federal general government (defense)",
    "GFGN": "Federal general government (nondefense)",
    "GFE": "Federal government enterprises",
    "GSLG": "State and local general government",
    "GSLE": "State and local government enterprises",
}


def get_regime(year: int) -> RegimePeriod:
    """Return the regime period for a given year."""
    for regime in REGIMES:
        end = regime.end_year or 9999
        if regime.start_year <= year <= end:
            return regime
    raise ValueError(f"No regime defined for year {year}")


def get_breaks_between(start_year: int, end_year: int) -> list[RegimeBreak]:
    """Return all regime breaks that fall between two years."""
    return [b for b in BREAKS if start_year < b.year <= end_year]


def is_comparable(year1: int, year2: int, strict: bool = True) -> bool:
    """Check if two years are in the same regime (directly comparable).

    Args:
        year1, year2: Years to compare.
        strict: If True, any break between them makes them incomparable.
                If False, only CRITICAL breaks make them incomparable.
    """
    breaks = get_breaks_between(min(year1, year2), max(year1, year2))
    if strict:
        return len(breaks) == 0
    return not any(b.severity == "CRITICAL" for b in breaks)


def get_available_benchmarks() -> list[int]:
    """Return all benchmark years with data in Leontief."""
    all_benchmarks = []
    for regime in REGIMES:
        all_benchmarks.extend(regime.benchmark_years)
    return sorted(all_benchmarks)


def regime_annotation(year: int) -> str:
    """Return a human-readable annotation string for charts."""
    regime = get_regime(year)
    parts = [f"{regime.classification.upper()}"]
    if regime.has_annual_io:
        parts.append(f"{regime.annual_sectors}-sector annual")
    else:
        parts.append("benchmark only")
    if regime.has_separate_imports:
        parts.append("domestic/import split")
    return " | ".join(parts)
