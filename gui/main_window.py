"""Scientific Research Workstation Main Window and Dialogs for Autonomous AI Research Scientist."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.api_client import HealthMonitorWorker, ResearchApiClient, WorkflowWorker
from gui.theme import DARK_STYLESHEET, STATUS_COLORS
from gui.widgets.manuscript_modal import ManuscriptModal
from gui.widgets.stage_tracker import StageTrackerWidget
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


class NewProjectDialog(QDialog):
    """Clean, focused modal dialog to define a new scientific research question."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create New Research Project")
        self.resize(500, 380)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        h_box = QVBoxLayout()
        h_box.setSpacing(3)
        title_lbl = QLabel("🔬 New Research Project")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
        subtitle_lbl = QLabel("Define your core research question to trigger autonomous multi-source literature retrieval, tournament hypotheses, and sandboxed experiment execution.")
        subtitle_lbl.setWordWrap(True)
        subtitle_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.4;")
        h_box.addWidget(title_lbl)
        h_box.addWidget(subtitle_lbl)
        layout.addLayout(h_box)

        # Project Name
        lbl_name = QLabel("PROJECT NAME")
        lbl_name.setStyleSheet("font-weight: 800; font-size: 10px; color: #cbd5e1; letter-spacing: 0.5px;")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Nanoparticle Cancer Drug Delivery")
        self.txt_name.setText("Nanoparticle Cancer Drug Delivery")
        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name)

        # Research Question
        lbl_q = QLabel("PRIMARY RESEARCH QUESTION")
        lbl_q.setStyleSheet("font-weight: 800; font-size: 10px; color: #cbd5e1; letter-spacing: 0.5px;")
        self.txt_question = QTextEdit()
        self.txt_question.setPlaceholderText("e.g. How can lipid nanoparticles improve targeted chemotherapy delivery while minimizing healthy cell toxicity?")
        self.txt_question.setText("How can lipid nanoparticles improve targeted chemotherapy delivery while minimizing healthy cell toxicity?")
        self.txt_question.setMaximumHeight(80)
        layout.addWidget(lbl_q)
        layout.addWidget(self.txt_question)

        # Objective
        lbl_obj = QLabel("OBJECTIVE (OPTIONAL)")
        lbl_obj.setStyleSheet("font-weight: 800; font-size: 10px; color: #cbd5e1; letter-spacing: 0.5px;")
        self.txt_objective = QLineEdit()
        self.txt_objective.setPlaceholderText("e.g. Investigate targeted nanomedicine for oncology therapeutics")
        self.txt_objective.setText("Investigate targeted nanomedicine for oncology therapeutics")
        layout.addWidget(lbl_obj)
        layout.addWidget(self.txt_objective)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_create = QPushButton("Create Project")
        self.btn_create.setStyleSheet("background-color: #2563eb; color: #ffffff; font-weight: 700; border: 1px solid #3b82f6; padding: 7px 20px;")
        self.btn_create.clicked.connect(self.accept)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_create)
        layout.addLayout(btn_box)

    def get_data(self) -> tuple[str, str, str]:
        return (
            self.txt_name.text().strip(),
            self.txt_question.toPlainText().strip(),
            self.txt_objective.text().strip(),
        )


