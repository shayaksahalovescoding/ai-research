"""Stable, typed domain records shared across future storage adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DomainRecord(BaseModel):
    """Minimum auditable envelope required for all research objects."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    created_at: datetime
    updated_at: datetime
    schema_version: str = "1.0"
    provenance: dict[str, Any] = Field(default_factory=dict)


class ResearchProjectRecord(DomainRecord):
    name: str
    status: str


class ResearchQuestionRecord(DomainRecord):
    project_id: UUID
    text: str


class ResearchObjectiveRecord(DomainRecord):
    project_id: UUID
    statement: str


class PaperRecord(DomainRecord):
    source_id: UUID
    external_id: str
    title: str


class DocumentRecord(DomainRecord):
    paper_id: UUID | None = None
    location: str


class SourceRecord(DomainRecord):
    name: str
    uri: str
    source_type: str


class ClaimRecord(DomainRecord):
    statement: str
    support_level: str


class EvidenceRecord(DomainRecord):
    paper_id: UUID | None = None
    text: str
    evidence_kind: str


class DatasetRecord(DomainRecord):
    name: str
    version: str


class ExperimentRecord(DomainRecord):
    project_id: UUID
    hypothesis_id: UUID
    template_id: str
    specification: dict[str, Any]


class ExperimentConfigRecord(DomainRecord):
    experiment_id: UUID
    values: dict[str, Any]


class ExperimentRunRecord(DomainRecord):
    experiment_id: UUID
    status: str
    environment: dict[str, Any]


class MetricRecord(DomainRecord):
    run_id: UUID
    name: str
    value: float


class ResultRecord(DomainRecord):
    run_id: UUID
    summary: str


class HypothesisRecord(DomainRecord):
    project_id: UUID
    statement: str
    confidence: float


class HypothesisEvaluationRecord(DomainRecord):
    hypothesis_id: UUID
    score: float


class ObservationRecord(DomainRecord):
    statement: str


class ConclusionRecord(DomainRecord):
    statement: str
    certainty: str


class CritiqueRecord(DomainRecord):
    project_id: UUID
    outcome: str
    findings: list[dict[str, Any]]


class CitationRecord(DomainRecord):
    citing_paper_id: UUID
    cited_paper_id: UUID | None = None


class KnowledgeNodeRecord(DomainRecord):
    node_type: str
    label: str


class KnowledgeEdgeRecord(DomainRecord):
    source_node_id: UUID
    target_node_id: UUID
    relation: str


class ResearchTaskRecord(DomainRecord):
    project_id: UUID
    status: str


class AgentRunRecord(DomainRecord):
    agent_name: str
    trace_id: UUID


class ArtifactRecord(DomainRecord):
    run_id: UUID | None = None
    sha256: str


class ExecutionJobRecord(DomainRecord):
    experiment_id: UUID
    status: str


class ReproducibilityRecord(DomainRecord):
    run_id: UUID
    environment_fingerprint: dict[str, Any]

