"""Unit tests for Autonomous Multi-Iteration Discovery Loops and Evolution Tree."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QApplication
from sqlalchemy import select

from app.critique.service import ScientificCritic
from app.evidence.extractor import AbstractEvidenceExtractor
from app.execution.replication import ReplicationEngine
from app.execution.sandbox import DeterministicSandboxDouble
from app.experiments.catalog import ExperimentCatalog
from app.hypotheses.generator import EvidenceGroundedHypothesisGenerator, OllamaHypothesisGenerator
from app.orchestration.research_orchestrator import ResearchOrchestrator
from app.reasoning.competing_hypotheses import CompetingHypothesisGenerator
from app.reasoning.decision_engine import ResearchDecisionEngine
from app.reasoning.gap_discovery import ResearchGapDiscovery
from app.statistics.service import StatisticsService
from tests.conftest import FixtureLiteratureProvider
from app.storage.database import create_database_engine, create_session_factory
from app.storage.models import (
    Base,
    Hypothesis,
    ProvenanceLink,
    ResearchProject,
    ResearchQuestion,
    ResearchTask,
)
from gui.widgets.charts.evolution_tree import EvolutionTreeWidget
from gui.widgets.hypothesis_tab import HypothesisTab


def _ensure_qt_app() -> QApplication:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    return QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])


def test_hypothesis_refiner() -> None:
    generator = EvidenceGroundedHypothesisGenerator()
    ev_id = uuid4()
    candidate = generator.refine(
        previous_statement="Initial hypothesis statement",
        previous_mechanism="Initial causal mechanism",
        critique_findings=[{"severity": "INFO", "code": "EXPLORATORY_SCOPE", "message": "Result is exploratory"}],
        critique_outcome="ACCEPT_WITH_LIMITATIONS",
        statistics_summary={"mean_difference": 0.142, "p_value": 0.001},
        research_question="How to optimize lipid drug delivery?",
        evidence_ids=[ev_id],
        iteration=2,
    )
    assert "Iteration 2" in candidate.statement or "Iter 2" in candidate.statement
    assert candidate.confidence >= 0.70
    assert candidate.testability_score >= 0.90
    assert len(candidate.assumptions) >= 2

    # Test Ollama refiner fallback
    ollama_gen = OllamaHypothesisGenerator()
    c2 = ollama_gen.refine(
        previous_statement="Initial hypothesis statement",
        previous_mechanism="Initial causal mechanism",
        critique_findings=[],
        critique_outcome="NEEDS_REVISION",
        statistics_summary={"mean_difference": 0.05, "p_value": 0.04},
        research_question="Question",
        evidence_ids=[ev_id],
        iteration=3,
    )
    assert c2.statement != ""


def test_multi_iteration_orchestrator(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path}/test_multi_iter.db")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    orchestrator = ResearchOrchestrator(
        session_factory=session_factory,
        literature_provider=FixtureLiteratureProvider(),
        evidence_extractor=AbstractEvidenceExtractor(),
        hypothesis_generator=EvidenceGroundedHypothesisGenerator(),
        experiment_catalog=ExperimentCatalog(),
        sandbox_runner=DeterministicSandboxDouble(),
        statistics_service=StatisticsService(),
        scientific_critic=ScientificCritic(),
        artifact_root=tmp_path / "artifacts",
        gap_discovery=ResearchGapDiscovery(),
        competing_hypotheses=CompetingHypothesisGenerator(),
        decision_engine=ResearchDecisionEngine(),
        replication_engine=ReplicationEngine(),
    )

    with session_factory() as session:
        proj = ResearchProject(name="Multi Iter Test", status="CREATED")
        session.add(proj)
        session.flush()

        q = ResearchQuestion(project_id=proj.id, text="Can targeted tuning improve model accuracy?")
        session.add(q)

        # Configure task for 2 autonomous iterations
        task = ResearchTask(
            project_id=proj.id,
            trace_id=uuid4(),
            status="QUEUED",
            stage="CREATED",
            provenance={"max_iterations": 2},
        )
        session.add(task)
        session.commit()
        task_id = task.id
        project_id = proj.id

    orchestrator.run_task(task_id)

    with session_factory() as session:
        refreshed_task = session.get(ResearchTask, task_id)
        refreshed_project = session.get(ResearchProject, project_id)
        assert refreshed_task.status == "COMPLETED"
        assert refreshed_project.status == "COMPLETED"
        assert refreshed_project.provenance.get("completed_iterations") == 2

        # Check hypotheses (should have initial + refined)
        hypotheses = session.scalars(
            select(Hypothesis).where(Hypothesis.project_id == project_id).order_by(Hypothesis.created_at.asc())
        ).all()
        assert len(hypotheses) == 2

        # Check refinement provenance link
        refined_link = session.scalar(
            select(ProvenanceLink).where(
                ProvenanceLink.child_id == hypotheses[1].id,
                ProvenanceLink.relationship == "REFINED_FROM",
            )
        )
        assert refined_link is not None
        assert refined_link.parent_id == hypotheses[0].id


def test_evolution_tree_widget() -> None:
    _ensure_qt_app()
    tree = EvolutionTreeWidget()
    assert tree.count_lbl.text() == "No Evolution Data"

    sample_evolution = [
        {
            "iteration": 1,
            "statement": "Initial statement for lipid carrier",
            "mechanism": "Causal mechanism 1",
            "confidence": 0.65,
            "testability_score": 0.90,
            "statistics": {"mean_difference": 0.12},
            "critique_outcome": "ACCEPT_WITH_LIMITATIONS",
        },
        {
            "iteration": 2,
            "statement": "Refined statement incorporating bounds",
            "mechanism": "Refined causal mechanism 2",
            "confidence": 0.85,
            "testability_score": 0.94,
            "statistics": {"mean_difference": 0.16},
            "critique_outcome": "ACCEPT",
        },
    ]

    selected_item = []
    tree.iteration_selected.connect(lambda item: selected_item.append(item))

    tree.set_evolution_data(sample_evolution)
    assert tree.count_lbl.text() == "2 Iterations"

    # Select iteration 0
    tree._select_iteration(0)
    assert len(selected_item) == 1
    assert selected_item[0]["iteration"] == 1
    tree.close()


def test_hypothesis_tab_with_evolution() -> None:
    _ensure_qt_app()
    tab = HypothesisTab()
    assert tab.evolution_tree is not None

    sample_evolution = [
        {
            "iteration": 1,
            "statement": "Initial statement",
            "mechanism": "Initial mechanism",
            "confidence": 0.65,
            "testability_score": 0.90,
            "novelty_estimate": "MODERATE_NOVELTY",
            "assumptions": ["Assumption 1"],
            "predictions": ["Prediction 1"],
            "critique_outcome": "ACCEPT_WITH_LIMITATIONS",
        },
        {
            "iteration": 2,
            "statement": "Refined statement",
            "mechanism": "Refined mechanism",
            "confidence": 0.85,
            "testability_score": 0.95,
            "novelty_estimate": "HIGH_NOVELTY",
            "assumptions": ["Assumption 1", "Assumption 2"],
            "predictions": ["Prediction 1", "Prediction 2"],
            "critique_outcome": "ACCEPT",
        },
    ]

    tab.set_hypotheses([], evolution_data=sample_evolution)
    assert tab.lbl_iter_pill.text() == "ITERATION 2"
    assert "Refined statement" in tab.lbl_statement.text()

    # Switch to Iteration 1
    tab._on_iteration_selected(sample_evolution[0])
    assert tab.lbl_iter_pill.text() == "ITERATION 1"
    assert "Initial statement" in tab.lbl_statement.text()

    tab.set_hypotheses([])
    assert tab.lbl_iter_pill.text() == "ITERATION —"
    tab.close()
