"""Expected Information Gain (EIG) Decision Engine & Continuous Bayesian Updater.

Formulates experimental design selection as optimal Bayesian experiment design (OBED):
1. Model-Derived Outcome Distributions P(y | H_i, e_j) via Gaussian CDF Binning
2. Exact Shannon Entropy & Expected Posterior Entropy:
   EIG(e_j) = H(H) - E_y [ H(H | y, e_j) ]
3. Cost-normalized Information Utility:
   Utility(e_j) = EIG(e_j) / Cost(e_j)
4. Continuous Gaussian Predictive Likelihood Bayesian Updating:
   P(H_i | Data) ∝ P(H_i) * N(d_hat; mu_i, sigma_i^2 + SE^2)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.reasoning.competing_hypotheses import (
    OUTCOME_HIGH_NOISE,
    OUTCOME_MODERATE_POSITIVE,
    OUTCOME_NEGATIVE,
    OUTCOME_NULL,
    OUTCOME_SPACE,
    OUTCOME_STRONG_POSITIVE,
    CompetingHypothesis,
    HypothesisTournament,
)
from app.statistics.service import StatisticalSummary


@dataclass(frozen=True, slots=True)
class CandidateExperimentDesign:
    design_id: str
    name: str
    description: str
    design_type: str  # "STANDARD" | "ABLATION" | "STRESS_PERTURBATION"
    target_hypothesis_id: str
    trial_count: int
    estimated_compute_seconds: float
    cost_flops_normalized: float
    expected_information_gain: float  # In bits (Shannon entropy reduction)
    cost_efficiency_utility: float    # EIG / Cost
    outcome_entropy_bits: float = 0.0
    design_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PosteriorBeliefState:
    posterior_probabilities: dict[str, float]  # hypothesis_id -> P(H_i | Data)
    entropy_prior_bits: float
    entropy_posterior_bits: float
    information_gain_bits: float
    leading_hypothesis_id: str
    confidence: float  # Posterior of leading hypothesis
    bayes_factors: dict[str, float]  # hypothesis_id -> BF vs H_NULL


class ResearchDecisionEngine:
    """Calculates exact Shannon EIG with model-derived likelihoods and continuous Gaussian Bayesian updates."""

    @staticmethod
    def compute_entropy(probabilities: list[float]) -> float:
        """Computes Shannon entropy in bits H(X) = -sum(p * log2(p))."""
        entropy = 0.0
        for p in probabilities:
            if p > 1e-12:
                entropy -= p * math.log2(p)
        return max(0.0, entropy)

    @staticmethod
    def _gaussian_cdf(x: float, mean: float, std: float) -> float:
        """Standard Gaussian normal cumulative distribution function Φ((x - μ) / σ)."""
        if std <= 1e-9:
            return 1.0 if x >= mean else 0.0
        z = (x - mean) / (std * math.sqrt(2.0))
        return 0.5 * (1.0 + math.erf(z))

    def compute_model_derived_distribution(
        self,
        hypothesis: CompetingHypothesis,
        design_type: str,
        design_parameters: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        """Calculates outcome probabilities P(y | H_i, e_j) by transforming μ, σ and integrating Gaussian CDF."""
        mu = hypothesis.predicted_effect_mean
        sigma = max(0.05, hypothesis.predicted_effect_std)
        label = hypothesis.label

        # Apply design sensitivity transforms
        if design_type == "ABLATION":
            # Ablation controls capacity/learning rate:
            if label == "H_CONFOUNDER":
                mu_eff = mu * 0.05  # Confounder collapses to null
                sigma_eff = sigma * 0.6
            elif label == "H_PRIMARY_MECHANISM":
                mu_eff = mu * 0.95  # Primary mechanism resists ablation
                sigma_eff = sigma * 0.9
            elif label == "H_NULL":
                mu_eff = 0.0
                sigma_eff = sigma * 0.6
            elif label == "H_ALT_MECHANISM":
                mu_eff = mu * 0.65
                sigma_eff = sigma * 0.9
            else:
                mu_eff = mu * 0.40
                sigma_eff = sigma * 1.1

        elif design_type == "STRESS_PERTURBATION":
            # Multi-seed stress test amplifies noise:
            if label == "H_MEASUREMENT_ARTIFACT":
                mu_eff = mu * 0.15
                sigma_eff = sigma * 2.8  # Artifact degrades into high variance noise
            elif label == "H_PRIMARY_MECHANISM":
                mu_eff = mu * 0.85  # Primary mechanism is robust
                sigma_eff = sigma * 1.1
            elif label == "H_NULL":
                mu_eff = 0.0
                sigma_eff = sigma * 1.2
            elif label == "H_CONFOUNDER":
                mu_eff = mu * 0.70
                sigma_eff = sigma * 1.3
            else:
                mu_eff = mu * 0.75
                sigma_eff = sigma * 1.2

        else:
            # Standard Trial: unperturbed expectations
            mu_eff = mu
            sigma_eff = sigma

        # Integrate normal distribution CDF over delta thresholds:
        # Thresholds: Strong Pos >= 0.12, Mod Pos [0.04, 0.12), Null [-0.02, 0.04), Neg < -0.02
        # Scale Cohen's d to delta space (delta ≈ d * 0.15 for typical baseline standard deviation)
        mu_delta = mu_eff * 0.15
        sigma_delta = sigma_eff * 0.15

        p_strong = max(0.01, 1.0 - self._gaussian_cdf(0.12, mu_delta, sigma_delta))
        p_mod = max(0.01, self._gaussian_cdf(0.12, mu_delta, sigma_delta) - self._gaussian_cdf(0.04, mu_delta, sigma_delta))
        p_null = max(0.01, self._gaussian_cdf(0.04, mu_delta, sigma_delta) - self._gaussian_cdf(-0.02, mu_delta, sigma_delta))
        p_neg = max(0.01, self._gaussian_cdf(-0.02, mu_delta, sigma_delta))

        # Check high variance noise risk
        if sigma_eff >= 0.35:
            p_noise = min(0.60, sigma_eff * 0.8)
            # Re-scale other outcome probabilities
            scale = 1.0 - p_noise
            p_strong *= scale
            p_mod *= scale
            p_null *= scale
            p_neg *= scale
        else:
            p_noise = 0.02

        # Normalize to exact sum of 1.0
        tot = p_strong + p_mod + p_null + p_neg + p_noise
        return {
            OUTCOME_STRONG_POSITIVE: round(p_strong / tot, 4),
            OUTCOME_MODERATE_POSITIVE: round(p_mod / tot, 4),
            OUTCOME_NULL: round(p_null / tot, 4),
            OUTCOME_NEGATIVE: round(p_neg / tot, 4),
            OUTCOME_HIGH_NOISE: round(p_noise / tot, 4),
        }

    def evaluate_and_select_experiment(
        self,
        tournament: HypothesisTournament,
        custom_candidate_designs: list[dict[str, Any]] | None = None,
    ) -> tuple[CandidateExperimentDesign, list[CandidateExperimentDesign]]:
        """Evaluates candidate experiment designs using model-derived EIG and selects optimal utility."""
        priors = {h.hypothesis_id: h.prior_probability for h in tournament.hypotheses}
        prior_probs = list(priors.values())
        prior_entropy = self.compute_entropy(prior_probs)

        candidates: list[CandidateExperimentDesign] = []
        raw_candidates = custom_candidate_designs or self._generate_default_candidate_designs(tournament)

        for raw in raw_candidates:
            design_id = str(raw.get("design_id", "EXP-01"))
            design_type = str(raw.get("design_type", "STANDARD"))
            design_params = dict(raw.get("design_parameters", {}))

            # 1. Compute model-derived outcome distribution P(y | H_i, e_j) for each hypothesis
            design_likelihood_matrix: dict[str, dict[str, float]] = {}
            for h in tournament.hypotheses:
                design_likelihood_matrix[h.hypothesis_id] = self.compute_model_derived_distribution(
                    h, design_type, design_params
                )

            # 2. Compute marginal outcome distribution P(y | e_j) = sum_i P(y | H_i, e_j) * P(H_i)
            p_outcome: dict[str, float] = {y: 0.0 for y in OUTCOME_SPACE}
            for h in tournament.hypotheses:
                h_dist = design_likelihood_matrix[h.hypothesis_id]
                for y in OUTCOME_SPACE:
                    p_outcome[y] += h_dist.get(y, 0.20) * h.prior_probability

            tot_p_y = sum(p_outcome.values()) or 1.0
            p_outcome = {y: p_outcome[y] / tot_p_y for y in OUTCOME_SPACE}

            # 3. Compute expected posterior entropy E_y[ H(H | y, e_j) ]
            expected_posterior_entropy = 0.0
            for y in OUTCOME_SPACE:
                p_y = p_outcome[y]
                if p_y <= 1e-12:
                    continue

                # Compute posterior P(H_i | y, e_j) = (P(y | H_i, e_j) * P(H_i)) / P(y | e_j)
                posteriors_for_y: list[float] = []
                for h in tournament.hypotheses:
                    h_dist = design_likelihood_matrix[h.hypothesis_id]
                    p_y_given_h = h_dist.get(y, 0.20)
                    post_h = (p_y_given_h * h.prior_probability) / p_y
                    posteriors_for_y.append(post_h)

                h_entropy_given_y = self.compute_entropy(posteriors_for_y)
                expected_posterior_entropy += p_y * h_entropy_given_y

            # 4. True Model-Derived EIG = Prior Entropy - Expected Posterior Entropy
            eig = max(0.001, prior_entropy - expected_posterior_entropy)
            cost = max(0.1, float(raw.get("cost_flops", 1.0)))
            utility = eig / cost

            candidate = CandidateExperimentDesign(
                design_id=design_id,
                name=str(raw.get("name", "Standard Trial")),
                description=str(raw.get("description", "")),
                design_type=design_type,
                target_hypothesis_id=str(raw.get("target_hypothesis_id", tournament.hypotheses[0].hypothesis_id)),
                trial_count=int(raw.get("trial_count", 12)),
                estimated_compute_seconds=float(raw.get("compute_seconds", 2.0)),
                cost_flops_normalized=cost,
                expected_information_gain=round(eig, 4),
                cost_efficiency_utility=round(utility, 4),
                outcome_entropy_bits=round(expected_posterior_entropy, 4),
                design_parameters=design_params,
            )
            candidates.append(candidate)

        # Select candidate with highest cost-efficiency utility
        best_design = max(candidates, key=lambda c: c.cost_efficiency_utility)
        return best_design, candidates

    def update_beliefs(
        self,
        tournament: HypothesisTournament,
        statistics: StatisticalSummary,
    ) -> PosteriorBeliefState:
        """Applies exact continuous Gaussian predictive likelihood Bayesian updating."""
        prior_probs = [h.prior_probability for h in tournament.hypotheses]
        prior_entropy = self.compute_entropy(prior_probs)

        observed_d = float(statistics.effect_size)
        n = statistics.sample_count or 10
        # Standard error of Cohen's d: SE = sqrt((1/N) + (d^2 / 2N))
        se_d = math.sqrt(max(0.01, (1.0 / n) + (observed_d**2 / (2.0 * n))))

        # Continuous Gaussian density likelihood L(H_i | d_hat)
        unnormalized_posteriors: dict[str, float] = {}
        likelihoods: dict[str, float] = {}

        for h in tournament.hypotheses:
            mu = h.predicted_effect_mean
            sigma = h.predicted_effect_std
            total_var = (sigma**2) + (se_d**2)
            diff = observed_d - mu
            exponent = -(diff**2) / (2.0 * total_var)
            likelihood = (1.0 / math.sqrt(2.0 * math.pi * total_var)) * math.exp(max(-50.0, exponent))
            likelihoods[h.hypothesis_id] = likelihood
            unnormalized_posteriors[h.hypothesis_id] = h.prior_probability * likelihood

        total_mass = sum(unnormalized_posteriors.values()) or 1.0
        posteriors = {hid: val / total_mass for hid, val in unnormalized_posteriors.items()}

        # Compute Bayes Factors relative to H_NULL
        null_likelihood = likelihoods.get("H-02-NULL", 1e-6) or 1e-6
        bayes_factors = {
            hid: round(likelihoods[hid] / null_likelihood, 4)
            for hid in likelihoods
        }

        post_entropy = self.compute_entropy(list(posteriors.values()))
        info_gain = max(0.0, prior_entropy - post_entropy)

        leading_id = max(posteriors.keys(), key=lambda hid: posteriors[hid])
        confidence = round(posteriors[leading_id], 4)

        return PosteriorBeliefState(
            posterior_probabilities={hid: round(p, 4) for hid, p in posteriors.items()},
            entropy_prior_bits=round(prior_entropy, 4),
            entropy_posterior_bits=round(post_entropy, 4),
            information_gain_bits=round(info_gain, 4),
            leading_hypothesis_id=leading_id,
            confidence=confidence,
            bayes_factors=bayes_factors,
        )

    @staticmethod
    def _generate_default_candidate_designs(tournament: HypothesisTournament) -> list[dict[str, Any]]:
        return [
            {
                "design_id": "EXP-DES-01-STANDARD",
                "name": "Standard Paired Empirical Trial",
                "description": "Evaluates baseline vs proposed mechanism across standard 12 trials.",
                "design_type": "STANDARD",
                "target_hypothesis_id": tournament.hypotheses[0].hypothesis_id,
                "trial_count": 12,
                "compute_seconds": 2.0,
                "cost_flops": 1.0,
                "design_parameters": {"controlled_capacity": False, "perturbation_noise_scale": 1.0},
            },
            {
                "design_id": "EXP-DES-02-ABLATION",
                "name": "Controlled Capacity & Confounder Isolation Ablation",
                "description": "Fixes learning rate scaling and parameter budget to discriminate primary causal mechanism from capacity confounders.",
                "design_type": "ABLATION",
                "target_hypothesis_id": tournament.hypotheses[2].hypothesis_id if len(tournament.hypotheses) > 2 else "H-02-NULL",
                "trial_count": 8,
                "compute_seconds": 1.4,
                "cost_flops": 0.7,
                "design_parameters": {"controlled_capacity": True, "freeze_learning_rate": True, "perturbation_noise_scale": 1.0},
            },
            {
                "design_id": "EXP-DES-03-STRESS-REP",
                "name": "Multi-Seed Noise Robustness Perturbation Test",
                "description": "High-powered 16 trial benchmark across randomized surface positions to discriminate causal mechanism from initialization artifacts.",
                "design_type": "STRESS_PERTURBATION",
                "target_hypothesis_id": tournament.hypotheses[0].hypothesis_id,
                "trial_count": 16,
                "compute_seconds": 3.6,
                "cost_flops": 1.5,
                "design_parameters": {"controlled_capacity": False, "perturbation_noise_scale": 1.6, "randomized_surface_shifts": True},
            },
        ]
