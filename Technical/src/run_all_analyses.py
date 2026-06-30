"""Master orchestrator for all 20 I-O analyses.

Loads annual pkl data once, runs each analysis module, and exports
results to Outputs/Data/.

Usage: python run_all_analyses.py [--modules mod1,mod2,...] [--years 1997-2024]
"""

import sys
import pickle
import time
import logging
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy import linalg

# Setup paths
PROJECT = Path(__file__).parent.parent.parent
PROCESSED = PROJECT / "Technical" / "data" / "processed" / "annual_71"
OUTPUTS = PROJECT / "Outputs" / "Data"
LOGS = PROJECT / "Technical" / "logs"

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS / "run_all_analyses.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("run_all_analyses")


def load_year(year: int) -> Optional[dict]:
    path = PROCESSED / f"year_{year}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def load_all_years(start: int = 1997, end: int = 2024) -> Dict[int, dict]:
    data = {}
    for year in range(start, end + 1):
        d = load_year(year)
        if d is not None:
            data[year] = d
    logger.info(f"Loaded {len(data)} years of data ({min(data.keys())}-{max(data.keys())})")
    return data


def get_final_demand_vector(d: dict) -> pd.Series:
    fd = d.get("final_demand")
    if fd is None:
        return pd.Series(dtype=float)
    if isinstance(fd, pd.DataFrame):
        return fd.sum(axis=1)
    return fd


def run_module(name: str, func, data: Dict[int, dict], latest_year: int) -> bool:
    """Run a single analysis module with error handling."""
    t0 = time.time()
    try:
        func(data, latest_year)
        elapsed = time.time() - t0
        logger.info(f"  {name}: OK ({elapsed:.1f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  {name}: FAILED ({elapsed:.1f}s) - {e}")
        return False


# ── Individual analysis runners ──────────────────────────────────────

def run_ras(data, latest):
    from ras_updating import ras_biproportional, ras_accuracy_report
    years = sorted(data.keys())
    if len(years) < 2:
        return

    results = []
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        A0 = data[y0]["A_matrix"]
        A1 = data[y1]["A_matrix"]
        x1 = data[y1]["total_output"]
        f1 = get_final_demand_vector(data[y1])

        common = A0.index.intersection(A1.index).intersection(x1.index)
        target_col = (x1.reindex(common).fillna(0) - f1.reindex(common).fillna(0)).clip(lower=0)
        target_row = A0.loc[common, common].sum(axis=1) * (x1.reindex(common).sum() / max(A0.loc[common, common].values.sum(), 1e-10))

        projected, _ = ras_biproportional(A0.loc[common, common], target_row, target_col)
        report = ras_accuracy_report(projected, A1.loc[common, common])
        report["base_year"] = y0
        report["target_year"] = y1
        results.append(report)

    pd.DataFrame(results).to_excel(OUTPUTS / "ras_projection_accuracy.xlsx", sheet_name="RAS", index=False)


def run_network(data, latest):
    from network_centrality import build_io_graph, compute_centrality_suite, _reconstruct_z

    all_results = {}
    for year in sorted(data.keys()):
        d = data[year]
        A = d["A_matrix"]
        Z = _reconstruct_z(A, d.get("total_output"))
        G = build_io_graph(Z)
        suite = compute_centrality_suite(G)
        all_results[year] = suite

    if latest in all_results:
        all_results[latest].to_excel(OUTPUTS / f"network_centrality_{latest}.xlsx", sheet_name="centrality")

    pagerank_ts = pd.DataFrame({y: r["pagerank"] for y, r in all_results.items()}).T
    pagerank_ts.index.name = "year"
    pagerank_ts.to_excel(OUTPUTS / "centrality_timeseries.xlsx", sheet_name="pagerank")


def run_community(data, latest):
    from network_centrality import build_io_graph, _reconstruct_z
    from community_detection import detect_communities_louvain, community_summary, community_flow_matrix

    d = data[latest]
    A = d["A_matrix"]
    Z = _reconstruct_z(A, d.get("total_output"))
    G = build_io_graph(Z)
    partition = detect_communities_louvain(G)
    summary = community_summary(Z, partition, d.get("sector_names"))
    summary.to_excel(OUTPUTS / f"community_detection_{latest}.xlsx", sheet_name="communities")


