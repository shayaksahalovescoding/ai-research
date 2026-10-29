from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import pytest

from app.core.config import Settings
from app.core.errors import FailureCode, ResearchWorkflowError
from app.execution.sandbox import DockerSandboxRunner
from app.experiments.catalog import ExperimentCatalog, TOY_LOGISTIC_TEMPLATE_ID


def test_sandbox_command_is_fixed_and_does_not_include_research_configuration(tmp_path: Path) -> None:
    runner = DockerSandboxRunner(
        Settings(artifact_root=tmp_path / "artifacts", sandbox_volume="audit_artifacts"),
        ExperimentCatalog(),
    )
    command = runner._build_command("eyJ0cmlhbF9jb3VudCI6MTJ9")

    assert "--network" in command
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop" in command
    assert "ALL" in command
    assert "--security-opt" in command
    assert "no-new-privileges:true" in command
    assert "--mount" not in command
    assert "/work:rw,noexec,nosuid,nodev,size=64m" in command
    assert "curl" not in command


def test_sandbox_fails_closed_when_docker_daemon_is_unreachable(tmp_path: Path) -> None:
    runner = DockerSandboxRunner(
        Settings(artifact_root=tmp_path / "artifacts", sandbox_volume="audit_artifacts"),
        ExperimentCatalog(),
    )
    with patch("subprocess.run", side_effect=OSError("Docker daemon not running")):
        with pytest.raises(ResearchWorkflowError) as exc_info:
            runner.run(TOY_LOGISTIC_TEMPLATE_ID, {"trial_count": 5}, tmp_path / "run_01")
        assert exc_info.value.code == FailureCode.SANDBOX_UNAVAILABLE
