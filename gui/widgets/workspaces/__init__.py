"""Workstation workspaces module for Autonomous AI Research Scientist."""

from __future__ import annotations

from .critique_workspace import CritiqueWorkspace
from .evidence_workspace import EvidenceWorkspace
from .experiment_workspace import ExperimentWorkspace
from .hypothesis_workspace import HypothesisWorkspace
from .overview_workspace import OverviewWorkspace
from .provenance_workspace import ProvenanceWorkspace
from .results_workspace import ResultsWorkspace
from .timeline_workspace import TimelineWorkspace

__all__ = [
    "CritiqueWorkspace",
    "EvidenceWorkspace",
    "ExperimentWorkspace",
    "HypothesisWorkspace",
    "OverviewWorkspace",
    "ProvenanceWorkspace",
    "ResultsWorkspace",
    "TimelineWorkspace",
]
