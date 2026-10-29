from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateProjectRequest(StrictModel):
    name: str = Field(min_length=3, max_length=160)
    research_question: str = Field(min_length=12, max_length=2_000)
    objective: str | None = Field(default=None, max_length=2_000)


class ProjectResponse(StrictModel):
    id: UUID
    name: str
    status: str
    research_question: str
    objective: str | None = None
    created_at: datetime


class TaskResponse(StrictModel):
    id: UUID
    project_id: UUID
    status: str
    trace_id: UUID
    error_code: str | None = None
    error_message: str | None = None


class HypothesisResponse(StrictModel):
    id: UUID
    statement: str
    mechanism: str
    confidence: float
    novelty_estimate: str
    supporting_evidence_ids: list[UUID]


class ExperimentResponse(StrictModel):
    id: UUID
    project_id: UUID
    hypothesis_id: UUID
    template_id: str
    kind: str
    specification: dict[str, Any]


class CreateExperimentRequest(StrictModel):
    project_id: UUID
    hypothesis_id: UUID


class ResultResponse(StrictModel):
    run_id: UUID
    status: str
    metrics: dict[str, float]
    statistics: dict[str, float | int | list[float] | None]
    critique_outcome: str | None


class ProvenanceResponse(StrictModel):
    record_id: UUID
    record_type: str
    provenance: dict[str, Any]
    parents: list[dict[str, Any]]
