"""Explicit, bounded workflow coordinator with active Bayesian decision-theoretic loop."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import FailureCode, ResearchWorkflowError
from app.critique.service import ScientificCritic
from app.evidence.extractor import AbstractEvidenceExtractor, ExtractedEvidence
from app.execution.replication import ReplicationEngine
from app.execution.sandbox import SandboxRunner
from app.experiments.catalog import ExperimentCatalog
from app.hypotheses.generator import EvidenceGroundedHypothesisGenerator
from app.literature.providers import LiteratureProvider, RetrievedPaper
from app.reasoning.competing_hypotheses import CompetingHypothesisGenerator, HypothesisTournament
from app.reasoning.decision_engine import ResearchDecisionEngine
from app.reasoning.gap_discovery import ResearchGapDiscovery
from app.statistics.service import StatisticsService
from app.storage.models import (
    Artifact,
    Critique,
    Evidence,
    Experiment,
    ExperimentRun,
    Hypothesis,
    Metric,
    Paper,
    ProvenanceLink,
    ResearchProject,
    ResearchQuestion,
    ResearchTask,
    Result,
    Source,
)

from .state import ResearchStage, ensure_transition


class ResearchOrchestrator:
    """Explicit, bounded workflow coordinator executing an active Bayesian decision-theoretic loop."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        literature_provider: LiteratureProvider,
        evidence_extractor: AbstractEvidenceExtractor,
        hypothesis_generator: EvidenceGroundedHypothesisGenerator,
        experiment_catalog: ExperimentCatalog,
        sandbox_runner: SandboxRunner,
        statistics_service: StatisticsService,
        scientific_critic: ScientificCritic,
        artifact_root: Path,
        gap_discovery: ResearchGapDiscovery | None = None,
        competing_hypotheses: CompetingHypothesisGenerator | None = None,
        decision_engine: ResearchDecisionEngine | None = None,
        replication_engine: ReplicationEngine | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._literature_provider = literature_provider
        self._evidence_extractor = evidence_extractor
        self._hypothesis_generator = hypothesis_generator
        self._experiment_catalog = experiment_catalog
        self._sandbox_runner = sandbox_runner
        self._statistics_service = statistics_service
        self._scientific_critic = scientific_critic
        self._artifact_root = artifact_root

        # True Decision-Theoretic Reasoning Core
        self._gap_discovery = gap_discovery or ResearchGapDiscovery()
        self._competing_hypotheses = competing_hypotheses or CompetingHypothesisGenerator()
        self._decision_engine = decision_engine or ResearchDecisionEngine()
        self._replication_engine = replication_engine or ReplicationEngine()

    def run_task(self, task_id: UUID) -> None:
        with self._session_factory() as session:
            task = session.get(ResearchTask, task_id)
            if task is None:
                raise LookupError(f"Research task {task_id} does not exist.")
            if task.status not in {"QUEUED", "RUNNING"}:
                raise ResearchWorkflowError(
                    FailureCode.INVALID_STATE,
                    f"Task {task_id} is already terminal with status {task.status}.",
                )
            project = session.get(ResearchProject, task.project_id)
            question = session.scalar(
                select(ResearchQuestion).where(ResearchQuestion.project_id == task.project_id)
            )
            if project is None or question is None:
                self._fail(session, task, project, FailureCode.INVALID_STATE, "Project or question is missing.")
                return
            task.status = "RUNNING"
            project.status = "RUNNING"
            session.commit()

            try:
                source, papers = self._retrieve_and_store(session, task, project, question)
                evidence = self._extract_and_store(session, task, project, papers)

                # 1. Literature-Driven Gap Discovery & 5-Hypothesis Tournament Formulation
                max_iterations = max(1, min(5, int((task.provenance or {}).get("max_iterations", 2))))
                hypothesis, tournament = self._generate_tournament_hypothesis(session, task, project, question, evidence)

                # 2. Exact Expected Information Gain (EIG / Cost) Optimal Experiment Selection
                experiment, best_design = self._plan_eig_experiment(
                    session, task, project, hypothesis, tournament, iteration=1
                )

                # 3. Sandbox Execution, Statistics, Multi-Seed Replication, Bayesian Update & Critic
                run, result, critique, replication_report = self._execute_replicate_and_critique(
                    session, task, project, experiment, hypothesis, tournament, best_design
                )

                completed_iterations = 1
                current_posteriors = (result.provenance or {}).get("posterior_probabilities")

                for it in range(2, max_iterations + 1):
                    if critique.outcome == "ACCEPT" and replication_report.is_reproducible:
                        break

                    hypothesis, tournament = self._refine_tournament_hypothesis(
                        session,
                        task,
                        project,
                        question,
                        hypothesis,
                        critique,
                        result,
                        evidence,
                        tournament,
                        prior_probabilities=current_posteriors,
                        iteration=it,
                    )
                    experiment, best_design = self._plan_eig_experiment(
                        session, task, project, hypothesis, tournament, iteration=it
                    )
                    run, result, critique, replication_report = self._execute_replicate_and_critique(
                        session, task, project, experiment, hypothesis, tournament, best_design
                    )
                    current_posteriors = (result.provenance or {}).get("posterior_probabilities")
                    completed_iterations = it

                task.status = "COMPLETED"
                project.status = "COMPLETED"
                project.provenance = {
                    **project.provenance,
                    "final_result_id": str(result.id),
                    "final_critique_id": str(critique.id),
                    "source_id": str(source.id),
                    "last_run_id": str(run.id),
                    "completed_iterations": completed_iterations,
                    "tournament_id": tournament.tournament_id,
                    "leading_hypothesis_id": (result.provenance or {}).get("leading_hypothesis_id"),
                    "reproducibility_score": replication_report.reproducibility_score,
                }
                self._transition(task, ResearchStage.COMPLETED)
                session.commit()
            except ResearchWorkflowError as error:
                self._fail(session, task, project, error.code, error.message)
            except Exception as error:  # pragma: no cover - defensive final failure boundary
                self._fail(session, task, project, FailureCode.INVALID_STATE, f"Unexpected workflow error: {error}")

    def run_experiment_task(self, task_id: UUID, experiment_id: UUID) -> None:
        """Run an existing registered experiment without re-running literature retrieval."""
        with self._session_factory() as session:
            task = session.get(ResearchTask, task_id)
            experiment = session.get(Experiment, experiment_id)
            if task is None or experiment is None:
                raise LookupError("Experiment task or experiment does not exist.")
            if task.status not in {"QUEUED", "RUNNING"}:
                raise ResearchWorkflowError(
                    FailureCode.INVALID_STATE,
                    f"Task {task.id} is in non-executable state {task.status}.",
                )
            project = session.get(ResearchProject, experiment.project_id)
            hypothesis = session.get(Hypothesis, experiment.hypothesis_id)
            question = session.scalar(
                select(ResearchQuestion).where(ResearchQuestion.project_id == project.id)
            )
            evidence_records = session.scalars(
                select(Evidence).where(Evidence.project_id == project.id)
            ).all()

            if project is None or hypothesis is None or question is None:
                self._fail(session, task, project, FailureCode.INVALID_STATE, "Experiment dependencies are missing.")
                return
            task.status = "RUNNING"
            project.status = "RUNNING"
            session.commit()
            try:
                extracted_ev = [
                    ExtractedEvidence(text=e.text, locator=e.locator or "", evidence_kind=e.evidence_kind)
                    for e in evidence_records
                ]
                gap = self._gap_discovery.discover_gaps(question.text, extracted_ev)[0]
                tournament = self._competing_hypotheses.generate_tournament(question.text, gap, extracted_ev)
                best_design, _ = self._decision_engine.evaluate_and_select_experiment(tournament)

                run, result, critique, rep_report = self._execute_replicate_and_critique(
                    session, task, project, experiment, hypothesis, tournament, best_design
                )
                task.status = "COMPLETED"
                project.status = "COMPLETED"
                project.provenance = {
                    **project.provenance,
                    "final_result_id": str(result.id),
                    "final_critique_id": str(critique.id),
                    "last_run_id": str(run.id),
                    "reproducibility_score": rep_report.reproducibility_score,
                }
                self._transition(task, ResearchStage.COMPLETED)
                session.commit()
            except ResearchWorkflowError as error:
                self._fail(session, task, project, error.code, error.message)
            except Exception as error:  # pragma: no cover - defensive final failure boundary
                self._fail(session, task, project, FailureCode.INVALID_STATE, f"Unexpected workflow error: {error}")

    def _retrieve_and_store(
        self,
        session: Session,
        task: ResearchTask,
        project: ResearchProject,
        question: ResearchQuestion,
    ) -> tuple[Source, list[Paper]]:
        self._transition(task, ResearchStage.RETRIEVING)
        result = self._literature_provider.search(question.text)
        if not result.papers:
            raise ResearchWorkflowError(
                FailureCode.RETRIEVAL_FAILED,
                "Literature provider returned no papers; no evidence-grounded workflow can continue.",
            )
        source = Source(
            project_id=project.id,
            name=result.provider_name,
            source_type="RETRIEVED_METADATA",
            uri=result.request_url,
            raw_payload={"query": result.query, **result.raw_payload},
            provenance={"task_id": str(task.id), "trace_id": str(task.trace_id)},
        )
        session.add(source)
        session.flush()
        papers: list[Paper] = []
        for retrieved in result.papers:
            paper = Paper(
                project_id=project.id,
                source_id=source.id,
                external_id=retrieved.external_id,
                title=retrieved.title,
                abstract=retrieved.abstract,
                authors=retrieved.authors,
                published_at=retrieved.published_at,
                url=retrieved.url,
                provenance={
                    "source_id": str(source.id),
                    "provider": retrieved.source_provider,
                    "doi": retrieved.doi,
                    "retrieval_kind": "multi_source_metadata",
                },
            )
            session.add(paper)
            papers.append(paper)
        session.flush()
        session.commit()
        return source, papers

    def _extract_and_store(
        self, session: Session, task: ResearchTask, project: ResearchProject, papers: list[Paper]
    ) -> list[Evidence]:
        self._transition(task, ResearchStage.EXTRACTING)
        evidence: list[Evidence] = []
        for paper in papers:
            retrieved_paper = RetrievedPaper(
                external_id=paper.external_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors or [],
                published_at=paper.published_at,
                url=paper.url,
                source_provider=(paper.provenance or {}).get("provider", "arXiv"),
            )
            for extracted in self._evidence_extractor.extract(retrieved_paper):
                record = Evidence(
                    project_id=project.id,
                    paper_id=paper.id,
                    evidence_kind=extracted.evidence_kind,
                    text=extracted.text,
                    locator=extracted.locator,
                    confidence=extracted.confidence,
                    provenance={
                        "paper_id": str(paper.id),
                        "source_locator": extracted.locator,
                        "extraction_method": "deterministic_abstract_sentence_split_v1",
                        "task_id": str(task.id),
                    },
                )
                session.add(record)
                evidence.append(record)
        session.flush()
        if not evidence:
            raise ResearchWorkflowError(
                FailureCode.EVIDENCE_EXTRACTION_FAILED,
                "No usable abstract sentences were extracted from retrieved papers.",
            )
        for record in evidence:
            session.add(
                ProvenanceLink(
                    child_type="Evidence",
                    child_id=record.id,
                    parent_type="Paper",
                    parent_id=record.paper_id,
                    relationship="EXTRACTED_FROM",
                    locator=record.locator,
                )
            )
        session.commit()
        return evidence

    def _generate_tournament_hypothesis(
        self,
        session: Session,
        task: ResearchTask,
        project: ResearchProject,
        question: ResearchQuestion,
        evidence: list[Evidence],
    ) -> tuple[Hypothesis, HypothesisTournament]:
        """Synthesizes literature gaps and an active 5-hypothesis tournament."""
        self._transition(task, ResearchStage.HYPOTHESIZING)

        extracted_ev_list = [
            ExtractedEvidence(text=e.text, locator=e.locator or "", evidence_kind=e.evidence_kind)
            for e in evidence
        ]
        gaps = self._gap_discovery.discover_gaps(question.text, extracted_ev_list)
        selected_gap = gaps[0]

        tournament = self._competing_hypotheses.generate_tournament(
            question.text,
            selected_gap,
            extracted_ev_list,
        )
        primary_h = tournament.hypotheses[0]

        hypothesis = Hypothesis(
            project_id=project.id,
            statement=primary_h.statement,
            mechanism=primary_h.mechanism,
            assumptions=[selected_gap.untested_assumption],
            predictions=[f"Predicted Cohen's d: {primary_h.predicted_effect_mean:.2f} ± {primary_h.predicted_effect_std:.2f}"],
            supporting_evidence_ids=[str(e.id) for e in evidence[:4]],
            contradicting_evidence_ids=[],
            confidence=primary_h.prior_probability,
            novelty_estimate="high",
            testability_score=0.95,
            estimated_cost=1.0,
            provenance={
                "task_id": str(task.id),
                "generation_method": "competing_hypotheses_tournament_v2",
                "tournament_id": tournament.tournament_id,
                "gap_id": selected_gap.gap_id,
                "gap_statement": selected_gap.gap_statement,
                "competing_hypotheses_count": len(tournament.hypotheses),
                "prior_probability": primary_h.prior_probability,
            },
        )
        session.add(hypothesis)
        session.flush()
        for evidence_record in evidence:
            session.add(
                ProvenanceLink(
                    child_type="Hypothesis",
                    child_id=hypothesis.id,
                    parent_type="Evidence",
                    parent_id=evidence_record.id,
                    relationship="MOTIVATED_BY",
                    locator=None,
                )
            )
        session.commit()
        return hypothesis, tournament

    def _refine_tournament_hypothesis(
        self,
        session: Session,
        task: ResearchTask,
        project: ResearchProject,
        question: ResearchQuestion,
        prev_hyp: Hypothesis,
        critique: Critique,
        result: Result,
        evidence: list[Evidence],
        prev_tournament: HypothesisTournament,
        prior_probabilities: dict[str, float] | None = None,
        iteration: int = 2,
    ) -> tuple[Hypothesis, HypothesisTournament]:
        self._transition(task, ResearchStage.HYPOTHESIZING)

        extracted_ev_list = [
            ExtractedEvidence(text=e.text, locator=e.locator or "", evidence_kind=e.evidence_kind)
            for e in evidence
        ]
        gaps = self._gap_discovery.discover_gaps(question.text, extracted_ev_list)
        selected_gap = gaps[0]
        tournament = self._competing_hypotheses.generate_tournament(
            f"{question.text} (Refinement Round {iteration})",
            selected_gap,
            extracted_ev_list,
            prior_probabilities=prior_probabilities,
        )
        primary_h = tournament.hypotheses[0]

        refined_hyp = Hypothesis(
            project_id=project.id,
            statement=f"Refinement (Round {iteration}): {primary_h.statement}",
            mechanism=primary_h.mechanism,
            assumptions=[selected_gap.untested_assumption],
            predictions=[f"Refined predicted d: {primary_h.predicted_effect_mean:.2f} ± {primary_h.predicted_effect_std:.2f}"],
            supporting_evidence_ids=[str(e.id) for e in evidence[:4]],
            contradicting_evidence_ids=[],
            confidence=primary_h.prior_probability,
            novelty_estimate="high",
            testability_score=0.96,
            estimated_cost=1.2,
            provenance={
                "task_id": str(task.id),
                "generation_method": "decision_theoretic_tournament_refinement_v2",
                "iteration": iteration,
                "parent_hypothesis_id": str(prev_hyp.id),
                "resolved_critique_id": str(critique.id),
                "tournament_id": tournament.tournament_id,
            },
        )
        session.add(refined_hyp)
        session.flush()
        session.add(
            ProvenanceLink(
                child_type="Hypothesis",
                child_id=refined_hyp.id,
                parent_type="Hypothesis",
                parent_id=prev_hyp.id,
                relationship="REFINED_FROM",
                locator=f"iteration_{iteration}",
            )
        )
        session.commit()
        return refined_hyp, tournament

    def _plan_eig_experiment(
        self,
        session: Session,
        task: ResearchTask,
        project: ResearchProject,
        hypothesis: Hypothesis,
        tournament: HypothesisTournament,
        iteration: int = 1,
    ) -> tuple[Experiment, Any]:
        """Calculates exact Expected Information Gain (EIG) to select the optimal experiment."""
        self._transition(task, ResearchStage.PLANNING_EXPERIMENT)

        best_design, _ = self._decision_engine.evaluate_and_select_experiment(tournament)

        planned = self._experiment_catalog.build_for_hypothesis(
            hypothesis_statement=hypothesis.statement,
            mechanism=hypothesis.mechanism,
            iteration=iteration,
        )
        spec = dict(planned.specification)
        spec["sample_size"] = best_design.trial_count
        spec["design_id"] = best_design.design_id
        spec["design_name"] = best_design.name
        spec["design_type"] = best_design.design_type
        spec["design_parameters"] = best_design.design_parameters
        if iteration > 1:
            spec["sample_size"] = min(24, int(spec.get("sample_size", 12)) + 4 * (iteration - 1))

        experiment = Experiment(
            project_id=project.id,
            hypothesis_id=hypothesis.id,
            template_id=planned.template_id,
            template_revision=planned.template_revision,
            kind=planned.specification["classification"],
            specification=spec,
            provenance={
                "task_id": str(task.id),
                "planning_method": "exact_shannon_eig_optimal_design_v2",
                "iteration": iteration,
                "selected_design_id": best_design.design_id,
                "expected_information_gain_bits": best_design.expected_information_gain,
                "cost_efficiency_utility": best_design.cost_efficiency_utility,
                "tournament_id": tournament.tournament_id,
            },
        )
        session.add(experiment)
        session.flush()
        session.add(
            ProvenanceLink(
                child_type="Experiment",
                child_id=experiment.id,
                parent_type="Hypothesis",
                parent_id=hypothesis.id,
                relationship="TESTS",
                locator=f"iteration_{iteration}",
            )
        )
        session.commit()
        return experiment, best_design

    def _execute_replicate_and_critique(
        self,
        session: Session,
        task: ResearchTask,
        project: ResearchProject,
        experiment: Experiment,
        hypothesis: Hypothesis,
        tournament: HypothesisTournament,
        best_design: Any,
    ) -> tuple[ExperimentRun, Result, Critique, Any]:
        """Executes sandbox run, multi-seed replication, Gaussian Bayesian update, and Deep Critic."""
        self._transition(task, ResearchStage.EXECUTING)
        configuration = _sandbox_configuration(experiment.specification)
        run = ExperimentRun(
            project_id=project.id,
            experiment_id=experiment.id,
            status="RUNNING",
            random_seed=configuration["random_seed"],
            configuration=configuration,
            environment={"template_revision": experiment.template_revision},
            started_at=datetime.now(timezone.utc),
            provenance={"task_id": str(task.id), "experiment_id": str(experiment.id)},
        )
        session.add(run)
        session.flush()
        run_directory = self._artifact_root / str(project.id) / str(run.id)
        try:
            # 1. Primary Isolated Sandbox Execution
            sandbox_result = self._sandbox_runner.run(experiment.template_id, configuration, run_directory)
            output = sandbox_result.output
            baseline_scores = _scores(output, "baseline_scores")
            treatment_scores = _scores(output, "treatment_scores")

            run.status = "SUCCEEDED"
            run.finished_at = datetime.now(timezone.utc)
            run.stdout = sandbox_result.stdout[-20_000:]
            run.stderr = sandbox_result.stderr[-20_000:]
            run.environment = {**run.environment, **sandbox_result.environment, "dataset": output.get("dataset", {})}
            session.add(
                Artifact(
                    run_id=run.id,
                    artifact_type="SANDBOX_RESULT_JSON",
                    path=str(sandbox_result.artifact_path),
                    sha256=sandbox_result.artifact_sha256,
                    provenance={"created_by": "DockerSandboxRunner"},
                )
            )
            if sandbox_result.code_path:
                session.add(
                    Artifact(
                        run_id=run.id,
                        artifact_type="GENERATED_PYTHON_SCRIPT",
                        path=str(sandbox_result.code_path),
                        sha256=sandbox_result.code_sha256 or "",
                        provenance={"created_by": "DynamicCodeGenerator", "ast_security": "verified"},
                    )
                )
            session.add_all(
                [
                    Metric(
                        run_id=run.id,
                        name="baseline_mean_accuracy",
                        value=sum(baseline_scores) / len(baseline_scores),
                        sample_count=len(baseline_scores),
                    ),
                    Metric(
                        run_id=run.id,
                        name="treatment_mean_accuracy",
                        value=sum(treatment_scores) / len(treatment_scores),
                        sample_count=len(treatment_scores),
                    ),
                ]
            )
            session.flush()

            # 2. Multi-Seed Replication Suite (S = 3 seeds)
            base_seed = int(configuration.get("random_seed", 1729))
            seed_count = max(2, min(10, int((task.provenance or {}).get("replication_seed_count", 3))))
            rep_seeds = [base_seed + 101 * i for i in range(seed_count)]
            rep_b_runs = [baseline_scores]
            rep_t_runs = [treatment_scores]
            replication_failed = False

            for s in rep_seeds[1:]:
                rep_config = dict(configuration)
                rep_config["random_seed"] = s
                rep_dir = self._artifact_root / str(project.id) / f"rep_{run.id}_{s}"
                try:
                    s_res = self._sandbox_runner.run(experiment.template_id, rep_config, rep_dir)
                    rep_b_runs.append(_scores(s_res.output, "baseline_scores"))
                    rep_t_runs.append(_scores(s_res.output, "treatment_scores"))
                except Exception:
                    # Strict Zero-Fabrication: Mark replication as failed, never invent synthetic measurements
                    replication_failed = True
                    break

            if replication_failed or len(rep_b_runs) < 2:
                from app.execution.replication import ReplicationReport
                replication_report = ReplicationReport(
                    is_reproducible=False,
                    reproducibility_score=0.0,
                    directional_consistency_ratio=0.0,
                    mean_delta_stability_cv=1.0,
                    evaluated_seeds=rep_seeds[:len(rep_b_runs)],
                    seed_deltas=[],
                    audit_notes=["Replication incomplete or failed during sandbox execution."],
                )
            else:
                replication_report = self._replication_engine.evaluate_replication(
                    rep_b_runs, rep_t_runs, seeds=rep_seeds[:len(rep_b_runs)]
                )

            # 3. Paired Statistical Analysis
            self._transition(task, ResearchStage.ANALYZING)
            statistics_summary = self._statistics_service.analyze_paired(baseline_scores, treatment_scores)

            # 4. Continuous Gaussian Bayesian Updating & Bayes Factors
            belief_state = self._decision_engine.update_beliefs(tournament, statistics_summary)

            result = Result(
                run_id=run.id,
                summary=(
                    f"Measured effect size d={statistics_summary.effect_size:.3f} "
                    f"with leading hypothesis '{belief_state.leading_hypothesis_id}' "
                    f"(confidence={belief_state.confidence * 100:.1f}%, info_gain={belief_state.information_gain_bits:.3f} bits, "
                    f"reproducibility={replication_report.reproducibility_score * 100:.1f}%)."
                ),
                statistics=statistics_summary.as_dict(),
                provenance={
                    "analysis_method": "paired_permutation_and_bootstrap_v1",
                    "run_id": str(run.id),
                    "leading_hypothesis_id": belief_state.leading_hypothesis_id,
                    "posterior_probabilities": belief_state.posterior_probabilities,
                    "bayes_factors": belief_state.bayes_factors,
                    "information_gain_bits": belief_state.information_gain_bits,
                    "reproducibility_score": replication_report.reproducibility_score,
                    "is_reproducible": replication_report.is_reproducible,
                },
            )
            session.add(result)
            session.flush()
            session.add(
                ProvenanceLink(
                    child_type="Result",
                    child_id=result.id,
                    parent_type="ExperimentRun",
                    parent_id=run.id,
                    relationship="MEASURED_BY",
                    locator=None,
                )
            )

            # 5. Deep Epistemic Scientific Referee Audit
            self._transition(task, ResearchStage.CRITIQUING)
            report = self._scientific_critic.evaluate(
                statistics_summary,
                experiment.kind,
                baseline_scores=baseline_scores,
                treatment_scores=treatment_scores,
                replication_report=replication_report,
            )
            critique = Critique(
                project_id=project.id,
                hypothesis_id=hypothesis.id,
                run_id=run.id,
                outcome=report.outcome,
                findings=report.as_persisted_findings(),
                provenance={
                    "critic": "deep_epistemic_causal_referee_v2",
                    "result_id": str(result.id),
                    "statistical_power": report.statistical_power,
                    "effect_magnitude_tier": report.effect_magnitude_tier,
                    "confounder_risk": report.confounder_risk,
                    "reproducibility_score": replication_report.reproducibility_score,
                },
            )
            session.add(critique)
            session.flush()
            session.add(
                ProvenanceLink(
                    child_type="Critique",
                    child_id=critique.id,
                    parent_type="Result",
                    parent_id=result.id,
                    relationship="EVALUATES",
                    locator=None,
                )
            )
            session.commit()
            return run, result, critique, replication_report
        except Exception as err:
            run.status = "FAILED"
            run.finished_at = datetime.now(timezone.utc)
            run.stderr = str(err)
            session.flush()
            session.commit()
            raise

    @staticmethod
    def _transition(task: ResearchTask, next_stage: ResearchStage) -> None:
        ensure_transition(task.stage, next_stage)
        task.stage = next_stage.value

    @staticmethod
    def _fail(
        session: Session,
        task: ResearchTask,
        project: ResearchProject | None,
        code: FailureCode,
        message: str,
    ) -> None:
        if task.stage not in {ResearchStage.COMPLETED.value, ResearchStage.FAILED.value}:
            task.stage = ResearchStage.FAILED.value
        task.status = "FAILED"
        task.error_code = code.value
        task.error_message = message
        if project is not None:
            project.status = "FAILED"
        session.commit()


