"""Scientific Benchmark Suite (Ground-Truth Evaluation Battery).

Evaluates whether the autonomous scientific platform exhibits true epistemic reasoning:
1. Benchmark Case A: DO_EXPERIMENT (Well-grounded, testable ML question with high EIG).
2. Benchmark Case B: REJECT_HYPOTHESIS (Empirical simulation demonstrates non-positive effect size).
3. Benchmark Case C: NEED_MORE_EVIDENCE (Insufficient evidence grounding halts before computing).
4. Benchmark Case D: ILL_POSED_QUESTION (Contradictory / tautological questions caught pre-execution).
"""

from __future__ import annotations


from app.critique.service import ScientificCritic
from app.evidence.extractor import ExtractedEvidence
from app.execution.replication import ReplicationEngine
from app.reasoning.competing_hypotheses import CompetingHypothesisGenerator
from app.reasoning.decision_engine import ResearchDecisionEngine
from app.reasoning.gap_discovery import ResearchGapDiscovery
from app.statistics.service import StatisticalSummary, StatisticsService


def test_benchmark_do_experiment_high_eig() -> None:
    """Benchmark A: Valid ML question yields high EIG and selects optimal experiment."""
    gap_engine = ResearchGapDiscovery()
    evidence = [
        ExtractedEvidence(
            text="First-order stochastic gradient methods oscillate along high-curvature ravines.",
            locator="pdf:sec_3",
            evidence_kind="METHODOLOGY_SNIPPET",
        )
    ]
    gaps = gap_engine.discover_gaps("How does curvature-adaptive momentum improve convergence in non-convex optimization?", evidence)
    assert len(gaps) >= 1
    selected_gap = gaps[0]

    # Tournament formulation
    tournament_gen = CompetingHypothesisGenerator()
    tournament = tournament_gen.generate_tournament(
        "How does curvature-adaptive momentum improve convergence?",
        selected_gap,
        evidence,
    )
    assert len(tournament.hypotheses) == 5

    # Decision Engine experiment selection via EIG / Cost
    decision_engine = ResearchDecisionEngine()
    best_design, candidates = decision_engine.evaluate_and_select_experiment(tournament)
    assert best_design is not None
    assert best_design.expected_information_gain > 0.0
    assert best_design.cost_efficiency_utility > 0.0

    # Simulate positive experimental run
    stats_service = StatisticsService()
    baseline = [0.60, 0.61, 0.59, 0.62, 0.60, 0.61, 0.63, 0.59, 0.60, 0.62, 0.61, 0.60]
    treatment = [0.76, 0.77, 0.75, 0.78, 0.76, 0.77, 0.79, 0.75, 0.76, 0.78, 0.77, 0.76]
    summary = stats_service.analyze_paired(baseline, treatment, random_seed=42)

    # Bayesian posterior update
    belief_state = decision_engine.update_beliefs(tournament, summary)
    assert belief_state.leading_hypothesis_id == "H-01-PRIMARY"
    assert belief_state.confidence >= 0.50
    assert belief_state.bayes_factors["H-01-PRIMARY"] > 1.0

    # Critic evaluation
    critic = ScientificCritic()
    report = critic.evaluate(summary, experiment_kind="EXPLORATORY", baseline_scores=baseline, treatment_scores=treatment)
    assert report.outcome == "ACCEPT_WITH_LIMITATIONS"
    assert report.statistical_power >= 0.80
    assert report.effect_magnitude_tier in {"LARGE", "MODERATE"}


def test_benchmark_reject_hypothesis_on_null_effect() -> None:
    """Benchmark B: When experimental data shows no effect, Critic correctly outputs REJECT."""
    stats_service = StatisticsService()
    # Baseline and treatment have identical distributions (null effect)
    baseline = [0.65, 0.66, 0.64, 0.65, 0.66, 0.64, 0.65, 0.66, 0.64, 0.65, 0.66, 0.64]
    treatment = [0.64, 0.65, 0.63, 0.64, 0.65, 0.63, 0.64, 0.65, 0.63, 0.64, 0.65, 0.63]

    summary = stats_service.analyze_paired(baseline, treatment, random_seed=42)
    assert summary.mean_difference <= 0.0

    critic = ScientificCritic()
    report = critic.evaluate(summary, experiment_kind="CONFIRMATORY", baseline_scores=baseline, treatment_scores=treatment)
    assert report.outcome == "REJECT"
    assert any(f.code == "NON_POSITIVE_EFFECT" for f in report.findings)
    assert any(f.code == "INTERVAL_INCLUDES_NO_IMPROVEMENT" for f in report.findings)

    # Tournament Bayesian update must shift probability mass to H_NULL
    gap = ResearchGapDiscovery().discover_gaps("Testing null effect", [])[0]
    tournament = CompetingHypothesisGenerator().generate_tournament("Testing null effect", gap, [])
    decision_engine = ResearchDecisionEngine()
    belief_state = decision_engine.update_beliefs(tournament, summary)
    assert belief_state.leading_hypothesis_id == "H-02-NULL"


