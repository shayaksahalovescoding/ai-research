"""Unit tests for AST Security Filter, Dynamic Code Generation, and Sandbox Execution."""

from __future__ import annotations

import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
import pytest

from app.execution.ast_security import ASTSecurityError, ASTSecurityValidator
from app.execution.code_generator import DynamicCodeGenerator
from app.execution.sandbox import DeterministicSandboxDouble
from app.experiments.catalog import DYNAMIC_SIMULATION_TEMPLATE_ID, ExperimentCatalog
from gui.widgets.experiment_tab import ExperimentTab


def _ensure_qt_app() -> QApplication:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    return QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])


def test_ast_security_validator_clean_code() -> None:
    clean_code = """
import numpy as np
import json
import math
import random

def simulate(n=10):
    rng = np.random.default_rng(42)
    return [float(x) for x in rng.normal(0.5, 0.1, n)]

if __name__ == "__main__":
    print(json.dumps({"scores": simulate()}))
"""
    is_valid, violations = ASTSecurityValidator.validate(clean_code)
    assert is_valid
    assert len(violations) == 0
    # Should not raise
    ASTSecurityValidator.assert_valid(clean_code)


def test_ast_security_validator_catches_banned_modules() -> None:
    malicious_scripts = [
        "import socket; s = socket.socket()",
        "import requests; requests.get('https://example.com')",
        "import subprocess; subprocess.run(['ls'])",
        "from os import system; system('rm -rf /')",
        "import urllib.request",
        "import pty; pty.spawn('/bin/sh')",
    ]

    for script in malicious_scripts:
        is_valid, violations = ASTSecurityValidator.validate(script)
        assert not is_valid
        assert len(violations) >= 1
        with pytest.raises(ASTSecurityError):
            ASTSecurityValidator.assert_valid(script)


def test_ast_security_validator_catches_eval_and_introspection() -> None:
    eval_scripts = [
        "eval('1 + 1')",
        "exec('print(123)')",
        "().__class__.__subclasses__()",
        "import os; os.system('echo 1')",
        "import os; os.remove('/tmp/file')",
    ]

    for script in eval_scripts:
        is_valid, violations = ASTSecurityValidator.validate(script)
        assert not is_valid
        assert len(violations) >= 1


def test_dynamic_code_generator() -> None:
    generator = DynamicCodeGenerator()
    code = generator.generate_experiment_script(
        hypothesis_statement="Lipid nanoparticles enhance targeted drug uptake while reducing toxicity.",
        mechanism="Targeted electrostatic interaction promotes selective cellular endocytosis.",
        trial_count=12,
        random_seed=42,
    )
    assert code is not None
    assert "baseline_scores" in code
    assert "treatment_scores" in code

    # Assert generated code passes AST security
    is_valid, violations = ASTSecurityValidator.validate(code)
    assert is_valid, f"Violations: {violations}"


def test_experiment_catalog_builds_dynamic_code() -> None:
    catalog = ExperimentCatalog()
    exp = catalog.build_for_hypothesis(
        hypothesis_statement="Extended optimization budget improves held-out model accuracy.",
        mechanism="Iterative gradient updates lower empirical loss surface.",
        iteration=1,
    )
    assert exp.template_id == DYNAMIC_SIMULATION_TEMPLATE_ID
    assert "generated_code" in exp.specification
    assert exp.specification["ast_security_verified"] is True
    assert exp.specification["code_sha256"] != ""


def test_sandbox_executes_dynamic_script(tmp_path: Path) -> None:
    generator = DynamicCodeGenerator()
    code = generator.generate_experiment_script("Test hypothesis", "Test mechanism", trial_count=10)

    sandbox = DeterministicSandboxDouble()
    run_dir = tmp_path / "run_01"
    config = {
        "generated_code": code,
        "sample_size": 10,
        "random_seed": 1729,
        "baseline": {"iterations": 20},
        "treatment": {"iterations": 400},
    }
    result = sandbox.run(DYNAMIC_SIMULATION_TEMPLATE_ID, config, run_dir)
    assert result.output is not None
    assert "baseline_scores" in result.output
    assert "treatment_scores" in result.output
    assert result.code_path is not None
    assert result.code_path.exists()


def test_experiment_tab_code_viewer() -> None:
    _ensure_qt_app()
    tab = ExperimentTab()
    assert tab.code_viewer is not None

    sample_code = "import numpy as np\nprint('Simulation running')\n"
    sample_result = {
        "metrics": {"baseline_mean_accuracy": 0.60, "treatment_mean_accuracy": 0.78},
        "statistics": {"mean_difference": 0.18, "effect_size": 1.4, "p_value": 0.001, "confidence_interval": [0.10, 0.26], "sample_count": 12},
        "critique_outcome": "ACCEPT",
    }
    tab.set_results(sample_result, generated_code=sample_code)
    assert "Simulation running" in tab.code_viewer.toPlainText()

    tab._copy_code_to_clipboard()

    tab.set_results(None)
    assert "Run research workflow" in tab.code_viewer.toPlainText()
    tab.close()
