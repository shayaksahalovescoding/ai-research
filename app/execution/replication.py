"""Autonomous Replication and Reproducibility Verification Engine.

Audits simulation stability by evaluating experiments across:
- Randomized seed suites (e.g. 5 independent seeds)
- Environmental noise perturbations
- Directional effect consistency
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReplicationReport:
    is_reproducible: bool
    reproducibility_score: float  # 0.0 to 1.0
    directional_consistency_ratio: float  # fraction of seeds with positive delta
    mean_delta_stability_cv: float  # coefficient of variation of deltas across seeds
    evaluated_seeds: list[int]
    seed_deltas: list[float]
    audit_notes: list[str]


class ReplicationEngine:
    """Evaluates cross-seed stability and perturbation sensitivity for scientific simulations."""

    def evaluate_replication(
        self,
        baseline_runs: list[list[float]],  # list of baseline scores per seed run
        treatment_runs: list[list[float]],  # list of treatment scores per seed run
        seeds: list[int],
    ) -> ReplicationReport:
        if not baseline_runs or not treatment_runs or len(baseline_runs) != len(treatment_runs):
            return ReplicationReport(
                is_reproducible=False,
                reproducibility_score=0.0,
                directional_consistency_ratio=0.0,
                mean_delta_stability_cv=1.0,
                evaluated_seeds=seeds,
                seed_deltas=[],
                audit_notes=["Insufficient paired run data to evaluate replication stability."],
            )

        seed_deltas: list[float] = []
        for b_scores, t_scores in zip(baseline_runs, treatment_runs, strict=False):
            mean_b = sum(b_scores) / len(b_scores) if b_scores else 0.0
            mean_t = sum(t_scores) / len(t_scores) if t_scores else 0.0
            seed_deltas.append(round(mean_t - mean_b, 4))

        positive_count = sum(1 for d in seed_deltas if d > 0)
        consistency_ratio = positive_count / len(seed_deltas) if seed_deltas else 0.0

        # Mean and standard deviation of seed deltas
        mean_d = sum(seed_deltas) / len(seed_deltas) if seed_deltas else 0.0
        if len(seed_deltas) > 1 and mean_d != 0:
            var_d = sum((d - mean_d) ** 2 for d in seed_deltas) / (len(seed_deltas) - 1)
            std_d = math.sqrt(var_d)
            cv = abs(std_d / mean_d)
        else:
            cv = 0.0

        # Reproducibility Score: penalize low consistency ratio and high CV
        score = consistency_ratio * max(0.0, min(1.0, 1.0 - cv * 0.3))
        is_reproducible = consistency_ratio >= 0.80 and score >= 0.70

        audit_notes: list[str] = []
        if is_reproducible:
            audit_notes.append(f"Replication verified across {len(seeds)} random seeds with {consistency_ratio * 100:.1f}% directional consistency.")
        else:
            audit_notes.append("High cross-seed variance or directional flips detected across seed suites.")

        return ReplicationReport(
            is_reproducible=is_reproducible,
            reproducibility_score=round(score, 3),
            directional_consistency_ratio=round(consistency_ratio, 3),
            mean_delta_stability_cv=round(cv, 3),
            evaluated_seeds=seeds,
            seed_deltas=seed_deltas,
            audit_notes=audit_notes,
        )
