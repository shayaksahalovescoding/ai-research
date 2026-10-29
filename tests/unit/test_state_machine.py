import pytest

from app.core.errors import ResearchWorkflowError
from app.orchestration.state import ResearchStage, ensure_transition


def test_state_machine_accepts_workflow_start() -> None:
    ensure_transition(ResearchStage.CREATED.value, ResearchStage.RETRIEVING)


def test_state_machine_rejects_skipping_security_critical_stages() -> None:
    with pytest.raises(ResearchWorkflowError, match="Cannot transition"):
        ensure_transition(ResearchStage.CREATED.value, ResearchStage.EXECUTING)