def run_topology(data, latest):
    from network_centrality import build_io_graph, _reconstruct_z
    from network_topology import topology_summary

    rows = []
    for year in sorted(data.keys()):
        d = data[year]
        A = d["A_matrix"]
        Z = _reconstruct_z(A, d.get("total_output"))
        G = build_io_graph(Z)
        summary = topology_summary(G)
        summary["year"] = year
        rows.append(summary)

    pd.concat(rows).set_index("year").to_excel(
        OUTPUTS / "topology_timeseries.xlsx", sheet_name="topology"
    )


def run_minflow(data, latest):
    from network_centrality import build_io_graph, _reconstruct_z
    from minimum_flow_analysis import chokepoint_index, flow_hierarchy_score, vulnerability_ranking

    d = data[latest]
    A = d["A_matrix"]
    Z = _reconstruct_z(A, d.get("total_output"))
    G = build_io_graph(Z)

    ranking = vulnerability_ranking(G, A)
    ranking.to_excel(OUTPUTS / f"minimum_flow_analysis_{latest}.xlsx", sheet_name="vulnerability")


def run_triangulation(data, latest):
    from triangulation import triangulation_summary

    rows = []
    for year in sorted(data.keys()):
        A = data[year]["A_matrix"]
        summary = triangulation_summary(A)
        summary["year"] = year
        rows.append(summary)

    pd.concat(rows).set_index("year").to_excel(
        OUTPUTS / "triangulation_timeseries.xlsx", sheet_name="triangulation"
    )


def run_qioa(data, latest):
    from qioa import structural_zeros_analysis, sign_stable_sectors

    A_by_year = {y: d["A_matrix"] for y, d in data.items()}
    zeros = structural_zeros_analysis(A_by_year)
    if not zeros.empty:
        zeros.to_excel(OUTPUTS / "structural_zeros.xlsx", sheet_name="zeros", index=False)

    A_latest = data[latest]["A_matrix"]
    stability = sign_stable_sectors(A_latest, n_perturbations=100)
    stability.to_excel(OUTPUTS / f"qioa_{latest}.xlsx", sheet_name="sign_stability")


def run_profit(data, latest):
    from profit_rate_simulation import (
        sectoral_profit_rates, sraffian_prices, maximum_profit_rate,
        wage_profit_frontier, equalize_profit_rates,
    )

    d = data[latest]
    A = d["A_matrix"]
    va = d.get("value_added", pd.DataFrame())
    x = d.get("total_output", pd.Series(dtype=float))

    if isinstance(va, pd.DataFrame) and not va.empty:
        wages_row = [r for r in va.index if "V001" in str(r) or "comp" in str(r).lower()]
        if wages_row:
            wages = va.loc[wages_row[0]].reindex(A.index).fillna(0)
        else:
            wages = va.iloc[0].reindex(A.index).fillna(0)
    else:
        wages = pd.Series(0, index=A.index)

    rates = sectoral_profit_rates(A, wages, x, va)
    R_max = maximum_profit_rate(A)
    frontier = wage_profit_frontier(A, wages / x.reindex(A.index).replace(0, np.nan).fillna(1))

    with pd.ExcelWriter(OUTPUTS / f"profit_rate_simulation_{latest}.xlsx") as writer:
        rates.to_frame().to_excel(writer, sheet_name="profit_rates")
        frontier.to_excel(writer, sheet_name="wage_profit_frontier", index=False)


def run_cascade(data, latest):
    from cascade_failure import cascade_vulnerability_map, systemic_risk_index

    d = data[latest]
    A = d["A_matrix"]
    f = get_final_demand_vector(d)

    vuln = cascade_vulnerability_map(A, f, threshold_pct=50.0, max_sectors=50)
    risk = systemic_risk_index(vuln)

    with pd.ExcelWriter(OUTPUTS / f"cascade_failure_{latest}.xlsx") as writer:
        vuln.to_excel(writer, sheet_name="vulnerability_map")
        risk.to_frame().to_excel(writer, sheet_name="systemic_risk")


