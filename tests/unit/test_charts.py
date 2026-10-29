"""Unit tests for Embedded Interactive Scientific Charts and DAG Visualizer."""

from __future__ import annotations

import os
from PySide6.QtWidgets import QApplication

from gui.api_client import ResearchApiClient
from gui.widgets.charts.forest_chart import ForestCIChartCanvas
from gui.widgets.charts.permutation_chart import PermutationChartCanvas
from gui.widgets.charts.provenance_graph import ProvenanceDAGCanvas
from gui.widgets.experiment_tab import ExperimentTab
from gui.widgets.provenance_tab import ProvenanceTab


def _ensure_qt_app() -> QApplication:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    return QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])


def test_permutation_chart_canvas() -> None:
    _ensure_qt_app()
    chart = PermutationChartCanvas()
    assert chart.figure is not None

    # Test update with significant data (p < 0.05)
    chart.update_data(delta=0.1420, p_value=0.001, sample_count=20)
    assert len(chart.figure.axes) == 1
    ax = chart.figure.axes[0]
    assert ax.get_title() != ""
    chart.canvas.draw()

    # Test update with non-significant data (p >= 0.05)
    chart.update_data(delta=0.0120, p_value=0.150, sample_count=20)
    assert len(chart.figure.axes) == 1
    chart.canvas.draw()

    # Test reset to empty state
    chart.draw_empty_state()
    assert len(chart.figure.axes) == 1
    chart.close()


def test_forest_ci_chart_canvas() -> None:
    _ensure_qt_app()
    chart = ForestCIChartCanvas()
    assert chart.figure is not None

    # Test update with CI and effect size
    chart.update_data(ci=[0.0812, 0.2028], delta=0.1420, effect_size=1.25)
    assert len(chart.figure.axes) == 1
    ax = chart.figure.axes[0]
    assert ax.get_title() != ""

    # Test empty state
    chart.draw_empty_state()
    chart.close()


def test_provenance_dag_canvas() -> None:
    _ensure_qt_app()
    chart = ProvenanceDAGCanvas()
    assert chart.figure is not None

    knowledge_payload = {
        "nodes": [
            {"id": "paper-1", "type": "Paper"},
            {"id": "ev-1", "type": "Evidence"},
            {"id": "hypo-1", "type": "Hypothesis"},
            {"id": "exp-1", "type": "Experiment"},
            {"id": "crit-1", "type": "Critique"},
        ],
        "edges": [
            {"source": "paper-1", "target": "ev-1", "type": "EXTRACTED_FROM"},
            {"source": "ev-1", "target": "hypo-1", "type": "GROUNDED_IN"},
            {"source": "hypo-1", "target": "exp-1", "type": "TESTED_BY"},
            {"source": "exp-1", "target": "crit-1", "type": "EVALUATED_BY"},
        ],
    }

    chart.update_data(knowledge_payload)
    assert len(chart.figure.axes) == 1

    chart.draw_empty_state()
    chart.close()


def test_experiment_tab_with_charts() -> None:
    _ensure_qt_app()
    tab = ExperimentTab()
    assert tab.chart_permutation is not None
    assert tab.chart_forest is not None

    sample_result = {
        "metrics": {
            "baseline_mean_accuracy": 0.650,
            "treatment_mean_accuracy": 0.792,
        },
        "statistics": {
            "mean_difference": 0.1420,
            "effect_size": 1.25,
            "p_value": 0.001,
            "confidence_interval": [0.0812, 0.2028],
            "sample_count": 20,
        },
        "critique_outcome": "ACCEPT_WITH_LIMITATIONS",
    }

    tab.set_results(sample_result)
    assert tab.lbl_pvalue.text() != "Permutation p-value: —"
    assert tab.card_delta.findChild(object, "val_label") is not None

    # Reset
    tab.set_results(None)
    tab.close()


def test_provenance_tab_with_dag() -> None:
    _ensure_qt_app()
    client = ResearchApiClient(base_url="http://127.0.0.1:8000")
    tab = ProvenanceTab(api_client=client)
    assert tab.dag_canvas is not None

    knowledge_payload = {
        "nodes": [{"id": "node-1", "type": "Hypothesis"}],
        "edges": [],
    }
    tab.set_knowledge(knowledge_payload)
    assert tab.table.rowCount() == 1

    tab.set_knowledge(None)
    assert tab.table.rowCount() == 0
    tab.close()
