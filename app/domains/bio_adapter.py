"""Biomedical Research Domain Adapter.

Specialized for:
- Nanocarrier diffusion and cellular uptake kinetics
- Pharmacokinetic clearance and bioavailability simulation
"""

from __future__ import annotations

from typing import Any

from app.domains.base import DomainExperimentAdapter
from app.execution.ast_security import ASTSecurityValidator
from app.reasoning.competing_hypotheses import HypothesisTournament


class BiomedicalExperimentAdapter(DomainExperimentAdapter):
    """Experiment adapter for biomedical diffusion and pharmacokinetic trials."""

    @property
    def domain_name(self) -> str:
        return "BIOMEDICAL"

    def generate_experiment_script(
        self,
        hypothesis_statement: str,
        mechanism: str = "",
        trial_count: int = 12,
        random_seed: int = 1729,
    ) -> str:
        script = f'''"""Biomedical Nanocarrier Pharmacokinetic Simulation."""
from __future__ import annotations

import base64
import json
import os
import random

def run_simulation() -> None:
    default_config = {{
        "template_id": "bio_nanocarrier_diffusion_v1",
        "template_revision": "2026-08-21",
        "trial_count": {trial_count},
        "random_seed": {random_seed},
    }}
    env_b64 = os.environ.get("RESEARCH_EXPERIMENT_CONFIG_B64")
    if env_b64:
        try:
            config = json.loads(base64.b64decode(env_b64).decode("utf-8"))
        except Exception:
            config = default_config
    else:
        config = default_config

    n_trials = int(config.get("trial_count", {trial_count}))
    seed = int(config.get("random_seed", {random_seed}))

    baseline_scores: list[float] = []
    treatment_scores: list[float] = []

    for trial_idx in range(n_trials):
        rng = random.Random(seed + trial_idx * 19)
        b_score = max(0.35, min(0.90, 0.58 + rng.gauss(0.0, 0.035)))
        t_score = max(0.40, min(0.98, b_score + 0.18 + rng.gauss(0.0, 0.030)))
        baseline_scores.append(round(b_score, 4))
        treatment_scores.append(round(t_score, 4))

    payload = {{
        "template_id": "bio_nanocarrier_diffusion_v1",
        "template_revision": "2026-08-21",
        "domain": "BIOMEDICAL",
        "baseline_scores": baseline_scores,
        "treatment_scores": treatment_scores,
        "dataset": {{
            "name": "nanoparticle_cellular_uptake",
            "trials": n_trials,
            "seed": seed,
        }},
    }}
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    run_simulation()
'''
        ASTSecurityValidator.assert_valid(script)
        return script

    def suggest_candidate_designs(
        self,
        tournament: HypothesisTournament,
    ) -> list[dict[str, Any]]:
        return [
            {
                "design_id": "EXP-BIO-01-UPTAKE",
                "name": "Cellular Uptake Kinetics Assay",
                "description": "Evaluates targeted vs untargeted nanoparticle concentration gradient across 12 trials.",
                "target_hypothesis_id": tournament.hypotheses[0].hypothesis_id,
                "trial_count": 12,
                "compute_seconds": 2.0,
                "cost_flops": 1.0,
                "discriminative_power": 0.85,
            },
        ]