def run_hem(data, latest):
    from hypothetical_extraction import hypothetical_extraction_all, extraction_decomposition

    d = data[latest]
    A = d["A_matrix"]
    f = get_final_demand_vector(d)

    hem_all = hypothetical_extraction_all(A, f)
    hem_all.to_excel(OUTPUTS / f"hypothetical_extraction_{latest}.xlsx", sheet_name="HEM")


# ── Wave 2 analysis runners ──────────────────────────────────────────

def _get_wages_and_labor(d, sectors):
    """Extract wages and labor coefficients from a year's data dict."""
    va = d.get("value_added", pd.DataFrame())
    x = d.get("total_output", pd.Series(dtype=float))
    if isinstance(va, pd.DataFrame) and not va.empty:
        comp_rows = [r for r in va.index if "V001" in str(r)]
        wages = va.loc[comp_rows[0]].reindex(sectors).fillna(0) if comp_rows else va.iloc[0].reindex(sectors).fillna(0)
    else:
        wages = pd.Series(0, index=sectors)
    x_aligned = x.reindex(sectors).fillna(0)
    labor_coeff = (wages / x_aligned.replace(0, np.nan)).fillna(0)
    return wages, labor_coeff


def run_spectral(data, latest):
    from spectral_gap_analysis import spectral_gap, spectral_gap_timeseries, eigenvector_centrality_from_spectrum
    ts = spectral_gap_timeseries(data)
    ev = eigenvector_centrality_from_spectrum(data[latest]["A_matrix"])
    with pd.ExcelWriter(OUTPUTS / "spectral_gap_analysis.xlsx") as w:
        ts.to_excel(w, sheet_name="timeseries")
        ev.to_excel(w, sheet_name="eigenvectors")


def run_propagation(data, latest):
    from innovation_propagation import propagation_depth_by_sector, innovation_propagation_timeseries
    depths = propagation_depth_by_sector(data[latest]["A_matrix"])
    ts = innovation_propagation_timeseries(data)
    with pd.ExcelWriter(OUTPUTS / "innovation_propagation.xlsx") as w:
        depths.to_frame().to_excel(w, sheet_name="sector_depths")
        ts.to_excel(w, sheet_name="timeseries")


def run_tournament(data, latest):
    from sector_knockout_tournament import sector_knockout_tournament
    d = data[latest]
    result = sector_knockout_tournament(d["A_matrix"], get_final_demand_vector(d), n_rounds=3)
    result.to_excel(OUTPUTS / f"sector_knockout_tournament_{latest}.xlsx", sheet_name="elo_ranking")


def run_gvc(data, latest):
    from gvc_upstreamness import antras_chor_upstreamness, downstreamness_index, gvc_position_index
    d = data[latest]
    A, x = d["A_matrix"], d.get("total_output", pd.Series(dtype=float))
    f = get_final_demand_vector(d)
    va = d.get("value_added", pd.DataFrame())
    u = antras_chor_upstreamness(A, f, x)
    dn = downstreamness_index(A, va, x)
    pos = gvc_position_index(u, dn)
    pos.to_excel(OUTPUTS / f"gvc_upstreamness_{latest}.xlsx", sheet_name="gvc_position")


def run_dva_gov(data, latest):
    from domestic_content_government import dva_in_government_procurement
    d = data[latest]
    use, va, x = d.get("use_table"), d.get("value_added"), d.get("total_output")
    fd = d.get("final_demand")
    if use is None or va is None or fd is None or isinstance(fd, pd.Series):
        return
    result = dva_in_government_procurement(use, va, x, fd)
    result.to_excel(OUTPUTS / f"domestic_content_gov_{latest}.xlsx", sheet_name="dva", index=False)


def run_leakage(data, latest):
    from import_leakage import leakage_by_fd_category
    d = data[latest]
    use, x = d.get("use_table"), d.get("total_output")
    fd = d.get("final_demand")
    if use is None or fd is None or isinstance(fd, pd.Series):
        return
    result = leakage_by_fd_category(use, x, fd)
    result.to_excel(OUTPUTS / f"import_leakage_{latest}.xlsx", sheet_name="leakage", index=False)