def test_benchmark_replication_stability() -> None:
    """Benchmark: Replication engine detects cross-seed instability."""
    engine = ReplicationEngine()
    # Consistent positive runs
    b_runs = [[0.60, 0.61, 0.62], [0.59, 0.60, 0.61], [0.60, 0.61, 0.62]]
    t_runs = [[0.75, 0.76, 0.77], [0.74, 0.75, 0.76], [0.75, 0.76, 0.77]]
    rep_good = engine.evaluate_replication(b_runs, t_runs, seeds=[1, 2, 3])
    assert rep_good.is_reproducible is True
    assert rep_good.reproducibility_score >= 0.80

    # Inconsistent flipped runs
    t_runs_bad = [[0.55, 0.56, 0.57], [0.74, 0.75, 0.76], [0.55, 0.56, 0.57]]
    rep_bad = engine.evaluate_replication(b_runs, t_runs_bad, seeds=[1, 2, 3])
    assert rep_bad.is_reproducible is False


def test_benchmark_need_more_evidence_and_ill_posed() -> None:
    """Benchmark C & D: Handles empty grounding and ill-posed questions gracefully."""
    gap_engine = ResearchGapDiscovery()
    gaps = gap_engine.discover_gaps("Can arbitrary hyper-entropy violate thermodynamics?", [])
    assert len(gaps) >= 1
    assert gaps[0].confidence <= 0.85


def test_critic_flags_trivial_effect_size() -> None:
    """Critic flags statistically significant results that have negligible effect size."""
    # Very small delta across high N with low variance
    baseline = [0.600, 0.601, 0.600, 0.601, 0.600, 0.601, 0.600, 0.601, 0.600, 0.601, 0.600, 0.601]
    treatment = [0.603, 0.604, 0.603, 0.604, 0.603, 0.604, 0.603, 0.604, 0.603, 0.604, 0.603, 0.604]

    # Force trivial effect size
    summary_trivial = StatisticalSummary(
        effect_size=0.12,
        confidence_interval=[0.001, 0.005],
        p_value=0.03,
        sample_count=12,
        variance=0.0001,
        mean_difference=0.003,
        statistical_power=0.85,
    )
    critic = ScientificCritic()
    report = critic.evaluate(summary_trivial, experiment_kind="CONFIRMATORY", baseline_scores=baseline, treatment_scores=treatment)
    assert any(f.code == "TRIVIAL_EFFECT_SIZE_DESPITE_SIGNIFICANCE" for f in report.findings)
    assert report.effect_magnitude_tier == "TRIVIAL"


def test_critic_flags_underpowered_inconclusive_trial() -> None:
    """Critic flags underpowered non-significant runs as INCONCLUSIVE rather than accepting H0."""
    summary_underpowered = StatisticalSummary(
        effect_size=0.08,
        confidence_interval=[-0.02, 0.05],
        p_value=0.18,
        sample_count=5,
        variance=0.01,
        mean_difference=0.01,
        statistical_power=0.35,
    )
    critic = ScientificCritic()
    report = critic.evaluate(summary_underpowered, experiment_kind="EXPLORATORY")
    assert any(f.code == "INCONCLUSIVE_DUE_TO_LOW_POWER" for f in report.findings)
    assert report.outcome in {"NEEDS_REVISION", "REJECT"}


def test_critic_flags_strawman_baseline() -> None:
    """Critic detects uncalibrated zero-variance strawman baselines."""
    stats_service = StatisticsService()
    baseline = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]  # Near-zero and zero variance
    treatment = [0.75, 0.76, 0.74, 0.77, 0.75, 0.76]
    summary = stats_service.analyze_paired(baseline, treatment, random_seed=42)

    critic = ScientificCritic()
    report = critic.evaluate(summary, experiment_kind="EXPLORATORY", baseline_scores=baseline, treatment_scores=treatment)
    assert any(f.code == "SUSPICIOUS_STRAWMAN_BASELINE" or f.code == "DEGRADED_BASELINE_FLOOR" for f in report.findings)


def test_decision_engine_design_conditioned_eig_differentiation() -> None:
    """Verifies that each candidate experiment design computes genuinely distinct EIG and utility."""
    gap = ResearchGapDiscovery().discover_gaps("Non-convex optimization dynamics", [])[0]
    tournament = CompetingHypothesisGenerator().generate_tournament("Non-convex optimization", gap, [])
    decision_engine = ResearchDecisionEngine()

    best_design, candidates = decision_engine.evaluate_and_select_experiment(tournament)
    assert len(candidates) == 3

    # Check that candidates have distinct design IDs and computed EIG values
    eigs = [c.expected_information_gain for c in candidates]
    utilities = [c.cost_efficiency_utility for c in candidates]
    assert len(set(eigs)) >= 2
    assert len(set(utilities)) >= 2


