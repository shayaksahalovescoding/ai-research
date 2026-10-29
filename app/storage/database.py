from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(database_url: str) -> Engine:
    """Create a non-global SQLAlchemy engine suitable for API or test injection."""

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_project_cascade(session: Session, project_id: object) -> bool:
    """Cascading deletion of a research project and all associated records."""
    from uuid import UUID
    from sqlalchemy import delete, select
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

    uid = UUID(str(project_id))
    project = session.get(ResearchProject, uid)
    if project is None:
        return False

    run_ids = session.scalars(select(ExperimentRun.id).where(ExperimentRun.project_id == uid)).all()
    paper_ids = session.scalars(select(Paper.id).where(Paper.project_id == uid)).all()
    evidence_ids = session.scalars(select(Evidence.id).where(Evidence.project_id == uid)).all()
    hypothesis_ids = session.scalars(select(Hypothesis.id).where(Hypothesis.project_id == uid)).all()
    experiment_ids = session.scalars(select(Experiment.id).where(Experiment.project_id == uid)).all()
    source_ids = session.scalars(select(Source.id).where(Source.project_id == uid)).all()
    task_ids = session.scalars(select(ResearchTask.id).where(ResearchTask.project_id == uid)).all()
    question_ids = session.scalars(select(ResearchQuestion.id).where(ResearchQuestion.project_id == uid)).all()

    all_entity_ids = [
        uid,
        *run_ids,
        *paper_ids,
        *evidence_ids,
        *hypothesis_ids,
        *experiment_ids,
        *source_ids,
        *task_ids,
        *question_ids,
    ]

    if all_entity_ids:
        session.execute(
            delete(ProvenanceLink).where(
                (ProvenanceLink.child_id.in_(all_entity_ids)) | (ProvenanceLink.parent_id.in_(all_entity_ids))
            )
        )

    if run_ids:
        session.execute(delete(Metric).where(Metric.run_id.in_(run_ids)))
        session.execute(delete(Result).where(Result.run_id.in_(run_ids)))
        session.execute(delete(Artifact).where(Artifact.run_id.in_(run_ids)))

    session.execute(delete(Critique).where(Critique.project_id == uid))
    session.execute(delete(ExperimentRun).where(ExperimentRun.project_id == uid))
    session.execute(delete(Experiment).where(Experiment.project_id == uid))
    session.execute(delete(Hypothesis).where(Hypothesis.project_id == uid))
    session.execute(delete(Evidence).where(Evidence.project_id == uid))
    session.execute(delete(Paper).where(Paper.project_id == uid))
    session.execute(delete(Source).where(Source.project_id == uid))
    session.execute(delete(ResearchTask).where(ResearchTask.project_id == uid))
    session.execute(delete(ResearchQuestion).where(ResearchQuestion.project_id == uid))

    session.delete(project)
    session.flush()
    return True

