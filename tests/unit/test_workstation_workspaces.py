"""Unit tests for the redesigned Scientific Research Workstation and 8 Dedicated Workspaces."""

import os
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.widgets.workspaces import (
    CritiqueWorkspace,
    EvidenceWorkspace,
    ExperimentWorkspace,
    HypothesisWorkspace,
    OverviewWorkspace,
    ProvenanceWorkspace,
    ResultsWorkspace,
    TimelineWorkspace,
)
from run_gui import preload_projects


def _ensure_qt_app() -> QApplication:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    return QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])


def test_workstation_initialization_and_switching() -> None:
    _ensure_qt_app()
    win = MainWindow(api_url="http://127.0.0.1:8000")
    preload_projects(win)

    assert win.project_list_widget.count() >= 1
    assert win.active_project is not None

    workspaces = ["Overview", "Evidence", "Hypotheses", "Experiments", "Results", "Critique", "Provenance", "Timeline"]
    for idx, ws in enumerate(workspaces):
        win._switch_workspace_by_key(ws)
        assert win.workspace_stack.currentIndex() == idx

    win.close()


def test_overview_workspace_update() -> None:
    _ensure_qt_app()
    ow = OverviewWorkspace()
    sample_project = {
        "id": "proj-1",
        "name": "Nanoparticle Cancer Drug Delivery",
        "research_question": "How can lipid nanoparticles improve targeted chemotherapy delivery while minimizing toxicity?",
        "status": "COMPLETED",
        "provenance": {"completed_iterations": 1, "max_iterations": 2, "reproducibility_score": 1.0},
    }
    sample_result = {
        "statistics": {"effect_size": 0.73, "p_value": 0.008, "sample_count": 12, "mean_difference": 0.142},
        "provenance": {
            "posterior_probabilities": {"H-01-PRIMARY": 0.71, "H-02-NULL": 0.12, "H-03-CONFOUNDER": 0.09, "H-04-ARTIFACT": 0.05, "H-05-ALT-MECH": 0.03},
            "information_gain_bits": 0.82,
        },
    }
    ow.update_overview(sample_project, result_payload=sample_result)
    assert "Nanoparticle" in ow.lbl_question_text.text() or "chemotherapy" in ow.lbl_question_text.text()
    assert "0.82" in ow.lbl_info_gain.text()
    ow.close()


def test_evidence_workspace_filtering() -> None:
    _ensure_qt_app()
    ew = EvidenceWorkspace()
    papers = [
        {"id": "p1", "external_id": "PMID:3829101", "title": "Nanoparticle Drug Delivery", "authors": ["Dr. Smith"], "abstract": "Study on lipid nanoparticles."},
        {"id": "p2", "external_id": "arxiv:2401.0001", "title": "Foundation Models for Drug Discovery", "authors": ["Dr. Doe"], "abstract": "Deep learning paper."},
    ]
    ew.set_papers(papers)
    assert ew.paper_list.count() == 2

    ew.input_search.setText("lipid")
    ew._on_search_clicked()
    ew._on_reset_search()
    assert ew.paper_list.count() == 2
    ew.close()


def test_hypothesis_workspace_selection() -> None:
    _ensure_qt_app()
    hw = HypothesisWorkspace()
    hw.set_hypotheses([
        {"statement": "Primary delivery mechanism improves targeted uptake", "mechanism": "Ligand-receptor selective affinity", "confidence": 0.75}
    ])
    assert "0.82" in hw.lbl_info_gain_bits.text()
    assert hw._selected_hyp_id is not None
    hw.close()


def test_results_and_critique_workspaces() -> None:
    _ensure_qt_app()
    rw = ResultsWorkspace()
    sample_result = {
        "statistics": {"effect_size": 1.25, "p_value": 0.008, "sample_count": 12, "mean_difference": 0.142, "confidence_interval": [0.081, 0.203]},
        "metrics": {"baseline_mean_accuracy": 0.650, "treatment_mean_accuracy": 0.792},
        "provenance": {"run_id": "RUN-01", "reproducibility_score": 1.0},
    }
    rw.set_results(sample_result)
    assert rw.chart_permutation is not None
    assert rw.chart_forest is not None
    rw.close()

    cw = CritiqueWorkspace()
    cw.set_critique("ACCEPT_WITH_LIMITATIONS", [{"severity": "INFO", "code": "VALID", "message": "All verified"}])
    assert "ACCEPT WITH LIMITATIONS" in cw.lbl_verdict_badge.text()
    cw.close()
