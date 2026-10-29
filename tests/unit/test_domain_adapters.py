"""Unit tests for Domain Experiment Adapters (ML and Biomedical)."""

from __future__ import annotations

from app.domains.bio_adapter import BiomedicalExperimentAdapter
from app.domains.ml_adapter import MLExperimentAdapter
from app.execution.ast_security import ASTSecurityValidator
from app.reasoning.competing_hypotheses import CompetingHypothesisGenerator
from app.reasoning.gap_discovery import ResearchGapDiscovery


def test_ml_experiment_adapter() -> None:
    adapter = MLExperimentAdapter()
    assert adapter.domain_name == "MACHINE_LEARNING"

    script = adapter.generate_experiment_script(
        hypothesis_statement="Curvature adaptive momentum reduces oscillation in non-convex ravines.",
        mechanism="Second-order curvature scaling",
        trial_count=10,
        random_seed=42,
    )
    is_valid, _ = ASTSecurityValidator.validate(script)
    assert is_valid is True

    gap = ResearchGapDiscovery().discover_gaps("ML optimization test", [])[0]
    tournament = CompetingHypothesisGenerator().generate_tournament("ML optimization test", gap, [])
    designs = adapter.suggest_candidate_designs(tournament)
    assert len(designs) >= 2
    assert all("design_id" in d and "cost_flops" in d for d in designs)


def test_bio_experiment_adapter() -> None:
    adapter = BiomedicalExperimentAdapter()
    assert adapter.domain_name == "BIOMEDICAL"

    script = adapter.generate_experiment_script(
        hypothesis_statement="Nanocarrier PEGylation increases circulation half-life and cellular uptake.",
        mechanism="Steric hindrance of opsonization",
        trial_count=8,
        random_seed=123,
    )
    is_valid, _ = ASTSecurityValidator.validate(script)
    assert is_valid is True

    gap = ResearchGapDiscovery().discover_gaps("Bio uptake test", [])[0]
    tournament = CompetingHypothesisGenerator().generate_tournament("Bio uptake test", gap, [])
    designs = adapter.suggest_candidate_designs(tournament)
    assert len(designs) >= 1