def run_miyazawa(data, latest):
    from miyazawa_decomposition import miyazawa_partition, autonomous_vs_induced_output
    d = data[latest]
    A, use, va, fd, x = d["A_matrix"], d.get("use_table"), d.get("value_added"), d.get("final_demand"), d.get("total_output")
    if use is None or va is None or fd is None or isinstance(fd, pd.Series):
        return
    result = miyazawa_partition(A, use, va, fd, x)
    decomp = autonomous_vs_induced_output(result["M"], result["L"], fd)
    decomp.to_excel(OUTPUTS / f"miyazawa_decomposition_{latest}.xlsx", sheet_name="output_decomp")


def run_fiscal(data, latest):
    from fiscal_multiplier import fiscal_multiplier_table
    d = data[latest]
    A, L, fd, va, x = d["A_matrix"], d["L_matrix"], d.get("final_demand"), d.get("value_added"), d.get("total_output")
    if fd is None or isinstance(fd, pd.Series):
        return
    table = fiscal_multiplier_table(A, L, fd, va, x)
    table.to_excel(OUTPUTS / f"fiscal_multiplier_{latest}.xlsx", sheet_name="multipliers", index=False)


def run_supermult(data, latest):
    from keynesian_supermultiplier import supermultiplier_timeseries
    ts = supermultiplier_timeseries(data)
    ts.to_excel(OUTPUTS / "keynesian_supermultiplier.xlsx", sheet_name="timeseries")


def run_feldman(data, latest):
    from feldman_mahalanobis import classify_departments, feldman_growth_dynamics
    d = data[latest]
    fd = d.get("final_demand")
    if fd is None or isinstance(fd, pd.Series):
        return
    dept = classify_departments(fd)
    ts = feldman_growth_dynamics(data, dept)
    with pd.ExcelWriter(OUTPUTS / "feldman_mahalanobis.xlsx") as w:
        dept.to_frame().to_excel(w, sheet_name="dept_classification")
        ts.to_excel(w, sheet_name="timeseries")


def run_counterfact(data, latest):
    from functional_counterfactuals import all_sector_wage_counterfactuals
    d_latest = data[latest]
    anchor_year = min(data.keys())
    d_anchor = data[anchor_year]
    result = all_sector_wage_counterfactuals(
        d_latest["A_matrix"], d_latest.get("value_added", pd.DataFrame()),
        d_anchor.get("value_added", pd.DataFrame()),
        d_latest.get("total_output", pd.Series(dtype=float)),
        d_anchor.get("total_output", pd.Series(dtype=float)),
    )
    result.to_excel(OUTPUTS / "functional_counterfactuals.xlsx", sheet_name="all_sectors")


def run_shaikh(data, latest):
    from shaikh_profit_rate import shaikh_profit_rate_timeseries, ltpf_regression
    ts = shaikh_profit_rate_timeseries(data)
    reg = ltpf_regression(ts)
    with pd.ExcelWriter(OUTPUTS / "shaikh_profit_rate.xlsx") as w:
        ts.to_excel(w, sheet_name="timeseries")
        pd.DataFrame([reg]).to_excel(w, sheet_name="ltpf_regression", index=False)


def run_tot(data, latest):
    from terms_of_trade_structural import tot_timeseries
    ts = tot_timeseries(data)
    ts.to_excel(OUTPUTS / "terms_of_trade_structural.xlsx", sheet_name="timeseries")


def run_okishio(data, latest):
    from okishio_simulator import okishio_timeseries
    ts = okishio_timeseries(data)
    ts.to_excel(OUTPUTS / "okishio_simulator.xlsx", sheet_name="timeseries")


def run_tssi(data, latest):
    from tssi_valuation import tssi_melt_timeseries
    ts = tssi_melt_timeseries(data)
    ts.to_excel(OUTPUTS / "tssi_valuation.xlsx", sheet_name="melt_timeseries")


def run_rebound(data, latest):
    from rebound_effect import rebound_by_energy_sector
    d = data[latest]
    result = rebound_by_energy_sector(d["A_matrix"], d.get("value_added", pd.DataFrame()), d.get("total_output", pd.Series(dtype=float)))
    result.to_excel(OUTPUTS / f"rebound_effect_{latest}.xlsx", sheet_name="rebound", index=False)


