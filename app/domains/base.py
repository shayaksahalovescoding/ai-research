"""Domain Experiment Adapter Abstract Base Interface.

Decouples the domain-agnostic scientific reasoning core (literature, evidence,
gap discovery, hypotheses tournaments, EIG decision engine, referee, provenance)
from domain-specific simulation and experiment execution runtimes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.reasoning.competing_hypotheses import HypothesisTournament


class DomainExperimentAdapter(ABC):
    """Abstract interface for domain-specific simulation and experimental execution."""

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Name of the scientific domain (e.g. 'MACHINE_LEARNING', 'BIOMEDICAL', 'PHYSICS')."""
        ...

    @abstractmethod
    def generate_experiment_script(
        self,
        hypothesis_statement: str,
        mechanism: str = "",
        trial_count: int = 12,
        random_seed: int = 1729,
    ) -> str:
        """Synthesizes a self-contained, AST-verified Python simulation script."""
        ...

    @abstractmethod
    def suggest_candidate_designs(
        self,
        tournament: HypothesisTournament,
    ) -> list[dict[str, Any]]:
        """Proposes candidate experiment designs tailored to discriminate competing hypotheses in this domain."""
        ...