class MainWindow(QMainWindow):
    """Scientific Research Workstation Main Window."""

    def __init__(self, api_url: str = "http://127.0.0.1:8000") -> None:
        super().__init__()
        self.setWindowTitle("Autonomous AI Research Scientist")
        self.resize(1340, 860)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        self.api_client = ResearchApiClient(base_url=api_url)
        self.active_project: dict[str, Any] | None = None
        self.projects_cache: list[dict[str, Any]] = []
        self.workflow_worker: WorkflowWorker | None = None
        self.select_mode: bool = False
        self._is_updating_checks: bool = False

        self._init_ui()
        self._init_health_monitor()

    def _init_ui(self) -> None:
        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ─── 1. TOP BAR ───────────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setObjectName("TopBarWidget")
        top_bar.setFixedHeight(46)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(16, 6, 16, 6)
        top_bar_layout.setSpacing(12)

        brand_lbl = QLabel("🔬 AUTONOMOUS AI RESEARCH SCIENTIST")
        brand_lbl.setStyleSheet("font-size: 13px; font-weight: 900; color: #f8fafc; letter-spacing: 0.8px;")
        top_bar_layout.addWidget(brand_lbl)

        sep = QLabel("│")
        sep.setStyleSheet("color: #1e304f; font-size: 13px;")
        top_bar_layout.addWidget(sep)

        self.lbl_top_project_name = QLabel("No Project Selected")
        self.lbl_top_project_name.setStyleSheet("font-size: 12px; font-weight: 700; color: #94a3b8;")
        top_bar_layout.addWidget(self.lbl_top_project_name)

        self.lbl_top_status_badge = QLabel("READY")
        self.lbl_top_status_badge.setStyleSheet("font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: 4px; background: #162238; color: #94a3b8;")
        top_bar_layout.addWidget(self.lbl_top_status_badge)

        top_bar_layout.addStretch()

        # Top Bar Action Controls
        self.btn_refresh = QPushButton("🔄 Sync")
        self.btn_refresh.clicked.connect(self._refresh_active_project)
        top_bar_layout.addWidget(self.btn_refresh)

        self.btn_export_paper = QPushButton("📄 Export Paper")
        self.btn_export_paper.clicked.connect(self._on_export_paper_clicked)
        self.btn_export_paper.setEnabled(False)
        top_bar_layout.addWidget(self.btn_export_paper)

        self.btn_delete_active = QPushButton("🗑️ Delete")
        self.btn_delete_active.setStyleSheet("""
            QPushButton {
                background-color: #0c1322;
                color: #f87171;
                border: 1px solid #450a0a;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #ffffff;
                border-color: #ef4444;
            }
        """)
        self.btn_delete_active.clicked.connect(self._on_delete_active_clicked)
        self.btn_delete_active.setEnabled(False)
        top_bar_layout.addWidget(self.btn_delete_active)

        self.btn_run_workflow = QPushButton("▶ Run Research Pipeline")
        self.btn_run_workflow.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 700;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #0c1322;
                color: #475569;
                border-color: #162238;
            }
        """)
        self.btn_run_workflow.clicked.connect(self._on_run_workflow_clicked)
        self.btn_run_workflow.setEnabled(False)
        top_bar_layout.addWidget(self.btn_run_workflow)

        root_layout.addWidget(top_bar)

        # ─── 2. MAIN BODY (Sidebar + Workspace Splitter) ──────────────
        main_splitter = QSplitter(Qt.Horizontal)

        # Left Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("SidebarWidget")
        sidebar.setMinimumWidth(240)
        sidebar.setMaximumWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(10)

        # Projects Section
        proj_hdr_row = QHBoxLayout()
        proj_title = QLabel("PROJECTS")
        proj_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #64748b; letter-spacing: 0.8px;")
        self.lbl_sidebar_count = QLabel("0")
        self.lbl_sidebar_count.setStyleSheet("font-size: 9px; color: #475569; font-weight: 700; background: #0c1322; padding: 1px 5px; border-radius: 3px;")
        proj_hdr_row.addWidget(proj_title)
        proj_hdr_row.addWidget(self.lbl_sidebar_count)
        proj_hdr_row.addStretch()

        self.btn_toggle_select = QPushButton("Select")
        self.btn_toggle_select.setStyleSheet("font-size: 9px; padding: 2px 6px;")
        self.btn_toggle_select.clicked.connect(self._on_toggle_select_clicked)
        proj_hdr_row.addWidget(self.btn_toggle_select)
        sidebar_layout.addLayout(proj_hdr_row)

        self.btn_new_project = QPushButton("+ New Research Project")
        self.btn_new_project.setStyleSheet("background-color: #10192c; color: #38bdf8; border: 1px solid #1e304f; font-weight: 700; font-size: 11px; padding: 6px 10px;")
        self.btn_new_project.clicked.connect(self._on_new_project_clicked)
        sidebar_layout.addWidget(self.btn_new_project)

        # Batch Selection Toolbar
        self.batch_actions_box = QFrame()
        self.batch_actions_box.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 6px; padding: 2px;")
        batch_layout = QHBoxLayout(self.batch_actions_box)
        batch_layout.setContentsMargins(2, 2, 2, 2)
        batch_layout.setSpacing(4)
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setStyleSheet("font-size: 9px; padding: 3px 6px;")
        self.btn_select_all.clicked.connect(self._on_select_all_clicked)
        self.btn_delete_selected = QPushButton("🗑️ Delete (0)")
        self.btn_delete_selected.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; font-size: 9px; padding: 3px 6px;")
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self._on_delete_selected_clicked)
        batch_layout.addWidget(self.btn_select_all)
        batch_layout.addWidget(self.btn_delete_selected)
        self.batch_actions_box.setVisible(False)
        sidebar_layout.addWidget(self.batch_actions_box)

        # Project List Widget
        self.project_list_widget = QListWidget()
        self.project_list_widget.setFixedHeight(140)
        self.project_list_widget.currentItemChanged.connect(self._on_project_selected)
        self.project_list_widget.itemClicked.connect(self._on_list_item_clicked)
        self.project_list_widget.itemChanged.connect(self._on_list_item_changed)
        self.project_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_list_widget.customContextMenuRequested.connect(self._on_project_context_menu)
        sidebar_layout.addWidget(self.project_list_widget)

        # Workspace Navigation Tree Section
        nav_title = QLabel("WORKSPACES")
        nav_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #64748b; letter-spacing: 0.8px; margin-top: 6px;")
        sidebar_layout.addWidget(nav_title)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        self.nav_buttons: dict[str, QPushButton] = {}
        workspace_items = [
            ("Overview", "📊 Overview"),
            ("Evidence", "📚 Evidence & Sources"),
            ("Hypotheses", "💡 Hypotheses & Beliefs"),
            ("Experiments", "🧪 Experiments & EIG"),
            ("Results", "📈 Results & Statistics"),
            ("Critique", "⚖️ Referee Critique"),
            ("Provenance", "🕸️ Lineage & DAG"),
            ("Timeline", "⏱️ Research Timeline"),
        ]

        for idx, (key, title) in enumerate(workspace_items):
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setProperty("workspace_key", key)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background-color: transparent;
                    color: #94a3b8;
                    border: 1px solid transparent;
                    border-radius: 5px;
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #0c1322;
                    color: #f8fafc;
                    border-color: #162238;
                }
                QPushButton:checked {
                    background-color: #121c30;
                    color: #38bdf8;
                    border: 1px solid #2563eb;
                    font-weight: 700;
                }
            """)
            btn.clicked.connect(lambda checked=False, k=key, i=idx: self._switch_workspace(k, i))
            self.nav_button_group.addButton(btn, idx)
            self.nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Server Status Bar
        server_box = QFrame()
        server_box.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 6px; padding: 4px 8px;")
        sl = QHBoxLayout(server_box)
        sl.setContentsMargins(4, 2, 4, 2)
        sl.setSpacing(6)
        self.lbl_server_dot = QLabel("●")
        self.lbl_server_dot.setStyleSheet("color: #64748b; font-size: 10px;")
        self.lbl_server_status = QLabel("Connecting...")
        self.lbl_server_status.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")
        sl.addWidget(self.lbl_server_dot)
        sl.addWidget(self.lbl_server_status)
        sl.addStretch()
        sidebar_layout.addWidget(server_box)

        main_splitter.addWidget(sidebar)

        # ─── 3. RIGHT MAIN WORKSPACE REGION ───────────────────────────
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        # Compact Project Header
        self.project_header = QFrame()
        self.project_header.setObjectName("ProjectHeaderWidget")
        self.project_header.setStyleSheet("""
            QFrame#ProjectHeaderWidget {
                background-color: #0c1322;
                border: 1px solid #1a2942;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        ph_layout = QVBoxLayout(self.project_header)
        ph_layout.setContentsMargins(12, 8, 12, 8)
        ph_layout.setSpacing(6)

        # Top line: Title & Metadata Pills
        ph_top = QHBoxLayout()
        self.lbl_header_project_name = QLabel("No Project Selected")
        self.lbl_header_project_name.setStyleSheet("font-size: 14px; font-weight: 800; color: #f8fafc;")

        self.lbl_header_status = QLabel("READY")
        self.lbl_header_status.setStyleSheet("font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; background: #162238; color: #94a3b8;")

        self.lbl_header_domain = QLabel("Domain: General AI")
        self.lbl_header_domain.setStyleSheet("font-size: 9px; font-weight: 700; color: #94a3b8; background: #080d16; padding: 2px 6px; border-radius: 4px; border: 1px solid #162238;")

        self.lbl_header_iter = QLabel("Iteration 1 / 2")
        self.lbl_header_iter.setStyleSheet("font-size: 9px; font-weight: 700; color: #38bdf8; background: #080d16; padding: 2px 6px; border-radius: 4px; border: 1px solid #162238;")

        self.lbl_header_updated = QLabel(f"Updated: {datetime.now().strftime('%H:%M')}")
        self.lbl_header_updated.setStyleSheet("font-size: 9px; color: #64748b;")

        ph_top.addWidget(self.lbl_header_project_name)
        ph_top.addWidget(self.lbl_header_status)
        ph_top.addWidget(self.lbl_header_domain)
        ph_top.addWidget(self.lbl_header_iter)
        ph_top.addStretch()
        ph_top.addWidget(self.lbl_header_updated)
        ph_layout.addLayout(ph_top)

        # Question Line
        self.lbl_header_question = QLabel("Research Question: Select a research project from the left sidebar or create a new one.")
        self.lbl_header_question.setWordWrap(True)
        self.lbl_header_question.setStyleSheet("font-size: 12px; color: #cbd5e1; font-weight: 600; line-height: 1.3;")
        ph_layout.addWidget(self.lbl_header_question)

        # Horizontal Pipeline Stepper
        self.stage_tracker = StageTrackerWidget()
        ph_layout.addWidget(self.stage_tracker)

        content_layout.addWidget(self.project_header)

        # Workspace Stack
        self.workspace_stack = QStackedWidget()

        self.workspace_overview = OverviewWorkspace()
        self.workspace_overview.run_research_requested.connect(self._on_run_workflow_clicked)
        self.workspace_overview.navigate_to_workspace.connect(self._switch_workspace_by_key)

        self.workspace_evidence = EvidenceWorkspace()
        self.workspace_hypotheses = HypothesisWorkspace()
        self.workspace_experiments = ExperimentWorkspace()
        self.workspace_results = ResultsWorkspace()
        self.workspace_critique = CritiqueWorkspace()
        self.workspace_provenance = ProvenanceWorkspace(self.api_client)
        self.workspace_timeline = TimelineWorkspace()

        self.workspace_stack.addWidget(self.workspace_overview)
        self.workspace_stack.addWidget(self.workspace_evidence)
        self.workspace_stack.addWidget(self.workspace_hypotheses)
        self.workspace_stack.addWidget(self.workspace_experiments)
        self.workspace_stack.addWidget(self.workspace_results)
        self.workspace_stack.addWidget(self.workspace_critique)
        self.workspace_stack.addWidget(self.workspace_provenance)
        self.workspace_stack.addWidget(self.workspace_timeline)

        content_layout.addWidget(self.workspace_stack)

        main_splitter.addWidget(content_container)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)

        root_layout.addWidget(main_splitter)
        self.setCentralWidget(root_widget)

        # Default select Overview
        self.nav_buttons["Overview"].setChecked(True)

    # ─── Backward Compatibility Properties for Unit Tests ─────────────
    @property
    def tab_literature(self) -> EvidenceWorkspace:
        return self.workspace_evidence

    @property
    def tab_hypotheses(self) -> HypothesisWorkspace:
        return self.workspace_hypotheses

    @property
    def tab_experiment(self) -> ResultsWorkspace:
        return self.workspace_results

    @property
    def tab_provenance(self) -> ProvenanceWorkspace:
        return self.workspace_provenance

    # ─── Health Monitor ───────────────────────────────────────────────
    def _init_health_monitor(self) -> None:
        self.health_worker = HealthMonitorWorker(self.api_client, self)
        self.health_worker.status_updated.connect(self._on_server_status_update)
        self.health_worker.start()

    def _on_server_status_update(self, online: bool, status_text: str) -> None:
        if online:
            self.lbl_server_dot.setStyleSheet("color: #10b981; font-size: 11px;")
            self.lbl_server_status.setText(f"Backend {status_text} (8000)")
        else:
            self.lbl_server_dot.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.lbl_server_status.setText(f"Backend {status_text}")

    # ─── Navigation Switcher ──────────────────────────────────────────
    def _switch_workspace(self, key: str, index: int) -> None:
        self.workspace_stack.setCurrentIndex(index)
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)

    def _switch_workspace_by_key(self, key: str) -> None:
        keys_order = ["Overview", "Evidence", "Hypotheses", "Experiments", "Results", "Critique", "Provenance", "Timeline"]
        if key in keys_order:
            idx = keys_order.index(key)
            self._switch_workspace(key, idx)

    # ─── Project Selection & Creation ─────────────────────────────────
    def _on_new_project_clicked(self) -> None:
        dlg = NewProjectDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, q, obj = dlg.get_data()
            if not name or not q:
                QMessageBox.warning(self, "Validation Error", "Name and research question are required.")
                return
            try:
                res = self.api_client.create_project(name, q, obj)
                self.add_project(res)
            except Exception as e:
                QMessageBox.critical(self, "Creation Failed", f"Failed to create project:\n{e}")

    def _on_project_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if not current:
            return
        proj = current.data(Qt.UserRole)
        if not proj:
            return
        self.active_project = proj
        self._update_header(proj)
        self._refresh_active_project()

    def _update_header(self, proj: dict[str, Any]) -> None:
        name = proj.get("name", "Project")
        q = proj.get("research_question", "")
        status = proj.get("status", "CREATED")

        self.lbl_top_project_name.setText(name)
        self.lbl_header_project_name.setText(name)
        self.lbl_header_question.setText(f"Research Question: \"{q}\"")

        domain = "Nanomedicine" if "nano" in q.lower() or "lipid" in q.lower() else (
            "Machine Learning" if "learning" in q.lower() or "model" in q.lower() else "General Science"
        )
        self.lbl_header_domain.setText(f"Domain: {domain}")

        fg, bg = STATUS_COLORS.get(status, ("#cbd5e1", "#334155"))
        self.lbl_top_status_badge.setText(status)
        self.lbl_top_status_badge.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: 4px; background: {bg}; color: {fg};")
        self.lbl_header_status.setText(status)
        self.lbl_header_status.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; background: {bg}; color: {fg};")

        self.btn_run_workflow.setEnabled(status in {"CREATED", "FAILED", "COMPLETED"})
        self.btn_delete_active.setEnabled(True)
        self.btn_export_paper.setEnabled(True)

    def _refresh_active_project(self) -> None:
        if not self.active_project:
            return
        pid = str(self.active_project.get("id"))

        # 1. Fetch updated status
        status_info = {}
        try:
            status_info = self.api_client.get_project_status(pid)
            st = status_info.get("status", "CREATED")
            self.active_project["status"] = st
            fg, bg = STATUS_COLORS.get(st, ("#cbd5e1", "#334155"))
            self.lbl_top_status_badge.setText(st)
            self.lbl_top_status_badge.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: 4px; background: {bg}; color: {fg};")
            self.lbl_header_status.setText(st)
            self.lbl_header_status.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; background: {bg}; color: {fg};")
            if st == "COMPLETED":
                self.stage_tracker.update_stage("COMPLETED", "COMPLETED")
        except Exception:
            pass

        # 2. Fetch literature
        papers = []
        paper_details: dict[str, dict[str, Any]] = {}
        try:
            papers = self.api_client.list_papers(pid)
            for p in papers:
                p_id = str(p.get("id"))
                try:
                    detail = self.api_client.get_paper(p_id)
                    paper_details[p_id] = detail
                except Exception:
                    paper_details[p_id] = p
            self.workspace_evidence.set_papers(papers, paper_details)
        except Exception:
            self.workspace_evidence.set_papers([])

        # 3. Fetch hypotheses & evolution
        hypotheses = []
        evo_list = []
        try:
            evolution_payload = self.api_client.get_evolution(pid)
            evo_list = evolution_payload.get("evolution_tree", [])
            hypotheses = self.api_client.list_hypotheses(pid)
        except Exception:
            try:
                hypotheses = self.api_client.list_hypotheses(pid)
            except Exception:
                hypotheses = []

        # 4. Fetch knowledge graph & provenance
        knowledge = None
        try:
            knowledge = self.api_client.get_knowledge(pid)
            self.workspace_provenance.set_knowledge(knowledge)
        except Exception:
            self.workspace_provenance.set_knowledge(None)

        # 5. Fetch experiment results and specification
        res_data = None
        exp_obj = None
        gen_code = None
        if self.active_project.get("status") == "COMPLETED" or True:
            try:
                if knowledge:
                    exp_node = next((n for n in knowledge.get("nodes", []) if n.get("type") == "Experiment"), None)
                    if exp_node:
                        exp_id = exp_node["id"]
                        res_data = self.api_client.get_experiment_results(exp_id)
                        exp_obj = self.api_client.get_experiment(exp_id)
                        gen_code = (exp_obj.get("specification") or {}).get("generated_code")
            except Exception:
                pass

        self.workspace_hypotheses.set_hypotheses(hypotheses, evolution_data=evo_list, result_payload=res_data)
        self.workspace_experiments.set_experiment(exp_obj, generated_code=gen_code)
        self.workspace_results.set_results(res_data)
        if res_data:
            critique_outcome = res_data.get("critique_outcome", "ACCEPT_WITH_LIMITATIONS")
            self.workspace_critique.set_critique(critique_outcome)
        else:
            self.workspace_critique.set_critique(None)

        self.workspace_timeline.set_timeline_data(self.active_project)
        self.workspace_overview.update_overview(self.active_project, hypotheses=hypotheses, result_payload=res_data, experiment_obj=exp_obj)

    # ─── Workflow Execution ───────────────────────────────────────────
    def _on_run_workflow_clicked(self) -> None:
        if not self.active_project:
            return
        pid = str(self.active_project.get("id"))

        self.btn_run_workflow.setEnabled(False)
        self.btn_run_workflow.setText("⏳ Running...")
        self.stage_tracker.reset()
        self.stage_tracker.update_stage("RETRIEVING", "RUNNING")

        if hasattr(self, "_simulate_timer") and self._simulate_timer.isActive():
            self._simulate_timer.stop()

        self._simulate_timer = QTimer(self)
        self._sim_stages = ["EXTRACTING", "HYPOTHESIZING", "PLANNING_EXPERIMENT", "EXECUTING", "ANALYZING", "CRITIQUING"]
        self._sim_idx = 0

        def next_stage_anim():
            if self._sim_idx < len(self._sim_stages):
                self.stage_tracker.update_stage(self._sim_stages[self._sim_idx], "RUNNING")
                self._sim_idx += 1

        self._simulate_timer.timeout.connect(next_stage_anim)
        self._simulate_timer.start(1200)

        self.workflow_worker = WorkflowWorker(self.api_client, pid, self)
        self.workflow_worker.completed_signal.connect(self._on_workflow_completed)
        self.workflow_worker.failed_signal.connect(self._on_workflow_failed)
        self.workflow_worker.start()

    def _on_workflow_completed(self, result: dict[str, Any]) -> None:
        if hasattr(self, "_simulate_timer"):
            self._simulate_timer.stop()
        self.stage_tracker.update_stage("COMPLETED", "COMPLETED")
        self.btn_run_workflow.setEnabled(True)
        self.btn_run_workflow.setText("▶ Run Research Pipeline")
        self._refresh_active_project()
        QMessageBox.information(
            self,
            "Research Pipeline Completed",
            "Multi-source scientific research pipeline completed successfully!\nAll literature evidence, hypotheses tournament, EIG experiment results, and referee critiques are updated.",
        )

    def _on_workflow_failed(self, error_msg: str) -> None:
        if hasattr(self, "_simulate_timer"):
            self._simulate_timer.stop()
        self.stage_tracker.update_stage("FAILED", "FAILED")
        self.btn_run_workflow.setEnabled(True)
        self.btn_run_workflow.setText("▶ Run Research Pipeline")
        self._refresh_active_project()
        QMessageBox.critical(self, "Workflow Failed", error_msg)

    # ─── Export Paper ─────────────────────────────────────────────────
    def _on_export_paper_clicked(self) -> None:
        if not self.active_project:
            return
        pid = str(self.active_project.get("id"))
        try:
            manuscript_data = self.api_client.get_manuscript(pid)
            modal = ManuscriptModal(manuscript_data, parent=self)
            modal.exec()
        except Exception as e:
            QMessageBox.critical(self, "Export Paper Error", f"Could not compile academic manuscript:\n{e}")

    # ─── Project Deletion & Select Management ─────────────────────────
    def _on_toggle_select_clicked(self) -> None:
        self.select_mode = not self.select_mode
        self.batch_actions_box.setVisible(self.select_mode)
        if self.select_mode:
            self.btn_toggle_select.setText("Done")
            self.btn_toggle_select.setStyleSheet("background-color: #2563eb; color: #ffffff; font-size: 9px; font-weight: 700; padding: 2px 6px;")
        else:
            self.btn_toggle_select.setText("Select")
            self.btn_toggle_select.setStyleSheet("font-size: 9px; padding: 2px 6px;")
        self._apply_select_mode_to_items()
        self._update_delete_button_state()

    def _apply_select_mode_to_items(self) -> None:
        self._is_updating_checks = True
        try:
            for i in range(self.project_list_widget.count()):
                item = self.project_list_widget.item(i)
                if self.select_mode:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    if item.checkState() != Qt.Checked:
                        item.setCheckState(Qt.Unchecked)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                    item.setData(Qt.CheckStateRole, None)
        finally:
            self._is_updating_checks = False

    def _on_list_item_clicked(self, item: QListWidgetItem) -> None:
        if self.select_mode:
            current_state = item.checkState()
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            self._is_updating_checks = True
            try:
                item.setCheckState(new_state)
            finally:
                self._is_updating_checks = False
            self._update_delete_button_state()

    def _on_list_item_changed(self, item: QListWidgetItem) -> None:
        if self._is_updating_checks or not self.select_mode:
            return
        self._update_delete_button_state()

    def _update_delete_button_state(self) -> None:
        if not self.select_mode:
            return
        checked_count = sum(
            1 for i in range(self.project_list_widget.count()) if self.project_list_widget.item(i).checkState() == Qt.Checked
        )
        total_count = self.project_list_widget.count()
        self.btn_delete_selected.setText(f"🗑️ Delete ({checked_count})")
        self.btn_delete_selected.setEnabled(checked_count > 0)
        if total_count > 0 and checked_count == total_count:
            self.btn_select_all.setText("Deselect All")
        else:
            self.btn_select_all.setText("Select All")

    def _on_select_all_clicked(self) -> None:
        total = self.project_list_widget.count()
        if total == 0:
            return
        checked_count = sum(1 for i in range(total) if self.project_list_widget.item(i).checkState() == Qt.Checked)
        target_state = Qt.Unchecked if checked_count == total else Qt.Checked
        self._is_updating_checks = True
        try:
            for i in range(total):
                self.project_list_widget.item(i).setCheckState(target_state)
        finally:
            self._is_updating_checks = False
        self._update_delete_button_state()

    def _on_delete_selected_clicked(self) -> None:
        checked_items = [
            self.project_list_widget.item(i)
            for i in range(self.project_list_widget.count())
            if self.project_list_widget.item(i).checkState() == Qt.Checked
        ]
        if not checked_items:
            return

        projects_to_delete = [item.data(Qt.UserRole) for item in checked_items if item.data(Qt.UserRole)]
        count = len(projects_to_delete)
        if count == 0:
            return

        names_preview = "\n".join(f"• {p.get('name', 'Untitled')}" for p in projects_to_delete[:4])
        if count > 4:
            names_preview += f"\n... and {count - 4} more"

        confirm = QMessageBox.question(
            self,
            "Confirm Project Deletion",
            f"Are you sure you want to permanently delete {count} research project(s)?\n\n{names_preview}\n\nThis will remove all associated literature, evidence, hypotheses, and sandbox runs.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        active_id = str(self.active_project.get("id")) if self.active_project else None
        deleted_active = False

        for p in projects_to_delete:
            pid = str(p.get("id"))
            if pid == active_id:
                deleted_active = True
            try:
                self.api_client.delete_project(pid)
            except Exception:
                try:
                    from uuid import UUID
                    from app.core.config import Settings
                    from app.storage.database import create_database_engine, create_session_factory, delete_project_cascade
                    settings = Settings()
                    engine = create_database_engine(settings.database_url)
                    factory = create_session_factory(engine)
                    with factory() as session:
                        delete_project_cascade(session, UUID(pid))
                        session.commit()
                except Exception as e:
                    print(f"[GUI] Delete error for {pid}: {e}")

        self.select_mode = False
        self.batch_actions_box.setVisible(False)
        self.btn_toggle_select.setText("Select")
        if deleted_active:
            self.active_project = None

        self.reload_projects_list()
        if not self.active_project or self.project_list_widget.count() == 0:
            self._reset_dashboard_to_empty()

    def _on_delete_active_clicked(self) -> None:
        if not self.active_project:
            return
        name = self.active_project.get("name", "Project")
        pid = str(self.active_project.get("id"))

        confirm = QMessageBox.question(
            self,
            "Delete Research Project",
            f"Are you sure you want to permanently delete \"{name}\"?\n\nAll literature, hypotheses, experiment runs, and referee critiques will be removed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.api_client.delete_project(pid)
        except Exception:
            try:
                from uuid import UUID
                from app.core.config import Settings
                from app.storage.database import create_database_engine, create_session_factory, delete_project_cascade
                settings = Settings()
                engine = create_database_engine(settings.database_url)
                factory = create_session_factory(engine)
                with factory() as session:
                    delete_project_cascade(session, UUID(pid))
                    session.commit()
            except Exception as e:
                QMessageBox.critical(self, "Deletion Error", f"Failed to delete project:\n{e}")
                return

        self.active_project = None
        self.reload_projects_list()
        if not self.active_project or self.project_list_widget.count() == 0:
            self._reset_dashboard_to_empty()

    def _on_project_context_menu(self, pos) -> None:
        item = self.project_list_widget.itemAt(pos)
        if not item:
            return
        proj = item.data(Qt.UserRole)
        if not proj:
            return
        menu = QMenu(self)
        action_delete = menu.addAction(f"🗑️ Delete \"{proj.get('name', 'Project')}\"")
        action = menu.exec(self.project_list_widget.mapToGlobal(pos))
        if action == action_delete:
            self.active_project = proj
            self._on_delete_active_clicked()

    def _reset_dashboard_to_empty(self) -> None:
        self.active_project = None
        self.lbl_top_project_name.setText("No Project Selected")
        self.lbl_header_project_name.setText("No Project Selected")
        self.lbl_header_question.setText("Research Question: Select a research project from the left sidebar or create a new one.")
        self.lbl_top_status_badge.setText("READY")
        self.lbl_header_status.setText("READY")
        self.btn_run_workflow.setEnabled(False)
        self.btn_delete_active.setEnabled(False)
        self.btn_export_paper.setEnabled(False)
        self.stage_tracker.reset()
        self.workspace_overview.update_overview(None)
        self.workspace_evidence.set_papers([])
        self.workspace_hypotheses.set_hypotheses([])
        self.workspace_experiments.set_experiment(None)
        self.workspace_results.set_results(None)
        self.workspace_critique.set_critique(None)
        self.workspace_provenance.set_knowledge(None)
        self.workspace_timeline.set_timeline_data(None)

    def reload_projects_list(self) -> None:
        projects = []
        try:
            projects = self.api_client.list_projects()
        except Exception:
            try:
                from sqlalchemy import select
                from app.core.config import Settings
                from app.storage.database import create_database_engine, create_session_factory
                from app.storage.models import ResearchProject, ResearchQuestion
                settings = Settings()
                engine = create_database_engine(settings.database_url)
                factory = create_session_factory(engine)
                with factory() as session:
                    db_projects = session.scalars(select(ResearchProject).order_by(ResearchProject.created_at.desc())).all()
                    for p in db_projects:
                        q = session.scalar(select(ResearchQuestion).where(ResearchQuestion.project_id == p.id))
                        projects.append({
                            "id": str(p.id),
                            "name": p.name,
                            "status": p.status,
                            "research_question": q.text if q else "",
                            "objective": p.objective,
                            "created_at": p.created_at.isoformat() if p.created_at else None,
                        })
            except Exception:
                projects = []

        current_id = self.active_project.get("id") if self.active_project else None
        self.project_list_widget.clear()
        self.projects_cache = projects
        self.lbl_sidebar_count.setText(str(len(projects)))
        selected_item = None
        for p in projects:
            status = p.get("status", "CREATED")
            name = p.get("name", "Project")
            status_icon = "🟢" if status == "COMPLETED" else ("⏳" if status == "RUNNING" else ("🔴" if status == "FAILED" else "🔵"))
            item = QListWidgetItem(f"{name}\n{status_icon} {status}")
            item.setData(Qt.UserRole, p)
            if self.select_mode:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
            self.project_list_widget.addItem(item)
            if current_id and str(p.get("id")) == str(current_id):
                selected_item = item
        if selected_item:
            self.project_list_widget.setCurrentItem(selected_item)
        elif self.project_list_widget.count() > 0 and not self.active_project:
            self.project_list_widget.setCurrentRow(0)
        elif self.project_list_widget.count() == 0:
            self._reset_dashboard_to_empty()

    def add_project(self, project: dict[str, Any]) -> None:
        self.projects_cache.append(project)
        self.lbl_sidebar_count.setText(str(len(self.projects_cache)))
        status = project.get("status", "CREATED")
        name = project.get("name", "Project")
        status_icon = "🟢" if status == "COMPLETED" else ("⏳" if status == "RUNNING" else ("🔴" if status == "FAILED" else "🔵"))
        item = QListWidgetItem(f"{name}\n{status_icon} {status}")
        item.setData(Qt.UserRole, project)
        if self.select_mode:
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
        self.project_list_widget.addItem(item)
        self.project_list_widget.setCurrentItem(item)

    def closeEvent(self, event) -> None:
        if hasattr(self, "health_worker"):
            self.health_worker.stop()
        event.accept()
