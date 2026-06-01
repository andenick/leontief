"""Global Value Chain position: Antràs-Chor upstreamness and downstreamness.

Measures each sector's distance from final demand (upstreamness) and
from primary inputs (downstreamness) using the I-O structure.

Reference: Antràs & Chor (2013); Fally (2012).
"""

import numpy as np
import pandas as pd
from scipy import linalg
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def antras_chor_upstreamness(
    A: pd.DataFrame,
    f: pd.Series,
    total_output: pd.Series,
) -> pd.Series:
    """Compute Antràs-Chor upstreamness index.

    U_i = [sum_k k * (A^{k-1} * f)_i] / x_i
    Efficient: U = L * (L * f) / x  (using the L^2 property)

    Higher U = further upstream from final demand.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector (aggregated across FD categories).
        total_output: Total output by sector.

    Returns:
        Series of upstreamness values >= 1.
    """
    n = A.shape[0]
    sectors = A.index

    f_aligned = f.reindex(sectors).fillna(0).values
    x = total_output.reindex(sectors).fillna(0).values
    x_safe = np.where(x > 0, x, np.nan)

    L = linalg.inv(np.eye(n) - A.values)

    numerator = L @ (L @ f_aligned)
    U = numerator / x_safe

    result = pd.Series(np.nan_to_num(U, nan=1.0), index=sectors, name="upstreamness")
    result = result.clip(lower=1.0)

    logger.info(f"Upstreamness: mean={result.mean():.2f}, range=[{result.min():.2f}, {result.max():.2f}]")
    return result


def downstreamness_index(
    A: pd.DataFrame,
    value_added: pd.DataFrame,
    total_output: pd.Series,
) -> pd.Series:
    """Compute downstreamness (distance from primary inputs) via Ghosh dual.

    D_i = [sum_k k * (va' * B^{k-1})_i] / x_i
    Efficient: D = (va' * G * G) / x  (G^2 property)

    Higher D = further downstream from primary inputs.

    Args:
        A: Direct requirements matrix.
        value_added: VA DataFrame (rows = components, cols = sectors).
        total_output: Total output by sector.

    Returns:
        Series of downstreamness values >= 1.
    """
    n = A.shape[0]
    sectors = A.index

    x = total_output.reindex(sectors).fillna(0).values
    x_safe = np.where(x > 0, x, np.nan)

    if isinstance(value_added, pd.DataFrame):
        va = value_added.sum(axis=0).reindex(sectors).fillna(0).values
    else:
        va = value_added.reindex(sectors).fillna(0).values

    # Ghosh model: B = x_hat^{-1} * Z, G = (I - B)^{-1}
    # Approximate B from A: B_ij = A_ij * x_j / x_i
    x_inv = np.where(x > 0, 1.0 / x, 0)
    B = A.values * x[np.newaxis, :] * x_inv[:, np.newaxis]

    try:
        G = linalg.inv(np.eye(n) - B)
        numerator = va @ G @ G
        D = numerator / x_safe
        result = pd.Series(np.nan_to_num(D, nan=1.0), index=sectors, name="downstreamness")
        result = result.clip(lower=1.0)
    except linalg.LinAlgError:
        result = pd.Series(1.0, index=sectors, name="downstreamness")
        logger.warning("Ghosh inverse singular; returning unit downstreamness")

    return result


def gvc_position_index(
    upstreamness: pd.Series,
    downstreamness: pd.Series,
) -> pd.DataFrame:
    """Compute net GVC position.

    Net position = downstreamness - upstreamness.
    Positive = more downstream (closer to consumers).
    Negative = more upstream (closer to raw materials).

    Args:
        upstreamness: Upstreamness values.
        downstreamness: Downstreamness values.

    Returns:
        DataFrame with upstreamness, downstreamness, net_position, gvc_length.
    """
    common = upstreamness.index.intersection(downstreamness.index)
    u = upstreamness.reindex(common)
    d = downstreamness.reindex(common)

    return pd.DataFrame({
        "upstreamness": u,
        "downstreamness": d,
        "net_position": d - u,
        "gvc_length": u + d,
    }).sort_values("upstreamness", ascending=False)


def gvc_position_timeseries(
    data_by_year: Dict[int, dict],
) -> pd.DataFrame:
    """Track upstreamness for all sectors across years.

    Args:
        data_by_year: Dict of year -> data dict.

    Returns:
        DataFrame with year x sector upstreamness values.
    """
    results = {}
    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        A = d.get("A_matrix")
        fd = d.get("final_demand")
        x = d.get("total_output")
        if A is None or A.empty:
            continue

        if isinstance(fd, pd.DataFrame):
            f = fd.sum(axis=1)
        else:
            f = fd

        u = antras_chor_upstreamness(A, f, x)
        results[year] = u

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results).T
    df.index.name = "year"
    return df
