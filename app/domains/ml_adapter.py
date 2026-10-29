"""Machine Learning & AI Empirical Research Domain Adapter.

Specialized for:
- Non-convex optimization loss landscape dynamics (adaptive curvature momentum)
- Continuous control reinforcement learning (optimistic Q-ensembles vs single critic)
- Sparsity-inducing regularization and out-of-distribution generalization
"""

from __future__ import annotations

from typing import Any

from app.domains.base import DomainExperimentAdapter
from app.execution.ast_security import ASTSecurityValidator
from app.execution.code_generator import DynamicCodeGenerator
from app.reasoning.competing_hypotheses import HypothesisTournament


class MLExperimentAdapter(DomainExperimentAdapter):
    """Experiment adapter for Machine Learning and optimization empirical simulations."""

    def __init__(self, code_generator: DynamicCodeGenerator | None = None) -> None:
        self._generator = code_generator or DynamicCodeGenerator()

    @property
    def domain_name(self) -> str:
        return "MACHINE_LEARNING"

    def generate_experiment_script(
        self,
        hypothesis_statement: str,
        mechanism: str = "",
        trial_count: int = 12,
        random_seed: int = 1729,
    ) -> str:
        script = self._generator.generate_experiment_script(
            hypothesis_statement,
            mechanism=mechanism,
            trial_count=trial_count,
            random_seed=random_seed,
        )
        ASTSecurityValidator.assert_valid(script)
        return script

    def suggest_candidate_designs(
        self,
        tournament: HypothesisTournament,
    ) -> list[dict[str, Any]]:
        return [
            {
                "design_id": "EXP-ML-01-AIRC",
                "name": "Adaptive Curvature Momentum Scaling",
                "description": "High-curvature ill-conditioned quadratic surface benchmark with 12 paired trials.",
                "target_hypothesis_id": tournament.hypotheses[0].hypothesis_id,
                "trial_count": 12,
                "compute_seconds": 2.5,
                "cost_flops": 1.0,
                "discriminative_power": 0.88,
            },
            {
                "design_id": "EXP-ML-02-ABLATION",
                "name": "Ablation of Curvature Damping",
                "description": "Ablation test isolating learning rate schedule vs curvature estimate.",
                "target_hypothesis_id": tournament.hypotheses[1].hypothesis_id,
                "trial_count": 8,
                "compute_seconds": 1.5,
                "cost_flops": 0.6,
                "discriminative_power": 0.70,
            },
            {
                "design_id": "EXP-ML-03-NOISE-STRESS",
                "name": "Stochastic Gradient Noise Stress Test",
                "description": "Varying batch size noise variance across 16 paired runs.",
                "target_hypothesis_id": tournament.hypotheses[2].hypothesis_id if len(tournament.hypotheses) > 2 else "H_ALT",
                "trial_count": 16,
                "compute_seconds": 4.0,
                "cost_flops": 1.8,
                "discriminative_power": 0.92,
            },
        ]
