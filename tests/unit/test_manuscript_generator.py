"""Unit tests for Academic Manuscript & Report Exporter."""

from __future__ import annotations

from pathlib import Path
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.reporting.manuscript_generator import generate_manuscript
from app.storage.models import (
    Base,
    Critique,
    Evidence,
    Experiment,
    ExperimentRun,
    Hypothesis,
    Metric,
    Paper,
    ResearchProject,
    ResearchQuestion,
    Result,
    Source,
)
from gui.api_client import ResearchApiClient
from gui.widgets.manuscript_modal import ManuscriptModal


def _create_sample_project(session: Session) -> ResearchProject:
    proj = ResearchProject(name="Nanoparticle Cancer Drug Delivery", status="COMPLETED", objective="Targeted delivery")
    session.add(proj)
    session.flush()

    q = ResearchQuestion(project_id=proj.id, text="How can lipid nanoparticles improve targeted chemotherapy?")
    session.add(q)

    src = Source(project_id=proj.id, name="PubMed", source_type="api", uri="https://eutils.ncbi.nlm.nih.gov")
    session.add(src)
    session.flush()

    paper = Paper(
        project_id=proj.id,
        source_id=src.id,
        external_id="PMID:12345678",
        title="Lipid Nanoparticles in Oncology",
        abstract="Lipid nanoparticles exhibit high encapsulation efficiency and reduced systemic toxicity.",
        authors=["Alice Smith", "Bob Jones"],
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
    )
    session.add(paper)
    session.flush()

    ev = Evidence(
        project_id=proj.id,
        paper_id=paper.id,
        evidence_kind="QUOTE",
        text="Encapsulation significantly reduces off-target cytotoxicity.",
        locator="p.3, para.2",
        confidence=0.92,
    )
    session.add(ev)

    hyp = Hypothesis(
        project_id=proj.id,
        statement="Lipid encapsulation increases localized drug concentration while reducing toxicity.",
        mechanism="Selective permeation and retention in tumor microenvironments.",
        assumptions=["Nanocarrier stability holds in vivo"],
        predictions=["Statistically significant decrease in off-target toxicity"],
        confidence=0.88,
        novelty_estimate="high_novelty",
        testability_score=0.95,
        estimated_cost="medium",
    )
    session.add(hyp)
    session.flush()

    exp = Experiment(
        project_id=proj.id,
        hypothesis_id=hyp.id,
        template_id="toy_logistic_regression_v1",
        template_revision="1.0",
        kind="SIMULATION",
        specification={"iterations": 400},
    )
    session.add(exp)
    session.flush()

    run = ExperimentRun(
        project_id=proj.id,
        experiment_id=exp.id,
        status="COMPLETED",
        random_seed=42,
    )
    session.add(run)
    session.flush()

    m1 = Metric(run_id=run.id, name="baseline_mean_accuracy", value=0.650, sample_count=20)
    m2 = Metric(run_id=run.id, name="treatment_mean_accuracy", value=0.792, sample_count=400)
    session.add_all([m1, m2])

    res = Result(
        run_id=run.id,
        summary="Treatment significantly outperformed baseline.",
        statistics={
            "mean_difference": 0.1420,
            "effect_size": 1.25,
            "p_value": 0.001,
            "confidence_interval": [0.0812, 0.2028],
            "sample_count": 20,
        },
    )
    session.add(res)

    crit = Critique(
        project_id=proj.id,
        hypothesis_id=hyp.id,
        run_id=run.id,
        outcome="ACCEPT_WITH_LIMITATIONS",
        findings=[{"severity": "INFO", "code": "POSITIVE_INTERVAL", "message": "Bootstrap CI excludes zero."}],
    )
    session.add(crit)
    session.commit()
    return proj


def test_generate_manuscript_markdown_latex_html() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        proj = _create_sample_project(session)
        payload = generate_manuscript(session, proj.id)

        assert payload["title"] == "Autonomous Investigation: Nanoparticle Cancer Drug Delivery"
        assert payload["citation_count"] == 1
        assert "Lipid encapsulation increases localized drug concentration" in payload["abstract"]

        # Markdown checks
        md = payload["markdown"]
        assert "# Autonomous Investigation: Nanoparticle Cancer Drug Delivery" in md
        assert "## Abstract" in md
        assert "## 1. Introduction & Background" in md
        assert "## 2. Hypothesis Formulation & Causal Mechanism" in md
        assert "## 3. Experimental Methodology & Sandbox Protocol" in md
        assert "## 4. Empirical Results & Statistical Inference" in md
        assert "## 5. Scientific Referee Review & Limitations" in md
        assert "## 7. References" in md
        assert "Lipid Nanoparticles in Oncology" in md

        # LaTeX checks
        tex = payload["latex"]
        assert r"\documentclass[11pt,a4paper]{article}" in tex
        assert r"\begin{document}" in tex
        assert r"\begin{abstract}" in tex
        assert r"\section{Introduction \& Research Objective}" in tex
        assert r"\section{Evidence-Grounded Hypothesis Formulation}" in tex
        assert r"\section{Empirical Results \& Statistical Inference}" in tex
        assert r"\begin{thebibliography}" in tex
        assert r"\end{document}" in tex

        # HTML checks
        html_doc = payload["html"]
        assert "<!DOCTYPE html>" in html_doc
        assert "Autonomous Investigation: Nanoparticle Cancer Drug Delivery" in html_doc
        assert "0.1420" in html_doc
        assert "Alice Smith, Bob Jones" in html_doc


def test_gui_manuscript_modal_and_pdf_export() -> None:
    import os
    from PySide6.QtGui import QPageSize, QPdfWriter
    from PySide6.QtWidgets import QApplication

    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    _app = QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])

    sample_payload = {
        "title": "Test Paper",
        "abstract": "This is a test abstract.",
        "created_date": "August 21, 2026",
        "citation_count": 2,
        "markdown": "# Test Paper\n\nAbstract text.",
        "latex": r"\documentclass{article}\begin{document}Hello\end{document}",
        "html": "<html><body><h1>Test Paper</h1><p>Body</p></body></html>",
    }

    modal = ManuscriptModal(sample_payload)
    assert modal.tabs.count() == 3
    assert modal.browser_html.toPlainText() != ""
    assert modal.txt_markdown.toPlainText() == "# Test Paper\n\nAbstract text."
    assert "documentclass" in modal.txt_latex.toPlainText()

    # Test PDF Generation to temporary file
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "test_paper.pdf"
        doc = modal.browser_html.document()
        writer = QPdfWriter(str(pdf_path))
        writer.setPageSize(QPageSize(QPageSize.A4))
        doc.print_(writer)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    modal.close()


def test_api_client_has_get_manuscript() -> None:
    client = ResearchApiClient(base_url="http://127.0.0.1:8000")
    assert hasattr(client, "get_manuscript")
    assert callable(client.get_manuscript)
