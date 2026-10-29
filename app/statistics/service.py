from __future__ import annotations

import math
import random
import statistics
from dataclasses import asdict, dataclass

from app.core.errors import FailureCode, ResearchWorkflowError


@dataclass(frozen=True, slots=True)
class StatisticalSummary:
    effect_size: float
    confidence_interval: list[float]
    p_value: float
    sample_count: int
    variance: float
    mean_difference: float
    statistical_power: float | None

    def as_dict(self) -> dict[str, float | int | list[float] | None]:
        return asdict(self)


class StatisticsService:
    """Performs deterministic numerical analysis over paired experimental scores."""

    def analyze_paired(
        self,
        baseline_scores: list[float],
        treatment_scores: list[float],
        *,
        bootstrap_samples: int = 2_000,
        permutation_samples: int = 10_000,
        random_seed: int = 1729,
    ) -> StatisticalSummary:
        if len(baseline_scores) != len(treatment_scores) or len(baseline_scores) < 3:
            raise ResearchWorkflowError(
                FailureCode.STATISTICS_FAILED,
                "Paired analysis needs at least three baseline and treatment scores.",
            )
        if not all(math.isfinite(value) for value in baseline_scores + treatment_scores):
            raise ResearchWorkflowError(FailureCode.STATISTICS_FAILED, "Scores must be finite numbers.")

        differences = [
            treatment - baseline
            for baseline, treatment in zip(baseline_scores, treatment_scores, strict=True)
        ]
        mean_difference = statistics.fmean(differences)
        variance = statistics.variance(differences)
        standard_deviation = math.sqrt(variance)
        if standard_deviation > 1e-12:
            effect_size = mean_difference / standard_deviation
        elif mean_difference > 0:
            effect_size = 10.0  # Constant positive improvement
        elif mean_difference < 0:
            effect_size = -10.0
        else:
            effect_size = 0.0
        confidence_interval = self._bootstrap_mean_interval(differences, bootstrap_samples, random_seed)
        p_value = self._paired_permutation_p_value(differences, permutation_samples, random_seed + 1)
        return StatisticalSummary(
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            p_value=p_value,
            sample_count=len(differences),
            variance=variance,
            mean_difference=mean_difference,
            statistical_power=None,
        )

    @staticmethod
    def _bootstrap_mean_interval(
        differences: list[float], repetitions: int, seed: int
    ) -> list[float]:
        generator = random.Random(seed)
        size = len(differences)
        means = sorted(
            statistics.fmean(generator.choice(differences) for _ in range(size))
            for _ in range(repetitions)
        )
        lower_index = int(0.025 * (repetitions - 1))
        upper_index = int(0.975 * (repetitions - 1))
        return [means[lower_index], means[upper_index]]

    @staticmethod
    def _paired_permutation_p_value(
        differences: list[float], repetitions: int, seed: int
    ) -> float:
        observed = abs(statistics.fmean(differences))
        generator = random.Random(seed)
        extreme_count = 0
        for _ in range(repetitions):
            permuted_mean = statistics.fmean(
                difference if generator.getrandbits(1) else -difference for difference in differences
            )
            if abs(permuted_mean) >= observed:
                extreme_count += 1
        return (extreme_count + 1) / (repetitions + 1)