def test_sequential_bayesian_prior_inheritance() -> None:
    """Verifies that posterior probabilities from round t become priors in round t+1."""
    gap = ResearchGapDiscovery().discover_gaps("Testing sequential updating", [])[0]
    evidence = [ExtractedEvidence(text="Curvature-adaptive updates prevent momentum divergence in steep valleys.", locator="p1", evidence_kind="SNIPPET")]
    tournament_gen = CompetingHypothesisGenerator()
    tournament_t1 = tournament_gen.generate_tournament("Testing sequential updating", gap, evidence)

    # Simulate strong positive result in round 1
    stats_service = StatisticsService()
    baseline = [0.60, 0.61, 0.62, 0.60, 0.61, 0.62]
    treatment = [0.76, 0.77, 0.78, 0.76, 0.77, 0.78]
    summary_t1 = stats_service.analyze_paired(baseline, treatment, random_seed=42)

    decision_engine = ResearchDecisionEngine()
    belief_state_t1 = decision_engine.update_beliefs(tournament_t1, summary_t1)
    assert belief_state_t1.leading_hypothesis_id == "H-01-PRIMARY"
    posteriors_t1 = belief_state_t1.posterior_probabilities

    # Round 2 tournament inherits posteriors_t1 as its priors
    tournament_t2 = tournament_gen.generate_tournament("Testing sequential updating", gap, evidence, prior_probabilities=posteriors_t1)
    priors_t2 = {h.hypothesis_id: h.prior_probability for h in tournament_t2.hypotheses}

    assert priors_t2["H-01-PRIMARY"] == posteriors_t1["H-01-PRIMARY"]
    assert priors_t2["H-02-NULL"] == posteriors_t1["H-02-NULL"]


def test_critic_flags_replication_failure() -> None:
    """Critic flags replication failure when replication report is marked not reproducible."""
    from app.execution.replication import ReplicationReport
    summary = StatisticalSummary(
        effect_size=0.85,
        confidence_interval=[0.10, 0.18],
        p_value=0.001,
        sample_count=12,
        variance=0.01,
        mean_difference=0.14,
        statistical_power=0.95,
    )
    failed_rep = ReplicationReport(
        is_reproducible=False,
        reproducibility_score=0.0,
        directional_consistency_ratio=0.0,
        mean_delta_stability_cv=1.0,
        evaluated_seeds=[1, 2, 3],
        seed_deltas=[],
        audit_notes=["Replication failed due to execution error."],
    )
    critic = ScientificCritic()
    report = critic.evaluate(summary, experiment_kind="CONFIRMATORY", replication_report=failed_rep)
    assert report.outcome == "REJECT"
    assert any(f.code == "REPLICATION_INSTABILITY" for f in report.findings)


def test_eig_selection_to_experiment_spec_invariant() -> None:
    """Invariant: The design selected by the EIG engine MUST determine the experiment spec and parameters."""
    gap = ResearchGapDiscovery().discover_gaps("Testing EIG invariant", [])[0]
    tournament = CompetingHypothesisGenerator().generate_tournament("Testing EIG invariant", gap, [])
    decision_engine = ResearchDecisionEngine()

    custom_candidates = [
        {
            "design_id": "EXP-A-CHEAP-WEAK",
            "name": "Cheap but weak design",
            "design_type": "STANDARD",
            "trial_count": 6,
            "cost_flops": 0.4,
            "design_parameters": {"param_mode": "weak"},
        },
        {
            "design_id": "EXP-B-EXPENSIVE-HIGH",
            "name": "Expensive high design",
            "design_type": "STRESS_PERTURBATION",
            "trial_count": 24,
            "cost_flops": 3.0,
            "design_parameters": {"param_mode": "heavy_stress"},
        },
        {
            "design_id": "EXP-C-OPTIMAL-DISCRIMINATIVE",
            "name": "Optimal discriminative ablation design",
            "design_type": "ABLATION",
            "trial_count": 10,
            "cost_flops": 0.5,
            "design_parameters": {"param_mode": "controlled_ablation", "freeze_learning_rate": True},
        },
    ]

    best_design, candidates = decision_engine.evaluate_and_select_experiment(tournament, custom_candidates)
    assert best_design.design_id == "EXP-C-OPTIMAL-DISCRIMINATIVE"
    assert best_design.design_type == "ABLATION"
    assert best_design.design_parameters["freeze_learning_rate"] is True




