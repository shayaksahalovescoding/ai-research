"""Multi-Section and Full-Text Evidence Extractor for Scientific Papers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.literature.pdf_reader import PDFSectionExtractor
from app.literature.providers import RetrievedPaper
from app.literature.vector_store import global_vector_store


@dataclass(frozen=True, slots=True)
class ExtractedEvidence:
    text: str
    locator: str
    evidence_kind: str = "EXTRACTED_ABSTRACT_TEXT"
    confidence: float = 1.0


class AbstractEvidenceExtractor:
    """Extracts quoted abstract sentences without interpreting them as facts."""

    def extract(self, paper: Any) -> list[ExtractedEvidence]:
        if hasattr(paper, "title") and paper.title:
            sections = PDFSectionExtractor.extract_from_paper(paper)
            year = getattr(paper, "published_at", None)
            year_val = year.year if year else 2024
            global_vector_store.index_paper_sections(
                paper_id=getattr(paper, "external_id", "unknown"),
                paper_title=paper.title,
                journal=getattr(paper, "source_provider", "arXiv"),
                year=year_val,
                citations=18,
                sections=sections,
            )

        if not hasattr(paper, "abstract") or not paper.abstract:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", paper.abstract.strip())
        selected = [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 30][:2]
        return [
            ExtractedEvidence(
                text=sentence,
                locator=f"abstract:sentence:{index + 1}",
                evidence_kind="EXTRACTED_ABSTRACT_TEXT",
                confidence=1.0,
            )
            for index, sentence in enumerate(selected)
        ]


class FullTextEvidenceExtractor:
    """Extracts multi-section evidence across abstract, methodology, and benchmark tables."""

    def extract(self, paper: RetrievedPaper) -> list[ExtractedEvidence]:
        evidence_items: list[ExtractedEvidence] = []
        sections = PDFSectionExtractor.extract_from_paper(paper)

        for sec in sections:
            if sec.section_type == "ABSTRACT":
                sentences = re.split(r"(?<=[.!?])\s+", sec.content.strip())
                for index, s in enumerate(sentences[:2]):
                    if len(s.strip()) >= 30:
                        evidence_items.append(
                            ExtractedEvidence(text=s.strip(), locator=f"abstract:sentence:{index + 1}", evidence_kind="EXTRACTED_ABSTRACT_TEXT")
                        )
            elif sec.section_type == "METHODOLOGY":
                evidence_items.append(
                    ExtractedEvidence(text=sec.content[:280] + "...", locator=sec.locator, evidence_kind="METHODOLOGY_SNIPPET", confidence=0.95)
                )
            elif sec.section_type == "RESULTS_TABLE":
                evidence_items.append(
                    ExtractedEvidence(text=sec.content[:280] + "...", locator=sec.locator, evidence_kind="EMPIRICAL_TABLE_ROW", confidence=0.98)
                )
        return evidence_items
