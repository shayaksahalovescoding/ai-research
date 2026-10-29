from __future__ import annotations

from enum import StrEnum

from app.core.errors import FailureCode, ResearchWorkflowError


class ResearchStage(StrEnum):
    CREATED = "CREATED"
    RETRIEVING = "RETRIEVING"
    EXTRACTING = "EXTRACTING"
    HYPOTHESIZING = "HYPOTHESIZING"
    PLANNING_EXPERIMENT = "PLANNING_EXPERIMENT"
    EXECUTING = "EXECUTING"
    ANALYZING = "ANALYZING"
    CRITIQUING = "CRITIQUING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[ResearchStage, set[ResearchStage]] = {
    ResearchStage.CREATED: {ResearchStage.RETRIEVING, ResearchStage.FAILED},
    ResearchStage.RETRIEVING: {ResearchStage.EXTRACTING, ResearchStage.FAILED},
    ResearchStage.EXTRACTING: {ResearchStage.HYPOTHESIZING, ResearchStage.FAILED},
    ResearchStage.HYPOTHESIZING: {ResearchStage.PLANNING_EXPERIMENT, ResearchStage.FAILED},
    ResearchStage.PLANNING_EXPERIMENT: {ResearchStage.EXECUTING, ResearchStage.FAILED},
    ResearchStage.EXECUTING: {ResearchStage.ANALYZING, ResearchStage.FAILED},
    ResearchStage.ANALYZING: {ResearchStage.CRITIQUING, ResearchStage.FAILED},
    ResearchStage.CRITIQUING: {
        ResearchStage.HYPOTHESIZING,
        ResearchStage.PLANNING_EXPERIMENT,
        ResearchStage.COMPLETED,
        ResearchStage.FAILED,
    },
    ResearchStage.COMPLETED: set(),
    ResearchStage.FAILED: set(),
}


def ensure_transition(current: str, target: ResearchStage) -> None:
    try:
        allowed = _ALLOWED_TRANSITIONS[ResearchStage(current)]
    except ValueError as error:
        raise ResearchWorkflowError(
            FailureCode.INVALID_STATE,
            f"Unknown research stage '{current}'.",
        ) from error
    if target not in allowed:
        raise ResearchWorkflowError(
            FailureCode.INVALID_STATE,
            f"Cannot transition research task from {current} to {target}.",
        )

