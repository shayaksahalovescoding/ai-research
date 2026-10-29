"""Unit tests for Semantic Vector Search, PDF Full-Text Reader, and Section Extractor."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from PySide6.QtWidgets import QApplication
import pytest

from app.evidence.extractor import FullTextEvidenceExtractor
from app.literature.pdf_reader import PDFSectionExtractor
from app.literature.providers import RetrievedPaper
from app.literature.vector_store import SemanticVectorStore
from gui.widgets.literature_tab import LiteratureTab


def _ensure_qt_app() -> QApplication:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    return QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])


@pytest.fixture
def sample_paper() -> RetrievedPaper:
    return RetrievedPaper(
        external_id="PMID:3829104",
        title="Functionalized Lipid Nanoparticles for Targeted Chemotherapeutic Delivery",
        abstract=(
            "We synthesize ionizable lipid nanoparticles functionalized with receptor-specific ligands. "
            "In vitro assays show a 4.2-fold increase in targeted cancer cell uptake and reduced systemic toxicity."
        ),
        authors=["Dr. Alice Smith", "Dr. Bob Jones"],
        published_at=datetime(2023, 5, 12, tzinfo=timezone.utc),
        url="https://pubmed.ncbi.nlm.nih.gov/3829104",
        source_provider="PubMed",
    )


def test_pdf_section_extractor(sample_paper: RetrievedPaper) -> None:
    sections = PDFSectionExtractor.extract_from_paper(sample_paper)
    assert len(sections) >= 4

    types = {s.section_type for s in sections}
    assert "ABSTRACT" in types
    assert "METHODOLOGY" in types
    assert "RESULTS_TABLE" in types
    assert "FIGURE_CAPTION" in types

    meth_sec = next(s for s in sections if s.section_type == "METHODOLOGY")
    assert "microfluidic" in meth_sec.content.lower() or "methodology" in meth_sec.content.lower()


def test_semantic_vector_store_indexing_and_search(sample_paper: RetrievedPaper) -> None:
    store = SemanticVectorStore()
    sections = PDFSectionExtractor.extract_from_paper(sample_paper)

    store.index_paper_sections(
        paper_id=sample_paper.external_id,
        paper_title=sample_paper.title,
        journal=sample_paper.source_provider,
        year=2023,
        citations=34,
        sections=sections,
    )
    assert store.count() >= 4

    # Test semantic query
    results = store.search("nanoparticle targeted delivery cellular uptake", limit=5)
    assert len(results) >= 1
    assert results[0]["paper_id"] == "PMID:3829104"
    assert results[0]["similarity_score"] > 0.0

    # Test year filter
    res_2024 = store.search("nanoparticle", year_min=2024)
    assert len(res_2024) == 0  # Paper is 2023

    res_2022 = store.search("nanoparticle", year_min=2022)
    assert len(res_2022) >= 1

    # Test citation filter
    res_high_cit = store.search("nanoparticle", min_citations=50)
    assert len(res_high_cit) == 0

    res_low_cit = store.search("nanoparticle", min_citations=20)
    assert len(res_low_cit) >= 1

    # Test section type filter
    res_table = store.search("nanoparticle", section_type="RESULTS_TABLE")
    assert all(r["section_type"] == "RESULTS_TABLE" for r in res_table)


def test_evidence_extractor_with_sections(sample_paper: RetrievedPaper) -> None:
    extractor = FullTextEvidenceExtractor()
    evidence_items = extractor.extract(sample_paper)
    assert len(evidence_items) >= 3

    kinds = {ev.evidence_kind for ev in evidence_items}
    assert "EXTRACTED_ABSTRACT_TEXT" in kinds
    assert "METHODOLOGY_SNIPPET" in kinds or "EMPIRICAL_TABLE_ROW" in kinds


def test_gui_literature_tab() -> None:
    _ensure_qt_app()
    tab = LiteratureTab()
    assert tab.paper_list is not None
    assert tab.input_search is not None

    sample_papers = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "external_id": "arxiv:2401.12345",
            "title": "Optimistic Exploration in Deep Reinforcement Learning",
            "authors": ["Author One", "Author Two"],
            "abstract": "We explore tensor factorization for RL policies with optimistic value bounds.",
            "url": "https://arxiv.org/abs/2401.12345",
            "provenance": {"provider": "arXiv"},
        }
    ]

    tab.set_papers(sample_papers)
    assert tab.paper_list.count() == 1

    # Test search query in UI
    tab.input_search.setText("reinforcement learning")
    tab._on_search_clicked()

    tab._on_reset_search()
    assert tab.paper_list.count() == 1

    tab.close()
