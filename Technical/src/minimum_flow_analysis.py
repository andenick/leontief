"""Minimum flow and chokepoint analysis for I-O networks.

Identifies critical flows and bottleneck sectors using graph-theoretic
min-cut, flow hierarchy, and Strassert's minimum flow method.

Reference: Strassert (1968); Miller & Blair (2009), Ch. 12.
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def minimum_cut_sectors(
    G: nx.DiGraph,
    source: str,
    sink: str,
) -> Dict:
    """Find minimum cut between two sectors in the I-O network.

    Args:
        G: Directed weighted I-O graph.
        source: Source sector code.
        sink: Target sector code.

    Returns:
        Dict with cut_value, reachable (set), unreachable (set).
    """
    if source not in G or sink not in G:
        raise ValueError(f"Source '{source}' or sink '{sink}' not in graph")

    try:
        cut_value, partition = nx.minimum_cut(G, source, sink, capacity="weight")
        reachable, unreachable = partition
        return {
            "source": source,
            "sink": sink,
            "cut_value": float(cut_value),
            "reachable": reachable,
            "unreachable": unreachable,
            "n_reachable": len(reachable),
            "n_unreachable": len(unreachable),
        }
    except nx.NetworkXError as e:
        logger.warning(f"Min-cut failed for {source}->{sink}: {e}")
        return {
            "source": source, "sink": sink,
            "cut_value": float("inf"),
            "reachable": set(), "unreachable": set(),
            "n_reachable": 0, "n_unreachable": 0,
        }


def critical_flow_pairs(
    G: nx.DiGraph,
    top_k: int = 20,
) -> pd.DataFrame:
    """Find min-cut between the top-k highest-flow sector pairs.

    Args:
        G: I-O network graph.
        top_k: Number of top-flow pairs to analyze.

    Returns:
        DataFrame with source, sink, flow_weight, min_cut_value.
    """
    edges = [(u, v, d["weight"]) for u, v, d in G.edges(data=True)]
    edges.sort(key=lambda x: -x[2])

    results = []
    seen = set()
    for u, v, w in edges:
        if (u, v) in seen or u == v:
            continue
        seen.add((u, v))

        mc = minimum_cut_sectors(G, u, v)
        results.append({
            "source": u,
            "sink": v,
            "flow_weight": w,
            "min_cut_value": mc["cut_value"],
            "n_reachable": mc["n_reachable"],
        })

        if len(results) >= top_k:
            break

    return pd.DataFrame(results)


def chokepoint_index(
    G: nx.DiGraph,
    A: pd.DataFrame,
) -> pd.Series:
    """Compute chokepoint score for each sector.

    Combines betweenness centrality with flow volume to identify
    sectors through which the most total inter-industry flow passes.

    Args:
        G: I-O network graph.
        A: Direct requirements matrix.

    Returns:
        Series of chokepoint scores indexed by sector, sorted descending.
    """
    if G.number_of_edges() == 0:
        return pd.Series(dtype=float, name="chokepoint_index")

    betweenness = nx.betweenness_centrality(G, weight="weight")

    total_flow = {}
    for node in G.nodes():
        in_flow = sum(d["weight"] for _, _, d in G.in_edges(node, data=True))
        out_flow = sum(d["weight"] for _, _, d in G.out_edges(node, data=True))
        total_flow[node] = in_flow + out_flow

    max_flow = max(total_flow.values()) if total_flow else 1.0
    max_betw = max(betweenness.values()) if betweenness else 1.0

    scores = {}
    for node in G.nodes():
        flow_norm = total_flow.get(node, 0) / max(max_flow, 1e-10)
        betw_norm = betweenness.get(node, 0) / max(max_betw, 1e-10)
        scores[node] = flow_norm * betw_norm

    result = pd.Series(scores, name="chokepoint_index").sort_values(ascending=False)
    return result


def flow_hierarchy_score(G: nx.DiGraph) -> float:
    """Compute flow hierarchy of the I-O network.

    Returns a value in [0, 1]:
    - 0: perfectly symmetric (all flows reciprocated equally)
    - 1: perfectly hierarchical (no reciprocated flows)

    Args:
        G: Directed weighted I-O graph.

    Returns:
        Flow hierarchy score.
    """
    if G.number_of_edges() == 0:
        return 0.0
    try:
        return nx.flow_hierarchy(G, weight="weight")
    except nx.NetworkXError:
        return 0.0


def strassert_minimum_flow(
    Z: pd.DataFrame,
    x: pd.Series,
    threshold_pct: float = 1.0,
) -> pd.DataFrame:
    """Strassert's minimum flow method.

    Identifies flows below a threshold as non-essential and filters them
    to reveal the skeleton of the I-O network.

    Args:
        Z: Transactions matrix.
        x: Total output vector.
        threshold_pct: Flows below this % of the supplier's output are dropped.

    Returns:
        DataFrame with essential flows only (zeros for non-essential).
    """
    threshold = threshold_pct / 100

    x_aligned = x.reindex(Z.index).fillna(0)
    x_safe = x_aligned.replace(0, np.nan)

    # Flow as share of supplier's total output
    flow_share = Z.div(x_safe, axis=0).fillna(0)

    # Keep only flows above threshold
    essential = Z.where(flow_share >= threshold, 0)

    total_flows = (Z > 0).sum().sum()
    kept_flows = (essential > 0).sum().sum()
    logger.info(
        f"Strassert: {kept_flows}/{total_flows} flows kept "
        f"({kept_flows/max(total_flows,1)*100:.0f}%) at {threshold_pct}% threshold"
    )

    return essential


def vulnerability_ranking(
    G: nx.DiGraph,
    A: pd.DataFrame,
) -> pd.DataFrame:
    """Rank sectors by multiple vulnerability/importance measures.

    Combines chokepoint index, betweenness, flow hierarchy contribution,
    and weighted degree into a composite ranking.

    Args:
        G: I-O network graph.
        A: Direct requirements matrix.

    Returns:
        DataFrame with individual scores and composite rank.
    """
    nodes = sorted(G.nodes())
    if not nodes:
        return pd.DataFrame()

    choke = chokepoint_index(G, A).reindex(nodes).fillna(0)
    betw = pd.Series(nx.betweenness_centrality(G, weight="weight")).reindex(nodes).fillna(0)

    in_str = pd.Series(
        {n: sum(d["weight"] for _, _, d in G.in_edges(n, data=True)) for n in nodes}
    )
    out_str = pd.Series(
        {n: sum(d["weight"] for _, _, d in G.out_edges(n, data=True)) for n in nodes}
    )

    df = pd.DataFrame({
        "chokepoint": choke,
        "betweenness": betw,
        "in_strength": in_str,
        "out_strength": out_str,
    })

    for col in df.columns:
        col_max = df[col].max()
        df[f"{col}_norm"] = df[col] / max(col_max, 1e-10)

    norm_cols = [c for c in df.columns if c.endswith("_norm")]
    df["composite_score"] = df[norm_cols].mean(axis=1)
    df["rank"] = df["composite_score"].rank(ascending=False).astype(int)

    return df.sort_values("composite_score", ascending=False)
