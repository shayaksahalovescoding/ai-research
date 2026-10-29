"""Dynamic 5-Hypothesis Tournament Formulation with Evidence-Derived Alternatives & Sequential Priors.

Synthesizes 5 mutually exclusive hypotheses with calibrated predictive distributions:
1. H_PRIMARY_MECHANISM: Proposed causal mechanism drives significant empirical gain
2. H_NULL: Observed delta is mini-batch sampling noise / zero true effect
3. H_CONFOUNDER: Empirical gain is driven by parameter scale or hyperparameter tuning confounder
4. H_MEASUREMENT_ARTIFACT: Gain is an artifact of initialization surface or metric sensitivity
5. H_ALT_MECHANISM: Gain occurs via a separate, competing causal explanation derived from literature
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.evidence.extractor import ExtractedEvidence
from app.reasoning.gap_discovery import ResearchGap


# Discrete outcome states for Expected Information Gain computation
OUTCOME_STRONG_POSITIVE = "STRONG_POSITIVE"      # delta > 0.12, d > 0.70
OUTCOME_MODERATE_POSITIVE = "MODERATE_POSITIVE"  # 0.04 < delta <= 0.12, 0.3 <= d <= 0.7
OUTCOME_NULL = "NULL_EFFECT"                     # -0.02 <= delta <= 0.04, -0.2 < d < 0.3
OUTCOME_NEGATIVE = "NEGATIVE_EFFECT"             # delta < -0.02, d <= -0.2
OUTCOME_HIGH_NOISE = "HIGH_VARIANCE_NOISE"       # std_dev > 0.15 regardless of mean

OUTCOME_SPACE = [
    OUTCOME_STRONG_POSITIVE,
    OUTCOME_MODERATE_POSITIVE,
    OUTCOME_NULL,
    OUTCOME_NEGATIVE,
    OUTCOME_HIGH_NOISE,
]


@dataclass(frozen=True, slots=True)
class CompetingHypothesis:
    hypothesis_id: str
    label: str  # "H_PRIMARY_MECHANISM" | "H_NULL" | "H_CONFOUNDER" | "H_MEASUREMENT_ARTIFACT" | "H_ALT_MECHANISM"
    statement: str
    mechanism: str
    prior_probability: float
    predicted_effect_mean: float  # Expected Cohen's d under this hypothesis
    predicted_effect_std: float   # Expected uncertainty in d
    predicted_outcome_distribution: dict[str, float] = field(default_factory=dict)
    falsification_condition: str = ""


@dataclass(frozen=True, slots=True)
class HypothesisTournament:
    tournament_id: str
    research_question: str
    research_gap: ResearchGap
    hypotheses: list[CompetingHypothesis]
    grounding_evidence_locators: list[str]


class CompetingHypothesisGenerator:
    """Synthesizes structured 5-hypothesis tournaments with evidence-derived alternative explanations."""

    def generate_tournament(
        self,
        research_question: str,
        research_gap: ResearchGap,
        evidence: list[ExtractedEvidence],
        prior_probabilities: dict[str, float] | None = None,
    ) -> HypothesisTournament:
        """Constructs a 5-hypothesis tournament with calibrated outcome predictions and sequential priors."""
        locators = [e.locator for e in evidence if e.locator]

        # Calculate average evidence confidence
        avg_conf = (
            sum(e.confidence for e in evidence if e.confidence) / max(1, len(evidence))
            if evidence
            else 0.80
        )
        base_priors = prior_probabilities or {
            "H-01-PRIMARY": 0.40 * avg_conf + 0.10,
            "H-02-NULL": 0.25,
            "H-03-CONFOUNDER": 0.15,
            "H-04-ARTIFACT": 0.10,
            "H-05-ALT-MECH": 0.10,
        }
        tot_prior = sum(base_priors.values()) or 1.0
        priors = {k: v / tot_prior for k, v in base_priors.items()}

        # Extract secondary candidate mechanism from literature evidence for H5
        alt_mechanism, alt_statement = self._extract_alternative_mechanism_from_evidence(evidence, research_gap)

        # 1. Primary Causal Mechanism
        h1 = CompetingHypothesis(
            hypothesis_id="H-01-PRIMARY",
            label="H_PRIMARY_MECHANISM",
            statement=(
                f"The proposed mechanism '{research_gap.proposed_direction}' produces non-trivial empirical "
                f"optimization gains by directly addressing the gap: {research_gap.gap_statement[:120]}."
            ),
            mechanism=research_gap.proposed_direction,
            prior_probability=round(priors.get("H-01-PRIMARY", 0.45), 4),
            predicted_effect_mean=round(0.70 + 0.20 * avg_conf, 3),
            predicted_effect_std=0.22,
            predicted_outcome_distribution={
                OUTCOME_STRONG_POSITIVE: 0.70,
                OUTCOME_MODERATE_POSITIVE: 0.20,
                OUTCOME_NULL: 0.05,
                OUTCOME_NEGATIVE: 0.02,
                OUTCOME_HIGH_NOISE: 0.03,
            },
            falsification_condition="Standardized paired effect size d < 0.20 or bootstrap 95% CI includes zero.",
        )

        # 2. Null Hypothesis
        h2 = CompetingHypothesis(
            hypothesis_id="H-02-NULL",
            label="H_NULL",
            statement=(
                f"The mechanism '{research_gap.proposed_direction}' has no true causal effect; observed differences "
                "are random sampling variance and stochastic mini-batch noise."
            ),
            mechanism="Stochastic sampling variance",
            prior_probability=round(priors.get("H-02-NULL", 0.25), 4),
            predicted_effect_mean=0.0,
            predicted_effect_std=0.20,
            predicted_outcome_distribution={
                OUTCOME_STRONG_POSITIVE: 0.02,
                OUTCOME_MODERATE_POSITIVE: 0.08,
                OUTCOME_NULL: 0.75,
                OUTCOME_NEGATIVE: 0.10,
                OUTCOME_HIGH_NOISE: 0.05,
            },
            falsification_condition="Statistically significant non-trivial positive effect d >= 0.40 with replication stability.",
        )

        # 3. Confounder / Capacity Hypothesis
        h3 = CompetingHypothesis(
            hypothesis_id="H-03-CONFOUNDER",
            label="H_CONFOUNDER",
            statement=(
                f"Reported gains from '{research_gap.proposed_direction}' are an artifact of effective learning rate, "
                "parameter budget scale, or implicit regularization confounders."
            ),
            mechanism="Capacity or hyperparameter tuning scale difference",
            prior_probability=round(priors.get("H-03-CONFOUNDER", 0.15), 4),
            predicted_effect_mean=0.35,
            predicted_effect_std=0.28,
            predicted_outcome_distribution={
                OUTCOME_STRONG_POSITIVE: 0.15,
                OUTCOME_MODERATE_POSITIVE: 0.55,
                OUTCOME_NULL: 0.15,
                OUTCOME_NEGATIVE: 0.05,
                OUTCOME_HIGH_NOISE: 0.10,
            },
            falsification_condition="Effect disappears when controlling for learning rate scale and parameter budget.",
        )

        # 4. Measurement / Initialization Artifact
        h4 = CompetingHypothesis(
            hypothesis_id="H-04-ARTIFACT",
            label="H_MEASUREMENT_ARTIFACT",
            statement=(
                "The observed performance difference is an artifact of initial loss surface positioning, "
                "favorable random seeds, or metric sensitivity."
            ),
            mechanism="Initialization surface bias / metric artifact",
            prior_probability=round(priors.get("H-04-ARTIFACT", 0.08), 4),
            predicted_effect_mean=0.15,
            predicted_effect_std=0.45,
            predicted_outcome_distribution={
                OUTCOME_STRONG_POSITIVE: 0.08,
                OUTCOME_MODERATE_POSITIVE: 0.22,
                OUTCOME_NULL: 0.30,
                OUTCOME_NEGATIVE: 0.15,
                OUTCOME_HIGH_NOISE: 0.25,
            },
            falsification_condition="Multi-seed replication reveals high coefficient of variation across distinct initial seeds.",
        )

        # 5. Evidence-Derived Alternative Mechanism
        h5 = CompetingHypothesis(
            hypothesis_id="H-05-ALT-MECH",
            label="H_ALT_MECHANISM",
            statement=alt_statement,
            mechanism=alt_mechanism,
            prior_probability=round(priors.get("H-05-ALT-MECH", 0.07), 4),
            predicted_effect_mean=0.55,
            predicted_effect_std=0.32,
            predicted_outcome_distribution={
                OUTCOME_STRONG_POSITIVE: 0.40,
                OUTCOME_MODERATE_POSITIVE: 0.40,
                OUTCOME_NULL: 0.10,
                OUTCOME_NEGATIVE: 0.05,
                OUTCOME_HIGH_NOISE: 0.05,
            },
            falsification_condition="Ablation of alternative mechanism isolates independent trajectory.",
        )

        tournament_id = f"TOURN-{abs(hash(research_question)) % 100000:05d}"
        return HypothesisTournament(
            tournament_id=tournament_id,
            research_question=research_question,
            research_gap=research_gap,
            hypotheses=[h1, h2, h3, h4, h5],
            grounding_evidence_locators=locators,
        )

    def _extract_alternative_mechanism_from_evidence(
        self,
        evidence: list[ExtractedEvidence],
        gap: ResearchGap,
    ) -> tuple[str, str]:
        """Extracts candidate alternative mechanisms directly from secondary evidence sentences."""
        candidate_mechanisms: list[str] = []
        for ev in evidence:
            text = ev.text or ""
            # Search for mechanism phrases: e.g. "via X", "using X", "by incorporating X", "through X"
            matches = re.findall(r"(?:via|using|by incorporating|through|based on)\s+([a-zA-Z\s\-]{4,35})", text, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if clean_m.lower() not in gap.proposed_direction.lower() and len(clean_m) > 5:
                    candidate_mechanisms.append(clean_m)

        if candidate_mechanisms:
            alt_mech = candidate_mechanisms[0]
            alt_statement = (
                f"The empirical gain is driven by secondary mechanism '{alt_mech}' "
                f"rather than the primary claimed mechanism '{gap.proposed_direction}'."
            )
            return alt_mech, alt_statement

        # Fallback evidence-grounded alternative
        alt_mech = "implicit gradient variance smoothing & representation alignment"
        alt_statement = (
            f"The empirical gain is driven by implicit optimization regularization and representation alignment "
            f"rather than the explicit mechanism of '{gap.proposed_direction}'."
        )
        return alt_mech, alt_statement
