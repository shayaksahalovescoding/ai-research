from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.critique.service import ScientificCritic
from app.evidence.extractor import AbstractEvidenceExtractor
from app.execution.replication import ReplicationEngine
from app.execution.sandbox import DockerSandboxRunner, SandboxRunner
from app.experiments.catalog import ExperimentCatalog
from app.hypotheses.generator import OllamaHypothesisGenerator
from app.literature.providers import LiteratureProvider, MultiSourceResearchProvider
from app.orchestration.research_orchestrator import ResearchOrchestrator
from app.reasoning.competing_hypotheses import CompetingHypothesisGenerator
from app.reasoning.decision_engine import ResearchDecisionEngine
from app.reasoning.gap_discovery import ResearchGapDiscovery
from app.statistics.service import StatisticsService
from app.storage.database import create_database_engine, create_session_factory


@dataclass(slots=True)
class AppServices:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    orchestrator: ResearchOrchestrator


def build_services(
    settings: Settings,
    *,
    literature_provider: LiteratureProvider | None = None,
    sandbox_runner: SandboxRunner | None = None,
) -> AppServices:
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    catalog = ExperimentCatalog()
    orchestrator = ResearchOrchestrator(
        session_factory=session_factory,
        literature_provider=literature_provider or MultiSourceResearchProvider(settings),
        evidence_extractor=AbstractEvidenceExtractor(),
        hypothesis_generator=OllamaHypothesisGenerator(settings),
        experiment_catalog=catalog,
        sandbox_runner=sandbox_runner or DockerSandboxRunner(settings, catalog),
        statistics_service=StatisticsService(),
        scientific_critic=ScientificCritic(),
        artifact_root=settings.artifact_root,
        gap_discovery=ResearchGapDiscovery(),
        competing_hypotheses=CompetingHypothesisGenerator(),
        decision_engine=ResearchDecisionEngine(),
        replication_engine=ReplicationEngine(),
    )
    return AppServices(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        orchestrator=orchestrator,
    )


def get_services(request: Request) -> AppServices:
    return request.app.state.services


def get_session(request: Request) -> Generator[Session, None, None]:
    services = get_services(request)
    with services.session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

