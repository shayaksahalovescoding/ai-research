"""Isolated Docker Sandbox and Dynamic Code Execution Engine."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings
from app.core.errors import FailureCode, ResearchWorkflowError
from app.execution.ast_security import ASTSecurityValidator
from app.experiments.catalog import (
    DYNAMIC_SIMULATION_TEMPLATE_ID,
    TOY_LOGISTIC_TEMPLATE_ID,
    ExperimentCatalog,
)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    output: dict[str, Any]
    stdout: str
    stderr: str
    artifact_path: Path
    artifact_sha256: str
    environment: dict[str, str | int | float]
    code_path: Path | None = None
    code_sha256: str | None = None


class SandboxRunner(Protocol):
    def run(self, template_id: str, configuration: dict[str, Any], run_directory: Path) -> SandboxResult: ...


class DockerSandboxRunner:
    """Executes registered experiment templates and AST-verified dynamic scripts using Docker isolation."""

    def __init__(self, settings: Settings, catalog: ExperimentCatalog) -> None:
        self._settings = settings
        self._catalog = catalog

    def run(self, template_id: str, configuration: dict[str, Any], run_directory: Path) -> SandboxResult:
        self._catalog.validate_template(template_id)
        run_directory.mkdir(parents=True, exist_ok=False)

        generated_code = configuration.get("generated_code")
        code_path: Path | None = None
        code_sha256: str | None = None

        if generated_code:
            # Statically assert AST security
            ASTSecurityValidator.assert_valid(generated_code)
            code_path = run_directory / "experiment.py"
            code_path.write_text(generated_code, encoding="utf-8")
            code_sha256 = hashlib.sha256(generated_code.encode("utf-8")).hexdigest()

        input_path = run_directory / "input.json"
        input_payload = json.dumps(configuration, sort_keys=True)
        output_path = run_directory / "output.json"
        input_path.write_text(input_payload, encoding="utf-8")

        encoded_configuration = base64.b64encode(input_payload.encode("utf-8")).decode("ascii")

        # Execute in Docker or safe isolated subprocess fallback
        completed = self._execute_sandboxed(encoded_configuration, code_path, run_directory)

        if completed.returncode != 0:
            raise ResearchWorkflowError(
                FailureCode.SANDBOX_FAILED,
                f"Sandbox returned non-zero exit code {completed.returncode}: {completed.stderr[-1_000:]}",
            )

        try:
            # Parse json from stdout
            output = json.loads(completed.stdout.strip())
        except json.JSONDecodeError as error:
            raise ResearchWorkflowError(
                FailureCode.SANDBOX_FAILED,
                f"Sandbox stdout does not contain the required JSON result: {error}\nStdout: {completed.stdout[:300]}",
            ) from error

        output_path.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
        digest = hashlib.sha256(output_path.read_bytes()).hexdigest()

        return SandboxResult(
            output=output,
            stdout=completed.stdout,
            stderr=completed.stderr,
            artifact_path=output_path,
            artifact_sha256=digest,
            environment={
                "runner": "docker",
                "image": self._settings.sandbox_image,
                "python_host": sys.version.split()[0],
                "network": "none",
                "ast_security": "verified",
            },
            code_path=code_path,
            code_sha256=code_sha256,
        )

    def _execute_sandboxed(
        self,
        encoded_configuration: str,
        code_path: Path | None,
        run_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        # Strict Zero-Trust Security Boundary: Docker container execution is MANDATORY.
        # Verify Docker daemon reachability before executing any autonomous code.
        try:
            ping = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            if ping.returncode != 0:
                raise ResearchWorkflowError(
                    FailureCode.SANDBOX_UNAVAILABLE,
                    "Docker sandbox daemon is unreachable. Autonomous code execution blocked to prevent unsafe host execution.",
                )
        except (OSError, subprocess.TimeoutExpired) as err:
            raise ResearchWorkflowError(
                FailureCode.SANDBOX_UNAVAILABLE,
                f"Docker daemon connection failed ({err}). Execution blocked for security.",
            ) from err

        command = self._build_docker_command(encoded_configuration, code_path=code_path)
        try:
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self._settings.sandbox_timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise ResearchWorkflowError(
                FailureCode.SANDBOX_FAILED,
                f"Docker sandbox exceeded timeout of {self._settings.sandbox_timeout_seconds} seconds.",
            ) from error

    def _build_command(self, encoded_configuration: str) -> list[str]:
        return self._build_docker_command(encoded_configuration)

    def _build_docker_command(self, encoded_configuration: str, code_path: Path | None = None) -> list[str]:
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "64",
            "--memory",
            self._settings.sandbox_memory_limit,
            "--cpus",
            str(self._settings.sandbox_cpu_limit),
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--tmpfs",
            "/work:rw,noexec,nosuid,nodev,size=64m",
            "--user",
            "10001:10001",
            "--env",
            f"RESEARCH_EXPERIMENT_CONFIG_B64={encoded_configuration}",
        ]
        if code_path and code_path.exists():
            cmd.extend(["-v", f"{code_path.resolve()}:/app/experiment.py:ro"])
        cmd.append(self._settings.sandbox_image)
        return cmd


class DeterministicSandboxDouble:
    """Explicit test double for unit testing without Docker or subprocess overhead."""

    def run(self, template_id: str, configuration: dict[str, Any], run_directory: Path) -> SandboxResult:
        valid_templates = {TOY_LOGISTIC_TEMPLATE_ID, DYNAMIC_SIMULATION_TEMPLATE_ID}
        if template_id not in valid_templates:
            raise AssertionError(f"Test double received unregistered template: {template_id}")

        run_directory.mkdir(parents=True, exist_ok=True)

        generated_code = configuration.get("generated_code")
        code_path: Path | None = None
        code_sha256: str | None = None
        if generated_code:
            ASTSecurityValidator.assert_valid(generated_code)
            code_path = run_directory / "experiment.py"
            code_path.write_text(generated_code, encoding="utf-8")
            code_sha256 = hashlib.sha256(generated_code.encode("utf-8")).hexdigest()

        output = {
            "template_id": template_id,
            "template_revision": "test-double",
            "baseline_scores": [0.61, 0.63, 0.60, 0.62, 0.61, 0.63, 0.60, 0.62, 0.61, 0.62, 0.60, 0.63],
            "treatment_scores": [0.75, 0.76, 0.74, 0.77, 0.75, 0.76, 0.74, 0.77, 0.75, 0.76, 0.74, 0.77],
            "dataset": {"name": "deterministic_synthetic_domain_v1", "version": "1.0"},
        }
        artifact_path = run_directory / "output.json"
        artifact_path.write_text(json.dumps(output), encoding="utf-8")

        return SandboxResult(
            output=output,
            stdout=json.dumps(output),
            stderr="",
            artifact_path=artifact_path,
            artifact_sha256=hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            environment={"runner": "test-double", "network": "none", "ast_security": "verified"},
            code_path=code_path,
            code_sha256=code_sha256,
        )
