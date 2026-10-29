"""Experiment Catalog and Dynamic Code Sandbox Template Builder."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from app.core.errors import FailureCode, ResearchWorkflowError
from app.execution.ast_security import ASTSecurityValidator
from app.execution.code_generator import DynamicCodeGenerator

TOY_LOGISTIC_TEMPLATE_ID = "toy_logistic_regression_v1"
DYNAMIC_SIMULATION_TEMPLATE_ID = "dynamic_generated_simulation_v1"
EXPERIMENT_TEMPLATE_REVISION = "2026-08-21"


@dataclass(frozen=True, slots=True)
class RegisteredExperiment:
    template_id: str
    template_revision: str
    specification: dict[str, Any]


class ExperimentCatalog:
    """Catalog for dynamic LLM-generated and registered sandbox experiments."""

    def __init__(self, code_generator: DynamicCodeGenerator | None = None) -> None:
        self._code_generator = code_generator or DynamicCodeGenerator()

    def build_for_hypothesis(
        self,
        hypothesis_statement: str,
        mechanism: str = "",
        iteration: int = 1,
    ) -> RegisteredExperiment:
        if not hypothesis_statement:
            raise ResearchWorkflowError(
                FailureCode.EXPERIMENT_GENERATION_FAILED,
                "A non-empty hypothesis is required to design an experiment.",
            )

        sample_size = min(24, 12 + 4 * (iteration - 1))
        random_seed = 1729 + (iteration - 1) * 31

        # Generate custom Python simulation script tailored to this hypothesis
        generated_code = self._code_generator.generate_experiment_script(
            hypothesis_statement=hypothesis_statement,
            mechanism=mechanism,
            trial_count=sample_size,
            random_seed=random_seed,
        )

        # Statically verify with AST security filter
        ASTSecurityValidator.assert_valid(generated_code)
        code_sha256 = hashlib.sha256(generated_code.encode("utf-8")).hexdigest()

        return RegisteredExperiment(
            template_id=DYNAMIC_SIMULATION_TEMPLATE_ID,
            template_revision=EXPERIMENT_TEMPLATE_REVISION,
            specification={
                "objective": f"Empirically evaluate hypothesis via AST-verified simulation (Iteration {iteration}).",
                "classification": "EXPLORATORY",
                "independent_variables": {"optimization_iterations": [20, 400 + 50 * (iteration - 1)]},
                "dependent_variables": ["held_out_accuracy", "paired_accuracy_delta"],
                "controls": ["same synthetic generator", "same per-trial seed", "same test split"],
                "baseline": {"name": "short_training_budget", "iterations": 20},
                "treatment": {"name": "extended_training_budget", "iterations": 400 + 50 * (iteration - 1)},
                "dataset": {"name": "tailored_synthetic_domain_v1", "version": "1.0"},
                "sample_size": sample_size,
                "random_seed": random_seed,
                "evaluation_metrics": ["accuracy"],
                "statistical_tests": ["paired_permutation_test", "bootstrap_confidence_interval"],
                "resource_budget": {"cpu": 1, "memory": "512m", "runtime_seconds": 45},
                "stopping_criteria": [f"finish all {sample_size} planned trials", "stop on sandbox timeout"],
                "expected_outcomes": ["positive paired accuracy difference"],
                "failure_conditions": ["missing result artifact", "non-finite metric", "sandbox non-zero exit"],
                "generated_code": generated_code,
                "code_sha256": code_sha256,
                "ast_security_verified": True,
            },
        )

    def validate_template(self, template_id: str) -> None:
        valid_templates = {TOY_LOGISTIC_TEMPLATE_ID, DYNAMIC_SIMULATION_TEMPLATE_ID}
        if template_id not in valid_templates:
            raise ResearchWorkflowError(
                FailureCode.EXPERIMENT_GENERATION_FAILED,
                f"Experiment template '{template_id}' is not registered.",
            )
