from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AuditedEntity:
    """Common immutable identity and provenance envelope for persisted records."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ResearchProject(AuditedEntity, Base):
    __tablename__ = "research_projects"

    name: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="CREATED")
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResearchQuestion(AuditedEntity, Base):
    __tablename__ = "research_questions"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    text: Mapped[str] = mapped_column(Text)


class ResearchTask(AuditedEntity, Base):
    __tablename__ = "research_tasks"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    trace_id: Mapped[UUID] = mapped_column(default=uuid4, index=True)
    status: Mapped[str] = mapped_column(String(40), default="QUEUED")
    stage: Mapped[str] = mapped_column(String(40), default="CREATED")
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Source(AuditedEntity, Base):
    __tablename__ = "sources"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40))
    uri: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Paper(AuditedEntity, Base):
    __tablename__ = "papers"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_paper_source_external"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str] = mapped_column(Text)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    url: Mapped[str] = mapped_column(Text)


class Evidence(AuditedEntity, Base):
    __tablename__ = "evidence"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    paper_id: Mapped[UUID | None] = mapped_column(ForeignKey("papers.id"), nullable=True, index=True)
    evidence_kind: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(Text)
    locator: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float)


class Hypothesis(AuditedEntity, Base):
    __tablename__ = "hypotheses"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    mechanism: Mapped[str] = mapped_column(Text)
    assumptions: Mapped[list[str]] = mapped_column(JSON, default=list)
    predictions: Mapped[list[str]] = mapped_column(JSON, default=list)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    contradicting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    novelty_estimate: Mapped[str] = mapped_column(String(120))
    testability_score: Mapped[float] = mapped_column(Float)
    estimated_cost: Mapped[str] = mapped_column(String(255))


class Experiment(AuditedEntity, Base):
    __tablename__ = "experiments"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    template_id: Mapped[str] = mapped_column(String(120))
    template_revision: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(40))
    specification: Mapped[dict[str, Any]] = mapped_column(JSON)


class ExperimentRun(AuditedEntity, Base):
    __tablename__ = "experiment_runs"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING")
    random_seed: Mapped[int] = mapped_column(Integer)
    environment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")


class Metric(AuditedEntity, Base):
    __tablename__ = "metrics"

    run_id: Mapped[UUID] = mapped_column(ForeignKey("experiment_runs.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(40), default="fraction")
    sample_count: Mapped[int] = mapped_column(Integer)


class Result(AuditedEntity, Base):
    __tablename__ = "results"

    run_id: Mapped[UUID] = mapped_column(ForeignKey("experiment_runs.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    statistics: Mapped[dict[str, Any]] = mapped_column(JSON)


class Critique(AuditedEntity, Base):
    __tablename__ = "critiques"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("experiment_runs.id"), index=True)
    outcome: Mapped[str] = mapped_column(String(40))
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class Artifact(AuditedEntity, Base):
    __tablename__ = "artifacts"

    run_id: Mapped[UUID] = mapped_column(ForeignKey("experiment_runs.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(80))
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))


class ProvenanceLink(AuditedEntity, Base):
    __tablename__ = "provenance_links"

    child_type: Mapped[str] = mapped_column(String(80), index=True)
    child_id: Mapped[UUID] = mapped_column(index=True)
    parent_type: Mapped[str] = mapped_column(String(80), index=True)
    parent_id: Mapped[UUID] = mapped_column(index=True)
    relationship: Mapped[str] = mapped_column(String(80))
    locator: Mapped[str | None] = mapped_column(String(255), nullable=True)