def _sandbox_configuration(specification: dict[str, Any]) -> dict[str, Any]:
    return {
        "template_id": str(specification.get("template_id", "dynamic_generated_simulation_v1")),
        "template_revision": str(specification.get("template_revision", "2026-08-21")),
        "baseline_iterations": int(specification.get("baseline", {}).get("iterations", 20)),
        "treatment_iterations": int(specification.get("treatment", {}).get("iterations", 400)),
        "trial_count": int(specification.get("sample_size", 12)),
        "sample_size": int(specification.get("sample_size", 12)),
        "random_seed": int(specification.get("random_seed", 1729)),
        "generated_code": specification.get("generated_code"),
        "design_id": specification.get("design_id", "EXP-DES-01-STANDARD"),
        "design_name": specification.get("design_name", "Standard Paired Empirical Trial"),
        "design_type": specification.get("design_type", "STANDARD"),
        "design_parameters": specification.get("design_parameters", {}),
    }


def _scores(output: dict[str, Any], key: str) -> list[float]:
    raw_scores = output.get(key)
    if not isinstance(raw_scores, list) or not raw_scores:
        raise ResearchWorkflowError(FailureCode.SANDBOX_FAILED, f"Sandbox output lacks '{key}'.")
    try:
        return [float(value) for value in raw_scores]
    except (TypeError, ValueError) as error:
        raise ResearchWorkflowError(
            FailureCode.SANDBOX_FAILED,
            f"Sandbox output contains invalid '{key}' values.",
        ) from error
