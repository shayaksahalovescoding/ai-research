"""Unit tests for PySide6 GUI client and components."""

from __future__ import annotations

from gui.api_client import ResearchApiClient
from gui.widgets.stage_tracker import STAGES


def test_api_client_url_formatting() -> None:
    client = ResearchApiClient(base_url="http://127.0.0.1:8000/")
    assert client.base_url == "http://127.0.0.1:8000"


def test_stage_definitions() -> None:
    assert len(STAGES) == 8
    stage_keys = [s[0] for s in STAGES]
    assert "RETRIEVING" in stage_keys
    assert "EXECUTING" in stage_keys
    assert "CRITIQUING" in stage_keys
    assert "COMPLETED" in stage_keys


def test_api_client_methods_exist() -> None:
    client = ResearchApiClient(base_url="http://127.0.0.1:8000")
    assert hasattr(client, "delete_project")
    assert hasattr(client, "get_experiment_results")
    assert callable(client.delete_project)
    assert callable(client.get_experiment_results)


def test_main_window_select_controls() -> None:
    import os
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    _app = QApplication.instance() or QApplication(["pytest", "-platform", "offscreen"])
    window = MainWindow(api_url="http://127.0.0.1:8000")
    assert window.btn_toggle_select is not None
    assert window.btn_delete_selected is not None
    assert window.select_mode is False

    # Test toggling select mode
    window._on_toggle_select_clicked()
    assert window.select_mode is True
    assert not window.batch_actions_box.isHidden()

    window._on_toggle_select_clicked()
    assert window.select_mode is False
    assert window.batch_actions_box.isHidden()
    window.close()


