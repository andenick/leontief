"""Sector knockout tournament: Elo-style pairwise HEM ranking.

Runs a round-robin tournament where each pair of sectors is compared
by their hypothetical extraction output loss. Produces an Elo rating
that captures ordinal importance beyond simple cardinal HEM measures.

Reference: Elo (1978); Miller & Blair Ch. 12.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def elo_update(
    rating_winner: float,
    rating_loser: float,
    k_factor: float = 32.0,
) -> Tuple[float, float]:
    """Standard Elo rating update.

    Args:
        rating_winner: Current rating of the winner.
        rating_loser: Current rating of the loser.
        k_factor: Adjustment speed.

    Returns:
        Tuple of (new_winner_rating, new_loser_rating).
    """
    expected_winner = 1.0 / (1.0 + 10 ** ((rating_loser - rating_winner) / 400.0))
    expected_loser = 1.0 - expected_winner

    new_winner = rating_winner + k_factor * (1.0 - expected_winner)
    new_loser = rating_loser + k_factor * (0.0 - expected_loser)

    return new_winner, new_loser


def sector_knockout_tournament(
    A: pd.DataFrame,
    f: pd.Series,
    initial_rating: float = 1500.0,
    k_factor: float = 32.0,
    n_rounds: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """Run Elo round-robin tournament across all sector pairs.

    Pre-computes HEM for all sectors once, then runs n_rounds of
    randomized pairwise matchups updating Elo ratings.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        initial_rating: Starting Elo for all sectors.
        k_factor: Elo K-factor.
        n_rounds: Number of full round-robin passes.
        seed: Random seed for matchup ordering.

    Returns:
        DataFrame with elo_rating, wins, losses, hem_loss_pct per sector.
    """
    from hypothetical_extraction import hypothetical_extraction_all

    hem = hypothetical_extraction_all(A, f)
    loss_dict = hem["loss_pct"].to_dict()

    sectors = list(A.index)
    n = len(sectors)
    ratings = {s: initial_rating for s in sectors}
    wins = {s: 0 for s in sectors}
    losses = {s: 0 for s in sectors}

    # Generate all pairs
    pairs = [(sectors[i], sectors[j]) for i in range(n) for j in range(i + 1, n)]

    rng = np.random.RandomState(seed)

    for round_num in range(n_rounds):
        rng.shuffle(pairs)
        for s_i, s_j in pairs:
            loss_i = loss_dict.get(s_i, 0)
            loss_j = loss_dict.get(s_j, 0)

            if loss_i > loss_j:
                winner, loser = s_i, s_j
            elif loss_j > loss_i:
                winner, loser = s_j, s_i
            else:
                continue

            new_w, new_l = elo_update(ratings[winner], ratings[loser], k_factor)
            ratings[winner] = new_w
            ratings[loser] = new_l
            wins[winner] += 1
            losses[loser] += 1

    result = pd.DataFrame({
        "elo_rating": pd.Series(ratings),
        "wins": pd.Series(wins),
        "losses": pd.Series(losses),
        "hem_loss_pct": hem["loss_pct"],
    })
    result = result.sort_values("elo_rating", ascending=False)
    result["elo_rank"] = range(1, len(result) + 1)

    logger.info(f"Tournament: {n_rounds} rounds, {len(pairs)} matchups each, top={result.index[0]}")
    return result


def tournament_vs_hem_correlation(
    tournament_result: pd.DataFrame,
    hem_result: pd.DataFrame,
) -> float:
    """Compute Spearman rank correlation between Elo and HEM rankings.

    Args:
        tournament_result: Output from sector_knockout_tournament.
        hem_result: Output from hypothetical_extraction_all.

    Returns:
        Spearman correlation coefficient (should be >0.9).
    """
    common = tournament_result.index.intersection(hem_result.index)
    elo_ranks = tournament_result.loc[common, "elo_rating"].rank(ascending=False)
    hem_ranks = hem_result.loc[common, "loss_pct"].rank(ascending=False)

    corr, _ = stats.spearmanr(elo_ranks.values, hem_ranks.values)
    logger.info(f"Elo-HEM Spearman correlation: {corr:.4f}")
    return float(corr)


def tournament_stability(
    A: pd.DataFrame,
    f: pd.Series,
    n_trials: int = 5,
    n_rounds: int = 3,
) -> pd.DataFrame:
    """Test stability of Elo rankings across different random seeds.

    Args:
        A: Direct requirements matrix.
        f: Final demand vector.
        n_trials: Number of independent tournaments.
        n_rounds: Rounds per tournament.

    Returns:
        DataFrame with mean_rating, std_rating, mean_rank, rank_stability per sector.
    """
    all_ratings = []
    for trial in range(n_trials):
        result = sector_knockout_tournament(A, f, n_rounds=n_rounds, seed=trial * 7 + 1)
        all_ratings.append(result["elo_rating"])

    ratings_df = pd.DataFrame(all_ratings)

    return pd.DataFrame({
        "mean_rating": ratings_df.mean(),
        "std_rating": ratings_df.std(),
        "cv_rating": ratings_df.std() / ratings_df.mean().replace(0, np.nan),
        "mean_rank": ratings_df.rank(axis=1, ascending=False).mean(),
    }).sort_values("mean_rating", ascending=False)
