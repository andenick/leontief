"""Network topology analysis: small-world, scale-free, and structural tests.

Tests whether the I-O network exhibits small-world properties (high clustering,
short paths) or scale-free degree distributions (power-law tails).

Reference: Carvalho (2014); Watts & Strogatz (1998).
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def degree_distribution(G: nx.DiGraph) -> pd.DataFrame:
    """Compute in-degree and out-degree distributions.

    Args:
        G: I-O network graph.

    Returns:
        DataFrame with degree, in_count, out_count, in_ccdf, out_ccdf.
    """
    in_degrees = [d for _, d in G.in_degree()]
    out_degrees = [d for _, d in G.out_degree()]

    max_deg = max(max(in_degrees, default=0), max(out_degrees, default=0))
    degrees = list(range(max_deg + 1))

    in_counts = np.bincount(in_degrees, minlength=max_deg + 1)
    out_counts = np.bincount(out_degrees, minlength=max_deg + 1)
    n = G.number_of_nodes()

    in_ccdf = np.cumsum(in_counts[::-1])[::-1] / max(n, 1)
    out_ccdf = np.cumsum(out_counts[::-1])[::-1] / max(n, 1)

    return pd.DataFrame({
        "degree": degrees,
        "in_count": in_counts,
        "out_count": out_counts,
        "in_ccdf": in_ccdf,
        "out_ccdf": out_ccdf,
    }).set_index("degree")


def weighted_degree_distribution(G: nx.DiGraph) -> pd.DataFrame:
    """Compute weighted degree (strength) distribution.

    Args:
        G: I-O network graph with "weight" edge attribute.

    Returns:
        DataFrame indexed by node with in_strength, out_strength.
    """
    nodes = sorted(G.nodes())
    in_str = []
    out_str = []
    for n in nodes:
        in_str.append(sum(d.get("weight", 1) for _, _, d in G.in_edges(n, data=True)))
        out_str.append(sum(d.get("weight", 1) for _, _, d in G.out_edges(n, data=True)))

    return pd.DataFrame({
        "in_strength": in_str,
        "out_strength": out_str,
    }, index=nodes)


def clustering_coefficients(G: nx.DiGraph) -> pd.Series:
    """Compute weighted local clustering coefficient per node.

    Args:
        G: I-O network graph.

    Returns:
        Series of clustering coefficients indexed by node.
    """
    G_undirected = G.to_undirected()
    cc = nx.clustering(G_undirected, weight="weight")
    return pd.Series(cc, name="clustering_coefficient").reindex(sorted(G.nodes()))


def characteristic_path_length(G: nx.DiGraph) -> float:
    """Average shortest path length on the largest weakly connected component.

    Args:
        G: I-O network graph.

    Returns:
        Average shortest path length (float), or inf if disconnected.
    """
    if G.number_of_nodes() == 0:
        return float("inf")

    components = list(nx.weakly_connected_components(G))
    largest = max(components, key=len)
    subgraph = G.subgraph(largest).copy()

    if subgraph.number_of_nodes() < 2:
        return 0.0

    try:
        return nx.average_shortest_path_length(subgraph, weight=None)
    except nx.NetworkXError:
        return float("inf")


def small_world_index(
    G: nx.DiGraph,
    n_random: int = 100,
    seed: int = 42,
) -> Dict[str, float]:
    """Compute Humphries-Gurney small-world index sigma.

    sigma = (C / C_rand) / (L / L_rand)
    sigma > 1 indicates small-world tendency.

    Args:
        G: I-O network graph.
        n_random: Number of random graphs for baseline.
        seed: Random seed.

    Returns:
        Dict with C_actual, C_random, L_actual, L_random, sigma.
    """
    G_undirected = G.to_undirected()
    n_nodes = G_undirected.number_of_nodes()
    n_edges = G_undirected.number_of_edges()

    if n_nodes < 3 or n_edges == 0:
        return {"C_actual": 0, "C_random": 0, "L_actual": 0, "L_random": 0, "sigma": 0}

    C_actual = nx.average_clustering(G_undirected, weight="weight")
    L_actual = characteristic_path_length(G)

    rng = np.random.RandomState(seed)
    p = 2 * n_edges / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0
    C_rand_list = []
    L_rand_list = []

    for i in range(n_random):
        G_rand = nx.gnp_random_graph(n_nodes, p, seed=rng.randint(0, 2**31))
        if G_rand.number_of_edges() == 0:
            continue
        C_rand_list.append(nx.average_clustering(G_rand))
        if nx.is_connected(G_rand):
            L_rand_list.append(nx.average_shortest_path_length(G_rand))

    C_random = np.mean(C_rand_list) if C_rand_list else 1e-10
    L_random = np.mean(L_rand_list) if L_rand_list else 1.0

    C_ratio = C_actual / max(C_random, 1e-10)
    L_ratio = L_actual / max(L_random, 1e-10)
    sigma = C_ratio / max(L_ratio, 1e-10)

    logger.info(f"Small-world sigma={sigma:.3f} (C_ratio={C_ratio:.2f}, L_ratio={L_ratio:.2f})")

    return {
        "C_actual": C_actual,
        "C_random": C_random,
        "L_actual": L_actual,
        "L_random": L_random,
        "C_ratio": C_ratio,
        "L_ratio": L_ratio,
        "sigma": sigma,
    }


def power_law_fit(degrees: pd.Series) -> Dict[str, float]:
    """Fit power-law exponent via OLS on log-log rank plot.

    Args:
        degrees: Series of degree values (one per node).

    Returns:
        Dict with exponent, r_squared, n_nonzero.
    """
    nonzero = degrees[degrees > 0].sort_values(ascending=False)
    if len(nonzero) < 3:
        return {"exponent": np.nan, "r_squared": np.nan, "n_nonzero": len(nonzero)}

    log_rank = np.log(np.arange(1, len(nonzero) + 1))
    log_vals = np.log(nonzero.values)

    coeffs = np.polyfit(log_rank, log_vals, 1)
    exponent = coeffs[0]

    predicted = np.polyval(coeffs, log_rank)
    ss_res = np.sum((log_vals - predicted) ** 2)
    ss_tot = np.sum((log_vals - log_vals.mean()) ** 2)
    r_squared = 1 - ss_res / max(ss_tot, 1e-15)

    return {
        "exponent": float(exponent),
        "r_squared": float(r_squared),
        "n_nonzero": len(nonzero),
    }


def topology_summary(G: nx.DiGraph) -> pd.DataFrame:
    """Single-row summary of network topology metrics.

    Args:
        G: I-O network graph.

    Returns:
        Single-row DataFrame with all key topology metrics.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    density = nx.density(G) if n > 0 else 0

    G_undirected = G.to_undirected()
    avg_clustering = nx.average_clustering(G_undirected, weight="weight") if n > 0 else 0
    avg_path = characteristic_path_length(G)

    sw = small_world_index(G, n_random=50)

    in_deg = pd.Series([d for _, d in G.in_degree()])
    pl = power_law_fit(in_deg)

    return pd.DataFrame([{
        "n_nodes": n,
        "n_edges": m,
        "density": density,
        "avg_clustering": avg_clustering,
        "avg_path_length": avg_path,
        "small_world_sigma": sw["sigma"],
        "degree_exponent": pl["exponent"],
        "degree_r_squared": pl["r_squared"],
    }])
