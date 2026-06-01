"""Build sectors.json — canonical 71-sector registry with agg15 crosswalk.

Reads the 2024 pickle (canonical year) plus 1997 for code-set comparison.
Emits site_data/sectors.json per the schema in WEBSITE_BUILD_PLAN.md §5.

Run:  python webapp/data_pipeline/build_sectors.py
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
WEBAPP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAPP_ROOT))
from app import config as C  # noqa: E402

# ---------------------------------------------------------------------------
# AGG15 mapping rule
# -----------------------------------------------------------------------
# Each BEA Summary sector code maps to one of ~14 broad NAICS-derived groups.
# Mapping is by leading code pattern; documented inline.
# Agriculture: NAICS 11x
# Mining: NAICS 21x
# Utilities: NAICS 22
# Construction: NAICS 23
# Manufacturing: NAICS 31x-33x (codes beginning 311..339 + 3361MV, 3364OT)
# Wholesale Trade: NAICS 42
# Retail Trade: NAICS 44x-45x + 4A0 (other retail)
# Transportation & Warehousing: NAICS 48x-49x
# Information: NAICS 51x
# Finance/Insurance/Real Estate: NAICS 52x, 53x + HS (housing), ORE (other real estate)
# Professional & Business Services: NAICS 54x, 55, 56x
# Education & Health: NAICS 61, 62x
# Arts/Accommodation/Food: NAICS 71x, 72x
# Other Services: NAICS 81
# Government: GF*, GSL*
# ---------------------------------------------------------------------------

AGG15_RULES: list[tuple[str, str]] = [
    # (prefix_or_exact_code, group_name)
    # Agriculture
    ("111CA", "Agriculture"),
    ("113FF", "Agriculture"),
    # Mining
    ("211",   "Mining"),
    ("212",   "Mining"),
    ("213",   "Mining"),
    # Utilities
    ("22",    "Utilities"),
    # Construction
    ("23",    "Construction"),
    # Manufacturing  (NAICS 31-33 range)
    ("311FT", "Manufacturing"),
    ("313TT", "Manufacturing"),
    ("315AL", "Manufacturing"),
    ("321",   "Manufacturing"),
    ("322",   "Manufacturing"),
    ("323",   "Manufacturing"),
    ("324",   "Manufacturing"),
    ("325",   "Manufacturing"),
    ("326",   "Manufacturing"),
    ("327",   "Manufacturing"),
    ("331",   "Manufacturing"),
    ("332",   "Manufacturing"),
    ("333",   "Manufacturing"),
    ("334",   "Manufacturing"),
    ("335",   "Manufacturing"),
    ("3361MV","Manufacturing"),
    ("3364OT","Manufacturing"),
    ("337",   "Manufacturing"),
    ("339",   "Manufacturing"),
    # Wholesale Trade  (NAICS 42)
    ("42",    "Wholesale Trade"),
    # Retail Trade  (NAICS 44-45 + 4A0)
    ("441",   "Retail Trade"),
    ("445",   "Retail Trade"),
    ("452",   "Retail Trade"),
    ("4A0",   "Retail Trade"),
    # Transportation & Warehousing  (NAICS 48-49)
    ("481",   "Transportation & Warehousing"),
    ("482",   "Transportation & Warehousing"),
    ("483",   "Transportation & Warehousing"),
    ("484",   "Transportation & Warehousing"),
    ("485",   "Transportation & Warehousing"),
    ("486",   "Transportation & Warehousing"),
    ("487OS", "Transportation & Warehousing"),
    ("493",   "Transportation & Warehousing"),
    # Information  (NAICS 51)
    ("511",   "Information"),
    ("512",   "Information"),
    ("513",   "Information"),
    ("514",   "Information"),
    # Finance, Insurance & Real Estate  (NAICS 52-53 + housing/ORE)
    ("521CI", "Finance, Insurance & Real Estate"),
    ("523",   "Finance, Insurance & Real Estate"),
    ("524",   "Finance, Insurance & Real Estate"),
    ("525",   "Finance, Insurance & Real Estate"),
    ("532RL", "Finance, Insurance & Real Estate"),
    ("HS",    "Finance, Insurance & Real Estate"),
    ("ORE",   "Finance, Insurance & Real Estate"),
    # Professional & Business Services  (NAICS 54-56)
    ("5411",  "Professional & Business Services"),
    ("5412OP","Professional & Business Services"),
    ("5415",  "Professional & Business Services"),
    ("55",    "Professional & Business Services"),
    ("561",   "Professional & Business Services"),
    ("562",   "Professional & Business Services"),
    # Education & Health  (NAICS 61-62)
    ("61",    "Education & Health"),
    ("621",   "Education & Health"),
    ("622",   "Education & Health"),
    ("623",   "Education & Health"),
    ("624",   "Education & Health"),
    # Arts, Accommodation & Food Services  (NAICS 71-72)
    ("711AS", "Arts, Accommodation & Food"),
    ("713",   "Arts, Accommodation & Food"),
    ("721",   "Arts, Accommodation & Food"),
    ("722",   "Arts, Accommodation & Food"),
    # Other Services  (NAICS 81)
    ("81",    "Other Services"),
    # Government
    ("GFE",  "Government"),
    ("GFGD", "Government"),
    ("GFGN", "Government"),
    ("GSLE", "Government"),
    ("GSLG", "Government"),
]

# Build a lookup dict from the rules list
_AGG15_LOOKUP: dict[str, str] = dict(AGG15_RULES)

KNOWN_GROUPS = [
    "Agriculture", "Mining", "Utilities", "Construction", "Manufacturing",
    "Wholesale Trade", "Retail Trade", "Transportation & Warehousing",
    "Information", "Finance, Insurance & Real Estate",
    "Professional & Business Services", "Education & Health",
    "Arts, Accommodation & Food", "Other Services", "Government",
]

NOTE = (
    "Best-effort mapping of 71 BEA Summary sectors to 15 broad NAICS-derived groups. "
    "Mapping is by exact BEA code match (see AGG15_RULES in build_sectors.py). "
    "Intended for Explorer aggregation toggle only; not an official BEA classification."
)


def load_pickle(year: int) -> dict:
    p = C.PROCESSED_DIR / f"year_{year}.pkl"
    with open(p, "rb") as f:
        return pickle.load(f)


def assign_agg15(code: str) -> str:
    if code in _AGG15_LOOKUP:
        return _AGG15_LOOKUP[code]
    # Fallback: try prefix match by code length descending
    for length in (6, 5, 4, 3, 2):
        prefix = code[:length]
        if prefix in _AGG15_LOOKUP:
            return _AGG15_LOOKUP[prefix]
    return "Other Services"  # fallback of last resort


def build() -> None:
    C.ensure_dirs()

    print("Loading 2024 pickle (canonical year)...")
    d24 = load_pickle(2024)

    print("Loading 1997 pickle (code-set comparison)...")
    d97 = load_pickle(1997)

    sectors_2024 = d24["sectors"]           # list[str], canonical column order
    sector_names_2024: dict = d24["sector_names"]
    sectors_1997 = set(d97["sectors"])

    # Report code-set differences
    s24_set = set(sectors_2024)
    only_2024 = s24_set - sectors_1997
    only_1997 = sectors_1997 - s24_set
    if only_2024:
        print(f"  WARNING: sectors in 2024 only: {sorted(only_2024)}")
    if only_1997:
        print(f"  WARNING: sectors in 1997 only: {sorted(only_1997)}")
    if not only_2024 and not only_1997:
        print("  Code sets identical across 1997 and 2024 — good.")

    # Build sector list
    sectors_out = []
    missing_names = []
    for order, code in enumerate(sectors_2024):
        name = sector_names_2024.get(code, "")
        if not name:
            missing_names.append(code)
            name = code  # fallback to code
        agg = assign_agg15(code)
        sectors_out.append({"code": code, "name": name, "order": order, "agg15": agg})

    if missing_names:
        print(f"  WARNING: no name for codes: {missing_names}")

    # Build agg15 group -> [codes] map
    agg15_map: dict[str, list[str]] = {g: [] for g in KNOWN_GROUPS}
    for s in sectors_out:
        grp = s["agg15"]
        if grp not in agg15_map:
            agg15_map[grp] = []
        agg15_map[grp].append(s["code"])

    # va_rows from latest year value_added index
    va = d24["value_added"]
    va_rows = {str(idx): str(idx) for idx in va.index}
    # Annotate known V-codes
    VA_LABELS = {
        "V001": "Compensation of employees",
        "V003": "Taxes on production and imports",
        "VABAS": "Value added at basic prices",
        "VAPRO": "Value added at producers' prices",
    }
    va_rows = {k: VA_LABELS.get(k, k) for k in va_rows}

    # fd_cols from latest year final_demand columns
    fd = d24["final_demand"]
    FD_LABELS = {
        "F010": "Personal consumption expenditures",
        "F02E": "Private fixed investment — equipment",
        "F02N": "Private fixed investment — nonresidential structures",
        "F02R": "Private fixed investment — residential",
        "F02S": "Private fixed investment — software/IP",
        "F030": "Change in private inventories",
        "F040": "Exports of goods and services",
        "F06C": "Federal government — national defense consumption",
        "F06E": "Federal government — national defense equipment",
        "F06N": "Federal government — national defense structures",
        "F06S": "Federal government — national defense software/IP",
        "F07C": "Federal government — nondefense consumption",
        "F07E": "Federal government — nondefense equipment",
        "F07N": "Federal government — nondefense structures",
        "F07S": "Federal government — nondefense software/IP",
        "F10C": "State & local government — consumption",
        "F10E": "State & local government — equipment",
        "F10N": "State & local government — structures",
        "F10S": "State & local government — software/IP",
    }
    fd_cols = {str(col): FD_LABELS.get(str(col), str(col)) for col in fd.columns}

    out = {
        "classification": "BEA Summary (71-sector, NAICS-based)",
        "_agg15_note": NOTE,
        "sectors": sectors_out,
        "agg15": agg15_map,
        "va_rows": va_rows,
        "fd_cols": fd_cols,
    }

    out_path = C.get_sectors_path()
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path}")

    # Verification
    assert len(sectors_out) == 71, f"Expected 71 sectors, got {len(sectors_out)}"
    no_agg = [s["code"] for s in sectors_out if not s["agg15"]]
    assert not no_agg, f"Sectors with empty agg15: {no_agg}"

    print(f"\nVerification passed: {len(sectors_out)} sectors, all have agg15.")
    print("\nagg15 distribution:")
    for grp in KNOWN_GROUPS:
        codes = agg15_map.get(grp, [])
        print(f"  {grp:40s}: {len(codes):2d} sectors")

    unassigned = [g for g in agg15_map if g not in KNOWN_GROUPS]
    if unassigned:
        print(f"  WARNING: unmapped groups: {unassigned}")

    print("\nSample sectors:")
    for s in sectors_out[:5]:
        print(f"  {s['code']}: {s['name']}  [{s['agg15']}]")


if __name__ == "__main__":
    build()
