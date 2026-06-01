"""Network centrality analysis for I-O tables.

Treats the transactions matrix as a directed weighted graph and computes
multiple centrality measures to identify structurally important sectors
beyond standard Rasmussen indices.

Reference: Carvalho & Gabaix (2013); Acemoglu et al. (2012).
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def build_io_graph(
    Z: pd.DataFrame,
    threshold_pct: float = 0.01,
) -> nx.DiGraph:
    """Build a directed weighted graph from an I-O transactions matrix.

    Nodes = sectors, edge i->j with weight = Z_ij / total_flow.
    Edges below threshold_pct of total flow are dropped.

    Args:
        Z: Transactions (flow) matrix or Use table (sector x sector portion).
        threshold_pct: Drop edges below this fraction of total flow.

    Returns:
        nx.DiGraph with weighted edges.
    """
    total = Z.values.sum()
    if total == 0:
        return nx.DiGraph()

    G = nx.DiGraph()
    G.add_nodes_from(Z.index)

    threshold = threshold_pct / 100 * total
    for i in Z.index:
        for j in Z.columns:
            w = Z.loc[i, j]
            if w > threshold:
                G.add_edge(i, j, weight=float(w), weight_norm=float(w / total))

    logger.info(f"I-O graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def compute_centrality_suite(G: nx.DiGraph) -> pd.DataFrame:
    """Compute multiple centrality measures for the I-O network.

    Returns:
        DataFrame indexed by sector with columns: in_degree, out_degree,
        betweenness, eigenvector, pagerank, hub_score, authority_score.
    """
    nodes = sorted(G.nodes())
    if len(nodes) == 0:
        return pd.DataFrame()

    in_deg = nx.in_degree_centrality(G)
    out_deg = nx.out_degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight")
    pagerank = nx.pagerank(G, weight="weight", alpha=0.85)

    try:
        eigenvector = nx.eigenvector_centrality_numpy(G, weight="weight")
    except (nx.NetworkXError, np.linalg.LinAlgError):
        eigenvector = {n: 0.0 for n in nodes}
        logger.warning("Eigenvector centrality failed; using zeros")

    try:
        hubs, authorities = nx.hits(G, max_iter=500)
    except nx.NetworkXError:
        hubs = {n: 0.0 for n in nodes}
        authorities = {n: 0.0 for n in nodes}

    result = pd.DataFrame({
        "in_degree": pd.Series(in_deg),
        "out_degree": pd.Series(out_deg),
        "betweenness": pd.Series(betweenness),
        "eigenvector": pd.Series(eigenvector),
        "pagerank": pd.Series(pagerank),
        "hub_score": pd.Series(hubs),
        "authority_score": pd.Series(authorities),
    }).reindex(nodes)

    return result


def upstream_downstream_position(
    A: pd.DataFrame,
    G: nx.DiGraph,
) -> pd.DataFrame:
    """Compute upstream/downstream position metrics for each sector.

    Upstream position: weighted average distance to final demand.
    Downstream position: weighted average distance from primary inputs.

    Args:
        A: Direct requirements matrix.
        G: I-O network graph.

    Returns:
        DataFrame with upstream_position, downstream_position columns.
    """
    nodes = sorted(G.nodes())
    n = len(nodes)

    # Use powers of A to measure distance
    A_vals = A.reindex(index=nodes, columns=nodes).fillna(0).values
    upstream = np.zeros(n)
    downstream = np.zeros(n)

    power = np.eye(n)
    for step in range(1, min(n, 20)):
        power = power @ A_vals
        row_activity = power.sum(axis=1)
        col_activity = power.sum(axis=0)
        upstream += step * col_activity
        downstream += step * row_activity

    col_total = A_vals.sum(axis=0)
    row_total = A_vals.sum(axis=1)
    col_total_safe = np.where(col_total > 0, col_total, 1)
    row_total_safe = np.where(row_total > 0, row_total, 1)

    upstream_norm = upstream / col_total_safe
    downstream_norm = downstream / row_total_safe

    return pd.DataFrame({
        "upstream_position": upstream_norm,
        "downstream_position": downstream_norm,
    }, index=nodes)


def weighted_degree(G: nx.DiGraph) -> pd.DataFrame:
    """Compute weighted in-degree and out-degree (strength).

    Args:
        G: I-O network graph with "weight" edge attribute.

    Returns:
        DataFrame with in_strength, out_strength, total_strength.
    """
    nodes = sorted(G.nodes())
    in_str = {n: sum(d["weight"] for _, _, d in G.in_edges(n, data=True)) for n in nodes}
    out_str = {n: sum(d["weight"] for _, _, d in G.out_edges(n, data=True)) for n in nodes}

    df = pd.DataFrame({
        "in_strength": pd.Series(in_str),
        "out_strength": pd.Series(out_str),
    }).reindex(nodes)
    df["total_strength"] = df["in_strength"] + df["out_strength"]
    return df


def centrality_timeseries(
    data_by_year: Dict[int, dict],
    measure: str = "pagerank",
    threshold_pct: float = 0.01,
) -> pd.DataFrame:
    """Compute a centrality measure across years.

    Args:
        data_by_year: Dict of year -> data dict with "use_table" or "A_matrix".
        measure: Column name from compute_centrality_suite.
        threshold_pct: Edge threshold for graph construction.

    Returns:
        DataFrame with years as rows, sectors as columns.
    """
    results = {}
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        if A is None or A.empty:
            continue
        Z = _reconstruct_z(A, d.get("total_output"))
        G = build_io_graph(Z, threshold_pct)
        suite = compute_centrality_suite(G)
        if measure in suite.columns:
            results[year] = suite[measure]

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results).T
    df.index.name = "year"
    return df


def _reconstruct_z(A: pd.DataFrame, x: Optional[pd.Series]) -> pd.DataFrame:
    """Reconstruct Z = A * x_hat from A matrix and total output."""
    if x is None:
        return A
    x_aligned = x.reindex(A.columns).fillna(0)
    Z = A.multiply(x_aligned, axis=1)
    return Z
