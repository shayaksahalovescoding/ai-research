from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureCode(StrEnum):
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    PAPER_PARSE_FAILED = "PAPER_PARSE_FAILED"
    EVIDENCE_EXTRACTION_FAILED = "EVIDENCE_EXTRACTION_FAILED"
    HYPOTHESIS_GENERATION_FAILED = "HYPOTHESIS_GENERATION_FAILED"
    EXPERIMENT_GENERATION_FAILED = "EXPERIMENT_GENERATION_FAILED"
    SANDBOX_FAILED = "SANDBOX_FAILED"
    SANDBOX_UNAVAILABLE = "BLOCKED_SANDBOX_UNAVAILABLE"
    STATISTICS_FAILED = "STATISTICS_FAILED"
    CRITIC_FAILED = "CRITIC_FAILED"
    ILL_POSED_QUESTION = "ILL_POSED_QUESTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_STATE = "INVALID_STATE"


@dataclass(slots=True)
class ResearchWorkflowError(Exception):
    code: FailureCode
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