def run_stranded(data, latest):
    from stranded_asset_propagation import stranded_asset_shock
    d = data[latest]
    result = stranded_asset_shock(d["A_matrix"], d.get("value_added", pd.DataFrame()), d.get("total_output", pd.Series(dtype=float)))
    result.to_excel(OUTPUTS / f"stranded_asset_{latest}.xlsx", sheet_name="impact")


def run_cbam(data, latest):
    from carbon_border_adjustment import cbam_price_adjustment
    d = data[latest]
    result = cbam_price_adjustment(d["A_matrix"], d.get("value_added", pd.DataFrame()), d.get("total_output", pd.Series(dtype=float)))
    result.to_excel(OUTPUTS / f"carbon_border_adjustment_{latest}.xlsx", sheet_name="cbam")


# ── Module registry ──────────────────────────────────────────────────

MODULES = {
    # Wave 1
    "ras": ("RAS / Cross-Entropy Updating", run_ras),
    "network": ("Network Centrality", run_network),
    "community": ("Community Detection", run_community),
    "topology": ("Network Topology", run_topology),
    "minflow": ("Minimum Flow Analysis", run_minflow),
    "triangulation": ("Triangulation / Block Decomposition", run_triangulation),
    "qioa": ("Qualitative I-O Analysis", run_qioa),
    "profit": ("Profit Rate Equalization", run_profit),
    "cascade": ("Cascade Failure Simulation", run_cascade),
    "hem": ("Hypothetical Extraction Method", run_hem),
    # Wave 2
    "spectral": ("Spectral Gap & Mixing Time", run_spectral),
    "propagation": ("Innovation Propagation Speed", run_propagation),
    "tournament": ("Sector Knockout Tournament", run_tournament),
    "gvc": ("GVC Position / Upstreamness", run_gvc),
    "dva_gov": ("Domestic Content in Gov Procurement", run_dva_gov),
    "leakage": ("Import Leakage Multiplier", run_leakage),
    "miyazawa": ("Miyazawa Demand Decomposition", run_miyazawa),
    "fiscal": ("Fiscal Multiplier by Category", run_fiscal),
    "supermult": ("Keynesian Supermultiplier", run_supermult),
    "feldman": ("Feldman-Mahalanobis Two-Sector", run_feldman),
    "counterfact": ("Functional Income Counterfactuals", run_counterfact),
    "shaikh": ("Shaikh Integrated Profit Rate", run_shaikh),
    "tot": ("Terms of Trade Structural Change", run_tot),
    "okishio": ("Okishio Theorem Simulator", run_okishio),
    "tssi": ("TSSI Sequential Valuation", run_tssi),
    "rebound": ("Rebound Effect Estimation", run_rebound),
    "stranded": ("Stranded Asset Propagation", run_stranded),
    "cbam": ("Carbon Border Adjustment", run_cbam),
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run all Leontief I-O analyses")
    parser.add_argument("--modules", type=str, default=None,
                        help="Comma-separated list of modules to run (default: all)")
    parser.add_argument("--start", type=int, default=1997)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Leontief I-O Analysis Suite — Master Orchestrator")
    logger.info("=" * 60)

    data = load_all_years(args.start, args.end)
    if not data:
        logger.error("No data loaded. Run bea_api_parser.py first.")
        return

    latest = max(data.keys())
    logger.info(f"Latest year with data: {latest}")

    if args.modules:
        selected = [m.strip() for m in args.modules.split(",")]
    else:
        selected = list(MODULES.keys())

    n_ok = 0
    n_fail = 0
    t_total = time.time()

    for mod_key in selected:
        if mod_key not in MODULES:
            logger.warning(f"Unknown module: {mod_key}")
            continue
        name, func = MODULES[mod_key]
        logger.info(f"Running: {name}")
        if run_module(mod_key, func, data, latest):
            n_ok += 1
        else:
            n_fail += 1

    elapsed = time.time() - t_total
    logger.info(f"\nComplete: {n_ok} OK, {n_fail} failed, {elapsed:.1f}s total")
    logger.info(f"Output directory: {OUTPUTS}")


if __name__ == "__main__":
    main()
