"""Community detection for I-O networks.

Identifies clusters of sectors that trade heavily with each other,
revealing industrial complexes without relying on SIC/NAICS groupings.

Requires networkx >= 3.0 (for louvain_communities).
"""

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities
from typing import Dict, List, Tuple, Optional
from scipy.optimize import linear_sum_assignment
import logging

logger = logging.getLogger(__name__)


def detect_communities_louvain(
    G: nx.DiGraph,
    resolution: float = 1.0,
    seed: int = 42,
) -> Dict[str, int]:
    """Detect communities using the Louvain method.

    Args:
        G: Directed weighted I-O graph.
        resolution: Higher values produce more communities.
        seed: Random seed for reproducibility.

    Returns:
        Dict mapping sector code -> community ID.
    """
    G_undirected = G.to_undirected()
    communities = louvain_communities(G_undirected, weight="weight",
                                      resolution=resolution, seed=seed)
    partition = {}
    for cid, members in enumerate(communities):
        for node in members:
            partition[node] = cid

    n_comm = len(communities)
    logger.info(f"Louvain: {n_comm} communities detected (resolution={resolution})")
    return partition


def detect_communities_label_propagation(G: nx.DiGraph) -> Dict[str, int]:
    """Detect communities using label propagation (fast, non-deterministic).

    Args:
        G: Directed weighted I-O graph.

    Returns:
        Dict mapping sector code -> community ID.
    """
    G_undirected = G.to_undirected()
    communities = nx.community.label_propagation_communities(G_undirected)
    partition = {}
    for cid, members in enumerate(communities):
        for node in members:
            partition[node] = cid
    return partition


def modularity_score(G: nx.DiGraph, partition: Dict[str, int]) -> float:
    """Compute modularity of a partition.

    Args:
        G: I-O network graph.
        partition: Sector -> community mapping.

    Returns:
        Modularity score in [-0.5, 1.0].
    """
    communities_list = {}
    for node, cid in partition.items():
        communities_list.setdefault(cid, set()).add(node)
    comm_sets = list(communities_list.values())

    G_undirected = G.to_undirected()
    return nx.community.modularity(G_undirected, comm_sets, weight="weight")


def community_flow_matrix(
    Z: pd.DataFrame,
    partition: Dict[str, int],
) -> pd.DataFrame:
    """Aggregate flows by community.

    Args:
        Z: Transactions matrix (sector x sector).
        partition: Sector -> community ID mapping.

    Returns:
        Community x community flow matrix.
    """
    sectors = [s for s in Z.index if s in partition]
    comm_ids = sorted(set(partition[s] for s in sectors))

    flows = pd.DataFrame(0.0, index=comm_ids, columns=comm_ids)
    for i in sectors:
        for j in sectors:
            ci, cj = partition[i], partition[j]
            flows.loc[ci, cj] += Z.loc[i, j]

    flows.index.name = "from_community"
    flows.columns.name = "to_community"
    return flows


def community_summary(
    Z: pd.DataFrame,
    partition: Dict[str, int],
    sector_names: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Summarize communities: size, internal flow share, key members.

    Args:
        Z: Transactions matrix.
        partition: Sector -> community ID mapping.
        sector_names: Optional sector code -> name mapping.

    Returns:
        DataFrame with one row per community.
    """
    comm_members = {}
    for node, cid in partition.items():
        comm_members.setdefault(cid, []).append(node)

    flow_mat = community_flow_matrix(Z, partition)
    total_flow = flow_mat.values.sum()

    rows = []
    for cid in sorted(comm_members.keys()):
        members = comm_members[cid]
        internal = float(flow_mat.loc[cid, cid]) if cid in flow_mat.index else 0.0
        total_comm = float(flow_mat.loc[cid].sum() + flow_mat[cid].sum() - internal)

        top_members = members[:5]
        if sector_names:
            labels = [sector_names.get(m, m) for m in top_members]
        else:
            labels = top_members

        rows.append({
            "community": cid,
            "n_sectors": len(members),
            "internal_flow": internal,
            "internal_flow_share": internal / max(total_comm, 1e-10),
            "total_flow_share": total_comm / max(total_flow, 1e-10),
            "top_members": ", ".join(str(l) for l in labels),
        })

    return pd.DataFrame(rows).set_index("community")


def _align_partitions(
    partition_old: Dict[str, int],
    partition_new: Dict[str, int],
) -> Dict[str, int]:
    """Align community IDs between two partitions using Hungarian matching.

    Minimizes reassignment by matching old and new communities that share
    the most members.
    """
    common = set(partition_old.keys()) & set(partition_new.keys())
    if not common:
        return partition_new

    old_ids = sorted(set(partition_old[n] for n in common))
    new_ids = sorted(set(partition_new[n] for n in common))

    cost = np.zeros((len(old_ids), len(new_ids)))
    for oi, old_id in enumerate(old_ids):
        old_members = {n for n in common if partition_old[n] == old_id}
        for ni, new_id in enumerate(new_ids):
            new_members = {n for n in common if partition_new[n] == new_id}
            overlap = len(old_members & new_members)
            cost[oi, ni] = -overlap

    row_ind, col_ind = linear_sum_assignment(cost)
    id_map = {}
    for r, c in zip(row_ind, col_ind):
        id_map[new_ids[c]] = old_ids[r]

    next_id = max(old_ids) + 1
    aligned = {}
    for node, cid in partition_new.items():
        if cid in id_map:
            aligned[node] = id_map[cid]
        else:
            aligned[node] = next_id
            id_map[cid] = next_id
            next_id += 1

    return aligned


def community_evolution(
    data_by_year: Dict[int, dict],
    method: str = "louvain",
    resolution: float = 1.0,
    threshold_pct: float = 0.01,
) -> pd.DataFrame:
    """Track community membership across years with aligned labels.

    Args:
        data_by_year: Dict of year -> data dict.
        method: "louvain" or "label_propagation".
        resolution: Louvain resolution parameter.
        threshold_pct: Edge threshold for graph construction.

    Returns:
        DataFrame with years as rows, sectors as columns, values = community ID.
    """
    from network_centrality import build_io_graph, _reconstruct_z

    partitions = {}
    prev_partition = None

    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        if A is None or A.empty:
            continue

        Z = _reconstruct_z(A, d.get("total_output"))
        G = build_io_graph(Z, threshold_pct)

        if method == "louvain":
            partition = detect_communities_louvain(G, resolution)
        else:
            partition = detect_communities_label_propagation(G)

        if prev_partition is not None:
            partition = _align_partitions(prev_partition, partition)

        partitions[year] = partition
        prev_partition = partition

    if not partitions:
        return pd.DataFrame()

    all_sectors = sorted(set().union(*[set(p.keys()) for p in partitions.values()]))
    df = pd.DataFrame(index=sorted(partitions.keys()), columns=all_sectors, dtype=float)
    for year, partition in partitions.items():
        for sector, cid in partition.items():
            df.loc[year, sector] = cid

    df.index.name = "year"
    return df
