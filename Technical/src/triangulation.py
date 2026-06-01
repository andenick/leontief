"""Triangulation and block decomposition of I-O matrices.

Reorders sectors to approximate upper-triangular form, revealing the
economy's hierarchy of production stages. Block decomposition identifies
strongly connected industrial clusters.

Reference: Korte & Oberhofer (1970); Helmstaedter (1973); Miller & Blair Ch. 12.
"""

import numpy as np
import pandas as pd
import networkx as nx
from scipy import linalg as sp_linalg
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


def triangularity_index(A: pd.DataFrame) -> float:
    """Compute the triangularity index of a matrix.

    Defined as the sum of elements above the main diagonal divided by
    the total sum. A perfectly upper-triangular matrix scores 1.0;
    a symmetric matrix scores ~0.5.

    Args:
        A: Square coefficient matrix.

    Returns:
        Triangularity index in [0, 1].
    """
    vals = A.values
    total = vals.sum()
    if total == 0:
        return 0.0
    upper = np.triu(vals, k=1).sum()
    return float(upper / total)


def reorder_by_triangulation(
    A: pd.DataFrame,
    method: str = "spectral",
) -> Tuple[pd.DataFrame, List[str]]:
    """Reorder sectors to maximize triangularity.

    Args:
        A: Direct requirements matrix.
        method: "spectral" (Fiedler vector) or "greedy" (Helmstaedter heuristic).

    Returns:
        Tuple of (reordered A matrix, new sector ordering).
    """
    if method == "spectral":
        order = _spectral_ordering(A)
    elif method == "greedy":
        order = _greedy_ordering(A)
    else:
        raise ValueError(f"Unknown method: {method}")

    A_reordered = A.loc[order, order]

    orig_tri = triangularity_index(A)
    new_tri = triangularity_index(A_reordered)
    logger.info(f"Triangulation ({method}): {orig_tri:.4f} -> {new_tri:.4f}")

    return A_reordered, order


def _spectral_ordering(A: pd.DataFrame) -> List[str]:
    """Order sectors using the Fiedler vector of the graph Laplacian."""
    n = A.shape[0]
    W = A.values + A.values.T
    D = np.diag(W.sum(axis=1))
    L = D - W

    try:
        eigenvalues, eigenvectors = sp_linalg.eigh(L)
        fiedler = eigenvectors[:, 1]
        order_idx = np.argsort(fiedler)
        return [A.index[i] for i in order_idx]
    except sp_linalg.LinAlgError:
        logger.warning("Spectral ordering failed; returning original order")
        return list(A.index)


def _greedy_ordering(A: pd.DataFrame) -> List[str]:
    """Helmstaedter's greedy heuristic for triangulation.

    Iteratively places the sector with the highest ratio of
    backward-to-forward flow at the beginning of the ordering.
    """
    remaining = list(A.index)
    order = []
    vals = A.values.copy()
    idx_map = {s: i for i, s in enumerate(A.index)}

    while remaining:
        best_score = -np.inf
        best_sector = remaining[0]

        for s in remaining:
            i = idx_map[s]
            rem_idx = [idx_map[r] for r in remaining if r != s]
            if not rem_idx:
                best_sector = s
                break

            # Forward flow: row i to remaining columns
            forward = sum(vals[i, j] for j in rem_idx)
            # Backward flow: remaining rows to column i
            backward = sum(vals[j, i] for j in rem_idx)

            score = backward - forward
            if score > best_score:
                best_score = score
                best_sector = s

        order.append(best_sector)
        remaining.remove(best_sector)

    return order


def decompose_into_blocks(
    A: pd.DataFrame,
) -> Tuple[List[List[str]], pd.DataFrame]:
    """Decompose matrix into strongly connected components (blocks).

    Uses Tarjan's algorithm to find SCCs in the I-O flow graph.
    SCCs represent groups of sectors with mutual circular dependencies.

    Args:
        A: Direct requirements matrix.

    Returns:
        Tuple of (list of SCC member lists, block-reordered A matrix).
    """
    G = nx.DiGraph()
    for i in A.index:
        for j in A.columns:
            if A.loc[i, j] > 0:
                G.add_edge(i, j, weight=A.loc[i, j])

    sccs = list(nx.strongly_connected_components(G))
    sccs.sort(key=lambda s: -len(s))

    scc_lists = [sorted(scc) for scc in sccs]

    block_order = []
    for scc in scc_lists:
        block_order.extend(scc)

    # Only include sectors in A
    block_order = [s for s in block_order if s in A.index]
    missing = [s for s in A.index if s not in block_order]
    block_order.extend(missing)

    A_blocked = A.loc[block_order, block_order]

    logger.info(f"Block decomposition: {len(scc_lists)} SCCs, largest = {len(scc_lists[0])} sectors")
    return scc_lists, A_blocked


def block_diagonal_structure(
    A: pd.DataFrame,
    blocks: List[List[str]],
) -> pd.DataFrame:
    """Analyze within-block vs. between-block flow structure.

    Args:
        A: Direct requirements matrix.
        blocks: List of sector groups (from decompose_into_blocks).

    Returns:
        DataFrame with one row per block: size, within_flow, between_flow,
        within_share.
    """
    rows = []
    for bid, members in enumerate(blocks):
        valid = [m for m in members if m in A.index]
        if not valid:
            continue

        within = A.loc[valid, valid].values.sum()
        total_out = A.loc[valid].values.sum()
        total_in = A[valid].values.sum()
        between = total_out + total_in - 2 * within

        rows.append({
            "block": bid,
            "n_sectors": len(valid),
            "within_flow": float(within),
            "between_flow": float(between),
            "within_share": float(within / max(within + between, 1e-10)),
            "members": ", ".join(valid[:5]) + ("..." if len(valid) > 5 else ""),
        })

    return pd.DataFrame(rows).set_index("block")


def triangulation_summary(A: pd.DataFrame) -> pd.DataFrame:
    """Run all triangulation methods and return comparative summary.

    Args:
        A: Direct requirements matrix.

    Returns:
        DataFrame comparing original vs. reordered triangularity.
    """
    original_tri = triangularity_index(A)

    A_spectral, _ = reorder_by_triangulation(A, "spectral")
    spectral_tri = triangularity_index(A_spectral)

    A_greedy, _ = reorder_by_triangulation(A, "greedy")
    greedy_tri = triangularity_index(A_greedy)

    sccs, _ = decompose_into_blocks(A)
    n_sccs = len(sccs)
    largest_scc = max(len(s) for s in sccs) if sccs else 0

    block_struct = block_diagonal_structure(A, sccs)
    within_total = block_struct["within_flow"].sum()
    between_total = block_struct["between_flow"].sum()

    return pd.DataFrame([{
        "original_triangularity": original_tri,
        "spectral_triangularity": spectral_tri,
        "greedy_triangularity": greedy_tri,
        "improvement_spectral": spectral_tri - original_tri,
        "improvement_greedy": greedy_tri - original_tri,
        "n_sccs": n_sccs,
        "largest_scc_size": largest_scc,
        "within_block_flow_share": within_total / max(within_total + between_total, 1e-10),
    }])
