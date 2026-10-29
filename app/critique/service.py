"""Deep Causal & Threat-to-Validity Scientific Critic.

Audits empirical experiments across multi-dimensional epistemic criteria:
- Statistical Power & Sample Sizing (1 - β)
- Effect Magnitude vs Variance (Cohen's d)
- Strawman Baseline & Variance Inflation Detection
- Low-Power Inconclusive Trial Detection (prevents falsely accepting H0)
- Potential Target Contamination / Data Leakage Anomaly Checks
- Preregistered vs Exploratory Scope Validity Boundaries
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from app.statistics.service import StatisticalSummary


@dataclass(frozen=True, slots=True)
class CritiqueFinding:
    severity: str  # "INFO" | "WARNING" | "ERROR"
    code: str
    message: str
    dimension: str = "GENERAL"  # "POWER" | "EFFECT_SIZE" | "BASELINE" | "INTERVAL" | "VALIDITY" | "LEAKAGE"


@dataclass(frozen=True, slots=True)
class CritiqueReport:
    outcome: str  # "ACCEPT_WITH_LIMITATIONS" | "NEEDS_REVISION" | "REJECT"
    findings: list[CritiqueFinding]
    statistical_power: float = 0.80
    effect_magnitude_tier: str = "MODERATE"
    confounder_risk: str = "LOW"

    def as_persisted_findings(self) -> list[dict[str, str]]:
        return [asdict(finding) for finding in self.findings]


class ScientificCritic:
    """Multi-dimensional epistemic referee evaluating causal validity and statistical integrity."""

    def evaluate(
        self,
        statistics_summary: StatisticalSummary,
        experiment_kind: str = "EXPLORATORY",
        baseline_scores: list[float] | None = None,
        treatment_scores: list[float] | None = None,
        replication_report: Any | None = None,
    ) -> CritiqueReport:
        findings: list[CritiqueFinding] = []

        # 1. Exploratory vs Confirmatory Scope Framing
        if experiment_kind.upper() == "EXPLORATORY":
            findings.append(
                CritiqueFinding(
                    severity="INFO",
                    code="EXPLORATORY_SCOPE",
                    dimension="VALIDITY",
                    message=(
                        "This trial is exploratory; conclusions must be framed with explicit external validity bounds "
                        "and validated across independent replication seeds."
                    ),
                )
            )

        # 2. Sample Size & Statistical Power Auditing
        n = statistics_summary.sample_count
        d_val = statistics_summary.effect_size
        d_abs = abs(d_val)

        # Estimate post-hoc power: Φ(d * sqrt(N) - 1.96)
        if n > 1 and d_abs > 0:
            z = d_abs * math.sqrt(n) - 1.96
            power = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
            power = max(0.05, min(0.999, power))
        else:
            power = 0.50

        p_val = statistics_summary.p_value
        mean_diff = getattr(statistics_summary, "mean_difference", getattr(statistics_summary, "mean_delta", 0.0))

        # Underpowered inconclusive check (Prevents falsely accepting null)
        if p_val >= 0.05 and power < 0.70:
            findings.append(
                CritiqueFinding(
                    severity="WARNING",
                    code="INCONCLUSIVE_DUE_TO_LOW_POWER",
                    dimension="POWER",
                    message=(
                        f"Non-significant result (p={p_val:.3f}) with low power ({power * 100:.1f}%). "
                        "Study is inconclusive; data cannot be used to confirm the null hypothesis."
                    ),
                )
            )
        elif n < 10:
            findings.append(
                CritiqueFinding(
                    severity="WARNING",
                    code="LOW_SAMPLE_COUNT",
                    dimension="POWER",
                    message=f"Sample count (N={n}) is below 10, increasing estimation variance and sensitivity to outliers.",
                )
            )

        # 3. Effect Size Magnitude & Practical Significance vs Triviality
        if mean_diff <= 0 or d_val <= 0:
            findings.append(
                CritiqueFinding(
                    severity="ERROR",
                    code="NON_POSITIVE_EFFECT",
                    dimension="EFFECT_SIZE",
                    message="The measured standardized paired effect (Cohen's d) is non-positive, providing insufficient empirical support for the predicted improvement.",
                )
            )
            tier = "NON_POSITIVE"
        elif p_val < 0.05 and d_val < 0.20:
            # Significant but trivial effect
            findings.append(
                CritiqueFinding(
                    severity="WARNING",
                    code="TRIVIAL_EFFECT_SIZE_DESPITE_SIGNIFICANCE",
                    dimension="EFFECT_SIZE",
                    message=(
                        f"Effect size d={d_val:.3f} is trivial (d < 0.20) despite statistical significance (p={p_val:.3f}). "
                        "Practical scientific impact is negligible."
                    ),
                )
            )
            tier = "TRIVIAL"
        elif d_val < 0.5:
            tier = "SMALL"
        elif d_val < 0.8:
            tier = "MODERATE"
        else:
            tier = "LARGE"

        # 4. Bootstrap Confidence Interval Directionality
        ci_lower, ci_upper = statistics_summary.confidence_interval
        if ci_lower <= 0:
            if mean_diff <= 0 or p_val >= 0.05:
                findings.append(
                    CritiqueFinding(
                        severity="ERROR",
                        code="INTERVAL_INCLUDES_NO_IMPROVEMENT",
                        dimension="INTERVAL",
                        message=f"The 95% bootstrap confidence interval [{ci_lower:.4f}, {ci_upper:.4f}] does not exclude zero or negative delta.",
                    )
                )
            else:
                findings.append(
                    CritiqueFinding(
                        severity="WARNING",
                        code="INTERVAL_MARGINAL_UNCERTAINTY",
                        dimension="INTERVAL",
                        message=f"Lower bootstrap bound [{ci_lower:.4f}] touches zero, indicating marginal confidence.",
                    )
                )

        # 5. Baseline Quality & Strawman Verification
        if baseline_scores:
            mean_b = sum(baseline_scores) / len(baseline_scores)
            var_b = sum((x - mean_b) ** 2 for x in baseline_scores) / len(baseline_scores)
            if var_b < 1e-9:
                findings.append(
                    CritiqueFinding(
                        severity="WARNING",
                        code="SUSPICIOUS_STRAWMAN_BASELINE",
                        dimension="BASELINE",
                        message="Baseline exhibits zero empirical variance, suggesting an uncalibrated strawman baseline.",
                    )
                )
            elif mean_b < 0.15:
                findings.append(
                    CritiqueFinding(
                        severity="WARNING",
                        code="DEGRADED_BASELINE_FLOOR",
                        dimension="BASELINE",
                        message=f"Baseline mean ({mean_b:.3f}) is near zero, artificially inflating relative treatment delta.",
                    )
                )

        # 6. Data Leakage / Target Contamination Anomaly
        if treatment_scores and baseline_scores:
            if mean_diff > 0.45 and statistics_summary.variance < 1e-6:
                findings.append(
                    CritiqueFinding(
                        severity="WARNING",
                        code="ANOMALOUS_EFFECT_LEAKAGE_RISK",
                        dimension="LEAKAGE",
                        message="Anomalously large deterministic effect delta with zero residual variance indicates possible target contamination.",
                    )
                )

        # 7. Replication Stability Audit
        if replication_report is not None and not getattr(replication_report, "is_reproducible", True):
            score = getattr(replication_report, "reproducibility_score", 0.0)
            findings.append(
                CritiqueFinding(
                    severity="WARNING" if experiment_kind == "EXPLORATORY" else "ERROR",
                    code="REPLICATION_INSTABILITY",
                    dimension="REPLICATION",
                    message=f"Cross-seed replication failed (score: {score * 100:.1f}%). Directional consistency across randomized seeds is insufficient.",
                )
            )

        # 7. Final Outcome Determination
        has_error = any(f.severity == "ERROR" for f in findings)
        has_warning = any(f.severity == "WARNING" for f in findings)

        if has_error:
            outcome = "REJECT"
        elif has_warning:
            outcome = "NEEDS_REVISION"
        else:
            outcome = "ACCEPT_WITH_LIMITATIONS"

        confound_risk = "HIGH" if has_error else ("MODERATE" if has_warning else "LOW")

        return CritiqueReport(
            outcome=outcome,
            findings=findings,
            statistical_power=round(power, 3),
            effect_magnitude_tier=tier,
            confounder_risk=confound_risk,
        )
