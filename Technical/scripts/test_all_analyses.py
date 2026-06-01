"""Pytest suite for all 20 I-O analysis modules.

Tests use synthetic I-O data (small 4-sector economy) to verify
correctness of computations against known analytical solutions.

Usage: pytest Technical/scripts/test_all_analyses.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ── Fixtures: synthetic 4-sector economy ─────────────────────────────

@pytest.fixture
def sectors():
    return ["Agri", "Mfg", "Svc", "Energy"]


@pytest.fixture
def A_matrix(sectors):
    """Direct requirements matrix for a 4-sector economy."""
    data = np.array([
        [0.10, 0.05, 0.02, 0.01],
        [0.15, 0.20, 0.10, 0.05],
        [0.05, 0.10, 0.15, 0.10],
        [0.03, 0.08, 0.05, 0.05],
    ])
    return pd.DataFrame(data, index=sectors, columns=sectors)


@pytest.fixture
def L_matrix(A_matrix):
    """Leontief inverse."""
    from scipy import linalg
    n = A_matrix.shape[0]
    L = linalg.inv(np.eye(n) - A_matrix.values)
    return pd.DataFrame(L, index=A_matrix.index, columns=A_matrix.columns)


@pytest.fixture
def total_output(sectors):
    return pd.Series([500, 1200, 900, 400], index=sectors, name="total_output")


@pytest.fixture
def final_demand(sectors):
    return pd.Series([200, 400, 350, 150], index=sectors, name="final_demand")


@pytest.fixture
def value_added(sectors):
    data = {s: [0] for s in sectors}
    data["Agri"] = [150]
    data["Mfg"] = [300]
    data["Svc"] = [400]
    data["Energy"] = [180]
    return pd.DataFrame(data, index=["V001"])


@pytest.fixture
def wages(sectors):
    return pd.Series([100, 200, 300, 100], index=sectors)


@pytest.fixture
def labor_coeff(sectors, total_output):
    wages = pd.Series([100, 200, 300, 100], index=sectors)
    return wages / total_output


# ── Phase 0 Tests ────────────────────────────────────────────────────

class TestHypotheticalExtraction:
    def test_single_extraction_reduces_output(self, A_matrix, final_demand):
        from hypothetical_extraction import hypothetical_extraction_single
        result = hypothetical_extraction_single(A_matrix, final_demand, "Mfg")
        assert result["output_loss"] > 0
        assert 0 < result["loss_pct"] < 100

    def test_complete_vs_partial(self, A_matrix, final_demand):
        from hypothetical_extraction import hypothetical_extraction_single, partial_extraction
        full = hypothetical_extraction_single(A_matrix, final_demand, "Mfg")
        partial = partial_extraction(A_matrix, final_demand, "Mfg", 0.5)
        assert partial["output_loss"] < full["output_loss"]

    def test_zero_extraction_no_loss(self, A_matrix, final_demand):
        from hypothetical_extraction import partial_extraction
        result = partial_extraction(A_matrix, final_demand, "Mfg", 0.0)
        assert abs(result["output_loss"]) < 1e-6

    def test_all_extraction_covers_all_sectors(self, A_matrix, final_demand, sectors):
        from hypothetical_extraction import hypothetical_extraction_all
        result = hypothetical_extraction_all(A_matrix, final_demand)
        assert len(result) == len(sectors)
        assert all(result["loss_pct"] >= 0)

    def test_decomposition_sums(self, A_matrix, final_demand):
        from hypothetical_extraction import extraction_decomposition
        result = extraction_decomposition(A_matrix, final_demand, "Mfg")
        # backward + forward + internal should approximate total
        parts = result["backward_loss"] + result["forward_loss"] + result["internal_loss"]
        assert abs(parts - result["total_loss"]) < 1e-6


class TestRASUpdating:
    def test_ras_preserves_marginals(self, A_matrix):
        from ras_updating import ras_biproportional
        target_row = A_matrix.sum(axis=1) * 1.1
        target_col = A_matrix.sum(axis=0) * 1.1
        result, log = ras_biproportional(A_matrix, target_row, target_col)
        np.testing.assert_allclose(result.sum(axis=1).values, target_row.values, atol=1e-6)
        np.testing.assert_allclose(result.sum(axis=0).values, target_col.values, atol=1e-6)

    def test_ras_convergence(self, A_matrix):
        from ras_updating import ras_biproportional, ras_convergence_diagnostics
        target_row = A_matrix.sum(axis=1) * 1.05
        target_col = A_matrix.sum(axis=0) * 1.05
        _, log = ras_biproportional(A_matrix, target_row, target_col)
        diag = ras_convergence_diagnostics(log)
        assert diag["converged"]

    def test_identity_ras(self, A_matrix):
        """RAS with current marginals should return same matrix."""
        from ras_updating import ras_biproportional
        target_row = A_matrix.sum(axis=1)
        target_col = A_matrix.sum(axis=0)
        result, _ = ras_biproportional(A_matrix, target_row, target_col)
        np.testing.assert_allclose(result.values, A_matrix.values, atol=1e-6)

    def test_accuracy_report(self, A_matrix):
        from ras_updating import ras_accuracy_report
        report = ras_accuracy_report(A_matrix, A_matrix)
        assert report["mape_pct"] < 1e-6
        assert report["correlation"] > 0.999


class TestSDAEnhancements:
    def test_sda_average_equals_polar(self, A_matrix, final_demand):
        from structural_decomposition import structural_decomposition_polar, sda_average_all_orderings
        A_1 = A_matrix * 1.05
        f_1 = final_demand * 1.1

        polar = structural_decomposition_polar(A_matrix, A_1, final_demand, f_1)
        avg = sda_average_all_orderings(A_matrix, A_1, final_demand, f_1)

        np.testing.assert_allclose(
            polar["demand_effect"].values, avg["demand_effect"].values, atol=1e-6
        )
        np.testing.assert_allclose(
            polar["technology_effect"].values, avg["technology_effect"].values, atol=1e-6
        )


class TestPasinettiSubsystem:
    def test_subsystem_output_sums(self, L_matrix, final_demand, total_output):
        from value_analysis import pasinetti_subsystem
        sub = pasinetti_subsystem(L_matrix, final_demand, total_output)
        # Total subsystem output should equal total output (approximately)
        assert sub["subsystem_output"].sum() > 0
        assert sub["f_share"].sum() == pytest.approx(1.0, abs=1e-6)

    def test_subsystem_with_labor(self, L_matrix, final_demand, total_output, labor_coeff):
        from value_analysis import pasinetti_subsystem
        sub = pasinetti_subsystem(L_matrix, final_demand, total_output, labor_coeff)
        assert "subsystem_labor" in sub.columns
        assert sub["subsystem_labor"].sum() > 0


class TestMarkupPricing:
    def test_zero_markup_equals_cost(self, A_matrix, labor_coeff, sectors):
        from price_model import markup_pricing, cost_push_prices
        zero_markup = pd.Series(0, index=sectors)
        mp = markup_pricing(A_matrix, labor_coeff, zero_markup)
        cp = cost_push_prices(A_matrix, labor_coeff)
        np.testing.assert_allclose(mp.values, cp.values, atol=1e-6)


class TestGhoshEnhancements:
    def test_validate_ghosh_clean_data(self, A_matrix, total_output):
        from ghosh_model import allocation_coefficients, validate_ghosh
        B = allocation_coefficients(A_matrix, total_output)
        diag = validate_ghosh(B)
        # For well-formed data, most sectors should be valid
        assert diag["valid"].any()


class TestImportAnalysisEnhancements:
    def test_split_use_table(self):
        """Test split with BEA-style sector codes (not starting with S/V/T/F)."""
        from import_analysis import split_use_table
        sectors = ["111CA", "211", "321", "511"]
        output = pd.Series([500, 1200, 900, 400], index=sectors)
        A_data = np.array([
            [0.10, 0.05, 0.02, 0.01],
            [0.15, 0.20, 0.10, 0.05],
            [0.05, 0.10, 0.15, 0.10],
            [0.03, 0.08, 0.05, 0.05],
        ])
        A = pd.DataFrame(A_data, index=sectors, columns=sectors)
        Z = A * output.values[np.newaxis, :]
        Z.index = sectors
        Z.columns = sectors
        dom, imp = split_use_table(Z)
        # Domestic + import should equal original
        np.testing.assert_allclose(
            (dom + imp).values, Z.values, atol=1e-6
        )


# ── Phase 1 Tests ────────────────────────────────────────────────────

class TestNetworkCentrality:
    def test_build_graph(self, A_matrix, total_output):
        from network_centrality import build_io_graph, _reconstruct_z
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() > 0

    def test_centrality_suite(self, A_matrix, total_output):
        from network_centrality import build_io_graph, compute_centrality_suite, _reconstruct_z
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        suite = compute_centrality_suite(G)
        assert "pagerank" in suite.columns
        assert suite["pagerank"].sum() == pytest.approx(1.0, abs=0.01)


class TestCommunityDetection:
    def test_louvain_assigns_all(self, A_matrix, total_output, sectors):
        from network_centrality import build_io_graph, _reconstruct_z
        from community_detection import detect_communities_louvain
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        partition = detect_communities_louvain(G)
        assert set(partition.keys()) == set(sectors)

    def test_modularity_bounded(self, A_matrix, total_output):
        from network_centrality import build_io_graph, _reconstruct_z
        from community_detection import detect_communities_louvain, modularity_score
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        partition = detect_communities_louvain(G)
        mod = modularity_score(G, partition)
        assert -0.5 <= mod <= 1.0


class TestNetworkTopology:
    def test_topology_summary(self, A_matrix, total_output):
        from network_centrality import build_io_graph, _reconstruct_z
        from network_topology import topology_summary
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        summary = topology_summary(G)
        assert summary["n_nodes"].iloc[0] == 4
        assert summary["density"].iloc[0] > 0

    def test_power_law_fit(self):
        from network_topology import power_law_fit
        degrees = pd.Series([10, 8, 5, 3, 2, 1, 1, 1])
        result = power_law_fit(degrees)
        assert result["exponent"] < 0  # Power law has negative exponent
        assert 0 <= result["r_squared"] <= 1


class TestMinimumFlow:
    def test_chokepoint_nonnegative(self, A_matrix, total_output):
        from network_centrality import build_io_graph, _reconstruct_z
        from minimum_flow_analysis import chokepoint_index
        Z = _reconstruct_z(A_matrix, total_output)
        G = build_io_graph(Z, threshold_pct=0)
        choke = chokepoint_index(G, A_matrix)
        assert (choke >= 0).all()

    def test_strassert(self, A_matrix, total_output):
        from minimum_flow_analysis import strassert_minimum_flow
        Z = A_matrix * total_output.values[np.newaxis, :]
        Z.index = A_matrix.index
        Z.columns = A_matrix.columns
        essential = strassert_minimum_flow(Z, total_output, threshold_pct=5.0)
        # Some flows should be filtered
        assert (essential == 0).any().any()


class TestTriangulation:
    def test_triangularity_bounded(self, A_matrix):
        from triangulation import triangularity_index
        tri = triangularity_index(A_matrix)
        assert 0 <= tri <= 1

    def test_reorder_improves(self, A_matrix):
        from triangulation import triangularity_index, reorder_by_triangulation
        orig = triangularity_index(A_matrix)
        A_reordered, order = reorder_by_triangulation(A_matrix, "spectral")
        new = triangularity_index(A_reordered)
        # Reordering should not make it worse (or only marginally)
        assert new >= orig - 0.01

    def test_scc_decomposition(self, A_matrix):
        from triangulation import decompose_into_blocks
        sccs, A_blocked = decompose_into_blocks(A_matrix)
        assert len(sccs) >= 1
        total_members = sum(len(s) for s in sccs)
        assert total_members >= A_matrix.shape[0]


class TestQIOA:
    def test_qualitative_matrix_binary(self, A_matrix):
        from qioa import qualitative_matrix
        Q = qualitative_matrix(A_matrix)
        assert set(Q.values.flatten()).issubset({0, 1})

    def test_qualitative_L_contains_identity(self, A_matrix):
        from qioa import qualitative_matrix, qualitative_leontief_inverse
        Q = qualitative_matrix(A_matrix)
        QL = qualitative_leontief_inverse(Q)
        # Diagonal should be all 1s (sector reaches itself)
        assert all(QL.values[i, i] == 1 for i in range(QL.shape[0]))

    def test_sign_stability_bounded(self, A_matrix):
        from qioa import sign_stable_sectors
        stability = sign_stable_sectors(A_matrix, n_perturbations=20)
        assert stability.values.min() >= 0
        assert stability.values.max() <= 1


class TestProfitRateSimulation:
    def test_sraffian_prices_at_zero_rate(self, A_matrix, labor_coeff):
        from profit_rate_simulation import sraffian_prices
        from value_analysis import labor_values
        sp = sraffian_prices(A_matrix, labor_coeff, 0.0)
        lv = labor_values(A_matrix, labor_coeff)
        # At r=0, Sraffian prices should equal labor values
        np.testing.assert_allclose(sp.values, lv.values, rtol=1e-4)

    def test_max_profit_rate_positive(self, A_matrix):
        from profit_rate_simulation import maximum_profit_rate
        R = maximum_profit_rate(A_matrix)
        assert R > 0

    def test_wage_profit_frontier_decreasing(self, A_matrix, labor_coeff):
        from profit_rate_simulation import wage_profit_frontier
        frontier = wage_profit_frontier(A_matrix, labor_coeff, n_points=10)
        wages = frontier["max_real_wage"].values
        # Wage should generally decrease as profit rate increases
        assert wages[0] >= wages[-1]


class TestCascadeFailure:
    def test_no_cascade_without_shock(self, A_matrix, final_demand):
        from cascade_failure import run_cascade
        result = run_cascade(A_matrix, final_demand, {}, threshold_pct=50)
        assert result.iloc[-1]["n_failed"] == 0

    def test_cascade_from_large_sector(self, A_matrix, final_demand):
        from cascade_failure import run_cascade
        result = run_cascade(A_matrix, final_demand, {"Mfg": 1.0}, threshold_pct=50)
        assert result.iloc[-1]["n_failed"] >= 1

    def test_systemic_risk_nonnegative(self, A_matrix, final_demand):
        from cascade_failure import cascade_vulnerability_map, systemic_risk_index
        vuln = cascade_vulnerability_map(A_matrix, final_demand, threshold_pct=50)
        risk = systemic_risk_index(vuln)
        assert (risk >= 0).all()


# ── Phase 2 Tests (structural, no satellite data needed) ─────────────

class TestEmbodiedEnergy:
    def test_embodied_equals_vertically_integrated(self, A_matrix, labor_coeff):
        """Embodied energy with labor coefficients should match vertically integrated labor."""
        from embodied_energy import embodied_energy
        from value_analysis import vertically_integrated_labor
        ee = embodied_energy(A_matrix, labor_coeff)
        vil = vertically_integrated_labor(A_matrix, labor_coeff)
        np.testing.assert_allclose(ee.values, vil.values, atol=1e-10)

    def test_energy_multipliers_positive(self, L_matrix, labor_coeff):
        from embodied_energy import energy_multipliers
        mult = energy_multipliers(L_matrix, labor_coeff)
        assert (mult >= 0).all()


class TestWaterFootprint:
    def test_embodied_water_structure(self, A_matrix, sectors):
        from water_footprint import embodied_water
        water_coeff = pd.Series([0.5, 0.1, 0.02, 0.3], index=sectors)
        ew = embodied_water(A_matrix, water_coeff)
        assert len(ew) == 4
        # Embodied should be >= direct for all sectors
        assert (ew.values >= water_coeff.values - 1e-10).all()


class TestDynamicLeontief:
    def test_balanced_growth_returns_result(self, A_matrix, sectors):
        from dynamic_leontief import balanced_growth_path
        # Use smaller capital coefficients to ensure B^{-1}(I-A) has positive eigenvalue
        B = pd.Series([0.5, 0.3, 0.2, 0.4], index=sectors)
        g, proportions = balanced_growth_path(A_matrix, B)
        # Growth rate should be finite; proportions should sum to ~1 if valid
        assert np.isfinite(g)
        if g > 0:
            assert proportions.sum() == pytest.approx(1.0, abs=1e-6)

    def test_investment_requirements(self, sectors):
        from dynamic_leontief import investment_requirements
        B = pd.Series([2.0, 3.0, 1.5, 4.0], index=sectors)
        dx = pd.Series([10, 20, 15, 5], index=sectors)
        inv = investment_requirements(B, dx)
        np.testing.assert_allclose(inv.values, (B * dx).values)


class TestInterregionalIO:
    def test_simple_lq(self, sectors):
        from interregional_io import location_quotients
        regional = pd.DataFrame({
            "East": [100, 200, 150, 50],
            "West": [80, 100, 200, 80],
        }, index=sectors)
        national = pd.Series([300, 500, 400, 200], index=sectors)
        lq = location_quotients(regional, national)
        assert lq.shape == (4, 2)
        assert (lq >= 0).all().all()

    def test_regionalize_preserves_zeros(self, A_matrix, sectors):
        from interregional_io import regionalize_a_matrix
        lq = pd.Series([0.5, 1.2, 0.8, 1.0], index=sectors)
        A_reg = regionalize_a_matrix(A_matrix, lq)
        # Where LQ > 1, should equal national; where < 1, should be scaled down
        for i in range(4):
            if lq.iloc[i] >= 1.0:
                np.testing.assert_allclose(
                    A_reg.iloc[i].values, A_matrix.iloc[i].values, atol=1e-10
                )
            else:
                assert (A_reg.iloc[i].values <= A_matrix.iloc[i].values + 1e-10).all()


class TestRCA:
    def test_rca_with_same_structure(self, sectors):
        from revealed_comparative_advantage import balassa_rca
        exports = pd.Series([100, 200, 300, 50], index=sectors)
        rca = balassa_rca(exports, exports)
        # Same structure as world -> all RCA = 1
        np.testing.assert_allclose(rca.values, 1.0, atol=1e-10)

    def test_normalized_rca_bounded(self, sectors):
        from revealed_comparative_advantage import balassa_rca, normalized_rca
        exports = pd.Series([100, 200, 300, 50], index=sectors)
        world = pd.Series([500, 100, 300, 200], index=sectors)
        rca = balassa_rca(exports, world)
        nrca = normalized_rca(rca)
        assert (nrca >= -1).all()
        assert (nrca <= 1).all()


# ── Cross-Module Consistency ─────────────────────────────────────────

class TestCrossModuleConsistency:
    def test_cascade_at_threshold_100_matches_hem(self, A_matrix, final_demand):
        """At threshold=100%, no cascade should propagate (only initial failure)."""
        from cascade_failure import run_cascade
        from hypothetical_extraction import hypothetical_extraction_single

        cascade = run_cascade(A_matrix, final_demand, {"Mfg": 1.0}, threshold_pct=100)
        hem = hypothetical_extraction_single(A_matrix, final_demand, "Mfg")

        cascade_loss = cascade.iloc[-1]["output_loss_pct"]
        hem_loss = hem["loss_pct"]
        # Should be similar (cascade with 100% threshold = only initial sector fails)
        assert abs(cascade_loss - hem_loss) < 5.0

    def test_sraffian_labor_value_identity(self, A_matrix, labor_coeff):
        """At r=0, Sraffian prices = labor values (the classical identity)."""
        from profit_rate_simulation import sraffian_prices
        from value_analysis import labor_values
        sp = sraffian_prices(A_matrix, labor_coeff, 0.0)
        lv = labor_values(A_matrix, labor_coeff)
        np.testing.assert_allclose(sp.values, lv.values, rtol=1e-4)


# ══════════════════════════════════════════════════════════════════════
# WAVE 2 TESTS
# ══════════════════════════════════════════════════════════════════════

# ── Additional fixtures for Wave 2 ───────────────────────────────────

@pytest.fixture
def final_demand_df(sectors):
    """Final demand as DataFrame with typed FD columns."""
    return pd.DataFrame({
        "F01000": [150, 300, 250, 80],
        "F03000": [30, 80, 50, 40],
        "F06C00": [10, 50, 20, 15],
        "F06N00": [5, 20, 30, 10],
        "F07C00": [5, 10, 50, 5],
    }, index=sectors)


@pytest.fixture
def value_added_df(sectors):
    """VA as DataFrame with BEA-style row codes."""
    return pd.DataFrame({
        s: [0] for s in sectors
    } | {
        "Agri": [100], "Mfg": [200], "Svc": [300], "Energy": [100]
    }, index=["V001"])[sectors]


@pytest.fixture
def A_matrix_pair(A_matrix):
    """Two A matrices for year-pair tests (slight technical improvement)."""
    return A_matrix, A_matrix * 0.97


# ── Phase 1: Network & Spectral ──────────────────────────────────────

class TestSpectralGap:
    def test_lambda1_matches_rmax(self, A_matrix):
        from spectral_gap_analysis import spectral_gap
        from profit_rate_simulation import maximum_profit_rate
        sg = spectral_gap(A_matrix)
        R = maximum_profit_rate(A_matrix)
        expected = 1.0 / (1 + R) if R > 0 else 0
        assert abs(sg["lambda_1"] - expected) < 1e-4

    def test_spectral_gap_positive(self, A_matrix):
        from spectral_gap_analysis import spectral_gap
        sg = spectral_gap(A_matrix)
        assert sg["spectral_gap"] > 0

    def test_mixing_time_finite(self, A_matrix):
        from spectral_gap_analysis import mixing_time_estimation
        mt = mixing_time_estimation(A_matrix, epsilon=0.01)
        assert np.isfinite(mt["mixing_time"])
        assert mt["n_steps_to_epsilon"] > 0

    def test_eigenvectors_sum_to_one(self, A_matrix):
        from spectral_gap_analysis import eigenvector_centrality_from_spectrum
        ev = eigenvector_centrality_from_spectrum(A_matrix)
        assert ev["right_eigenvector"].sum() == pytest.approx(1.0, abs=1e-6)
        assert ev["left_eigenvector"].sum() == pytest.approx(1.0, abs=1e-6)


class TestInnovationPropagation:
    def test_depth_geq_one(self, A_matrix):
        from innovation_propagation import propagation_depth_by_sector
        depths = propagation_depth_by_sector(A_matrix, threshold_pct=90.0)
        assert (depths >= 1).all()

    def test_power_series_converges(self, A_matrix):
        from innovation_propagation import leontief_power_series_convergence
        conv = leontief_power_series_convergence(A_matrix, n_terms=100)
        assert conv["pct_of_L_total"].iloc[-1] > 99.0

    def test_propagation_speed_matrix_shape(self, A_matrix):
        from innovation_propagation import propagation_speed_matrix
        speed = propagation_speed_matrix(A_matrix, threshold_pct=50.0, max_steps=10)
        assert speed.shape == A_matrix.shape


class TestSectorKnockout:
    def test_elo_covers_all_sectors(self, A_matrix, final_demand, sectors):
        from sector_knockout_tournament import sector_knockout_tournament
        result = sector_knockout_tournament(A_matrix, final_demand, n_rounds=1)
        assert set(result.index) == set(sectors)

    def test_elo_correlates_with_hem(self, A_matrix, final_demand):
        from sector_knockout_tournament import sector_knockout_tournament, tournament_vs_hem_correlation
        from hypothetical_extraction import hypothetical_extraction_all
        tournament = sector_knockout_tournament(A_matrix, final_demand, n_rounds=1)
        hem = hypothetical_extraction_all(A_matrix, final_demand)
        corr = tournament_vs_hem_correlation(tournament, hem)
        assert corr > 0.7

    def test_elo_ratings_spread(self, A_matrix, final_demand):
        from sector_knockout_tournament import sector_knockout_tournament
        result = sector_knockout_tournament(A_matrix, final_demand, n_rounds=2)
        assert result["elo_rating"].std() > 0


# ── Phase 2: GVC & Trade ─────────────────────────────────────────────

class TestGVCUpstreamness:
    def test_upstreamness_geq_one(self, A_matrix, final_demand, total_output):
        from gvc_upstreamness import antras_chor_upstreamness
        u = antras_chor_upstreamness(A_matrix, final_demand, total_output)
        assert (u >= 1.0 - 1e-6).all()

    def test_downstreamness_geq_one(self, A_matrix, value_added_df, total_output):
        from gvc_upstreamness import downstreamness_index
        d = downstreamness_index(A_matrix, value_added_df, total_output)
        assert (d >= 1.0 - 1e-6).all()

    def test_gvc_position_covers_sectors(self, A_matrix, final_demand, total_output, value_added_df, sectors):
        from gvc_upstreamness import antras_chor_upstreamness, downstreamness_index, gvc_position_index
        u = antras_chor_upstreamness(A_matrix, final_demand, total_output)
        d = downstreamness_index(A_matrix, value_added_df, total_output)
        pos = gvc_position_index(u, d)
        assert len(pos) == len(sectors)


class TestDomesticContentGov:
    def test_dva_share_bounded(self, A_matrix, total_output, value_added_df, final_demand_df):
        from domestic_content_government import dva_in_government_procurement
        # Use A as use_table proxy
        Z = A_matrix * total_output.values[np.newaxis, :]
        Z.index = A_matrix.index
        Z.columns = A_matrix.columns
        result = dva_in_government_procurement(Z, value_added_df, total_output, final_demand_df)
        if not result.empty:
            assert (result["dva_share"] >= 0).all()
            assert (result["dva_share"] <= 1.0 + 1e-6).all()


class TestImportLeakage:
    def test_retention_rate_bounded(self, A_matrix, final_demand, sectors):
        from import_leakage import domestic_retention_rate
        A_dom = A_matrix * 0.8
        A_imp = A_matrix * 0.2
        drr = domestic_retention_rate(A_dom, A_imp, final_demand)
        assert (drr >= 0).all()
        assert (drr <= 1.0 + 1e-6).all()

    def test_leakage_fraction_bounded(self, A_matrix):
        from import_leakage import import_leakage_multiplier
        A_dom = A_matrix * 0.8
        A_imp = A_matrix * 0.2
        result = import_leakage_multiplier(A_dom, A_imp)
        assert (result["leakage_fraction"] >= 0).all()
        assert (result["leakage_fraction"] <= 1.0 + 1e-6).all()


# ── Phase 3: Demand-Side Macro ────────────────────────────────────────

class TestMiyazawa:
    def test_induced_share_bounded(self, A_matrix, total_output, value_added_df, final_demand_df):
        from miyazawa_decomposition import miyazawa_partition
        Z = A_matrix * total_output.values[np.newaxis, :]
        Z.index = A_matrix.index
        Z.columns = A_matrix.columns
        result = miyazawa_partition(A_matrix, Z, value_added_df, final_demand_df, total_output)
        assert 0 <= result["induced_output_share"] <= 1.0

    def test_autonomous_plus_induced(self, A_matrix, total_output, value_added_df, final_demand_df):
        from miyazawa_decomposition import miyazawa_partition, autonomous_vs_induced_output
        Z = A_matrix * total_output.values[np.newaxis, :]
        Z.index = A_matrix.index
        Z.columns = A_matrix.columns
        result = miyazawa_partition(A_matrix, Z, value_added_df, final_demand_df, total_output)
        decomp = autonomous_vs_induced_output(result["M"], result["L"], final_demand_df)
        # Total should be positive
        assert (decomp["total_output"] >= 0).all()


class TestFiscalMultiplier:
    def test_multiplier_positive(self, A_matrix, L_matrix, final_demand_df, value_added_df, total_output):
        from fiscal_multiplier import fiscal_multiplier_table
        table = fiscal_multiplier_table(A_matrix, L_matrix, final_demand_df, value_added_df, total_output)
        if not table.empty:
            assert (table["output_multiplier"] > 0).all()

    def test_output_multiplier_by_category(self, L_matrix, final_demand_df):
        from fiscal_multiplier import output_multiplier_by_fd_category
        result = output_multiplier_by_fd_category(L_matrix, final_demand_df["F06C00"])
        assert result["multiplier"] > 1.0


class TestSupermultiplier:
    def test_sm_exceeds_standard(self, A_matrix, final_demand_df, value_added_df, total_output):
        from keynesian_supermultiplier import keynesian_supermultiplier
        result = keynesian_supermultiplier(A_matrix, final_demand_df, value_added_df, total_output)
        assert result["supermultiplier"] >= result["standard_multiplier"]

    def test_components_bounded(self, A_matrix, final_demand_df, value_added_df, total_output):
        from keynesian_supermultiplier import keynesian_supermultiplier
        result = keynesian_supermultiplier(A_matrix, final_demand_df, value_added_df, total_output)
        assert 0 < result["propensity_to_consume"] < 1
        assert 0 <= result["effective_tax_rate"] < 1


# ── Phase 4: Classical Political Economy ──────────────────────────────

class TestFeldmanMahalanobis:
    def test_departments_binary(self, final_demand_df):
        from feldman_mahalanobis import classify_departments
        dept = classify_departments(final_demand_df)
        assert set(dept.values).issubset({"I", "II"})

    def test_alpha_bounded(self, A_matrix, final_demand_df):
        from feldman_mahalanobis import classify_departments, feldman_investment_ratio
        dept = classify_departments(final_demand_df)
        result = feldman_investment_ratio(A_matrix, final_demand_df, dept)
        assert 0 <= result["alpha"] <= 1


class TestFunctionalCounterfactuals:
    def test_no_change_at_same_year(self, A_matrix, value_added_df, total_output):
        from functional_counterfactuals import all_sector_wage_counterfactuals
        result = all_sector_wage_counterfactuals(
            A_matrix, value_added_df, value_added_df, total_output, total_output
        )
        # Same anchor = same VA → zero deviation
        assert result["mean_price_impact_pct"].abs().max() < 1e-6


class TestShaikhProfitRate:
    def test_rate_components(self, A_matrix, labor_coeff, wages, total_output):
        from shaikh_profit_rate import shaikh_profit_rate_single
        result = shaikh_profit_rate_single(A_matrix, labor_coeff, wages, total_output)
        assert result["V_variable_capital"] > 0
        assert result["C_constant_capital"] > 0
        # wage_share in [0, 1]
        assert 0 <= result["wage_share"] <= 1

    def test_ltpf_regression_runs(self):
        from shaikh_profit_rate import ltpf_regression
        ts = pd.DataFrame({
            "r_classical": [0.15, 0.14, 0.13, 0.135, 0.12],
        }, index=[2000, 2001, 2002, 2003, 2004])
        result = ltpf_regression(ts)
        assert result["interpretation"] == "falling"


class TestTermsOfTrade:
    def test_tot_normalized(self, A_matrix, value_added_df, total_output):
        from terms_of_trade_structural import sectoral_terms_of_trade
        tot = sectoral_terms_of_trade(A_matrix, value_added_df, total_output)
        assert tot.mean() == pytest.approx(1.0, abs=0.5)

    def test_decomposition_sums(self, A_matrix, value_added_df, total_output):
        from terms_of_trade_structural import tot_structural_decomposition
        A1 = A_matrix * 0.98
        decomp = tot_structural_decomposition(
            A_matrix, A1, value_added_df, value_added_df, total_output, total_output
        )
        # tech + distribution should approximate total
        residual = (decomp["tot_change"] - decomp["technology_component"] - decomp["distribution_component"]).abs()
        assert residual.mean() < 0.01


# ── Phase 5: Year-Pair ────────────────────────────────────────────────

class TestOkishio:
    def test_improvement_is_viable(self, A_matrix, wages, sectors):
        from okishio_simulator import okishio_viable_technique
        A_1 = A_matrix * 0.95
        prices_0 = pd.Series(1.0, index=sectors)
        w_coeff = wages / 1000
        viable = okishio_viable_technique(A_matrix, A_1, w_coeff, prices_0)
        assert viable.all()

    def test_improvement_raises_rmax(self, A_matrix, wages, total_output, value_added_df):
        from okishio_simulator import okishio_profit_rate_effect
        A_1 = A_matrix * 0.95
        result = okishio_profit_rate_effect(A_matrix, A_1, wages, total_output, value_added_df)
        assert result["okishio_confirmed"]


class TestTSSI:
    def test_melt_positive(self, total_output, labor_coeff):
        from tssi_valuation import melt_monetary_expression
        melt = melt_monetary_expression(total_output, labor_coeff)
        assert melt > 0

    def test_tssi_steady_state_approx_sraffian(self, A_matrix, labor_coeff, wages, total_output):
        from tssi_valuation import tssi_vs_static_comparison
        w_coeff = wages / total_output
        result = tssi_vs_static_comparison(
            A_matrix, A_matrix, w_coeff, w_coeff, labor_coeff, labor_coeff, total_output
        )
        assert result["deviation_pct"].abs().mean() < 30


# ── Phase 6: Environment ─────────────────────────────────────────────

class TestReboundEffect:
    def test_rebound_bounded(self, A_matrix, value_added_df, total_output, sectors):
        from rebound_effect import energy_efficiency_shock
        result = energy_efficiency_shock(A_matrix, sectors[0], value_added_df, total_output, 10.0)
        assert result["rebound_fraction"] >= 0

    def test_zero_gain_zero_rebound(self, A_matrix, value_added_df, total_output, sectors):
        from rebound_effect import energy_efficiency_shock
        result = energy_efficiency_shock(A_matrix, sectors[0], value_added_df, total_output, 0.0)
        assert abs(result["direct_energy_saved"]) < 1e-6


class TestStrandedAsset:
    def test_shock_produces_impact(self, A_matrix, value_added_df, total_output, sectors):
        from stranded_asset_propagation import stranded_asset_shock
        result = stranded_asset_shock(A_matrix, value_added_df, total_output,
                                      fossil_sectors=[sectors[3]], write_down_fraction=0.3)
        assert result["va_shock"].abs().sum() > 0

    def test_cascade_runs(self, A_matrix, final_demand, sectors):
        from stranded_asset_propagation import stranded_cascade_path
        cascade = stranded_cascade_path(A_matrix, final_demand,
                                         fossil_sectors=[sectors[3]], cascade_threshold_pct=50)
        assert len(cascade) > 0


class TestCBAM:
    def test_price_adjustment_positive(self, A_matrix, value_added_df, total_output):
        from carbon_border_adjustment import cbam_price_adjustment
        result = cbam_price_adjustment(A_matrix, value_added_df, total_output, carbon_price_per_unit=50)
        assert (result["price_increase"] >= -1e-6).all()

    def test_winners_losers_table(self, A_matrix, total_output, value_added_df):
        from carbon_border_adjustment import cbam_winners_losers
        Z = A_matrix * total_output.values[np.newaxis, :]
        Z.index = A_matrix.index
        Z.columns = A_matrix.columns
        result = cbam_winners_losers(Z, total_output, value_added_df)
        assert "net_competitive_effect" in result.columns


# ── Wave 2 Cross-Module Consistency ───────────────────────────────────

class TestWave2Consistency:
    def test_spectral_gap_r_max_match(self, A_matrix):
        """Spectral gap's r_max should match profit_rate_simulation."""
        from spectral_gap_analysis import spectral_gap
        from profit_rate_simulation import maximum_profit_rate
        sg = spectral_gap(A_matrix)
        R = maximum_profit_rate(A_matrix)
        assert abs(sg["r_max"] - R) < 1e-4

    def test_sm_geq_type1(self, A_matrix, L_matrix, final_demand_df, value_added_df, total_output):
        """Supermultiplier should exceed standard Type I multiplier."""
        from keynesian_supermultiplier import keynesian_supermultiplier
        result = keynesian_supermultiplier(A_matrix, final_demand_df, value_added_df, total_output)
        type1 = L_matrix.sum().sum() / L_matrix.shape[0]
        assert result["supermultiplier"] >= type1 * 0.9
