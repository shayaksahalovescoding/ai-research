from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.execution.sandbox import DockerSandboxRunner
from app.experiments.catalog import ExperimentCatalog, TOY_LOGISTIC_TEMPLATE_ID


@pytest.mark.docker
@pytest.mark.skipif(
    os.getenv("RUN_DOCKER_SMOKE_TESTS") != "1",
    reason="Set RUN_DOCKER_SMOKE_TESTS=1 after building the local sandbox image.",
)
def test_registered_template_runs_in_real_docker_sandbox() -> None:
    settings = Settings(
        artifact_root=Path("/app/artifacts"),
        sandbox_image="ai-research-experiment:dev",
        sandbox_volume="research_artifacts",
        sandbox_timeout_seconds=45,
    )
    result = DockerSandboxRunner(settings, ExperimentCatalog()).run(
        TOY_LOGISTIC_TEMPLATE_ID,
        {"baseline_iterations": 20, "treatment_iterations": 400, "trial_count": 12, "random_seed": 1729},
        settings.artifact_root / "smoke-test-project" / str(uuid4()),
    )

    assert len(result.output["baseline_scores"]) == 12
    assert len(result.output["treatment_scores"]) == 12
    assert result.environment["network"] == "none"
