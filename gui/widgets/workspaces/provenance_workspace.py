"""Provenance Workspace: Cryptographic Lineage DAG Network, Entity Table & Node Inspector."""

from __future__ import annotations

import json
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.api_client import ResearchApiClient
from gui.widgets.charts.provenance_graph import ProvenanceDAGCanvas


class ProvenanceWorkspace(QWidget):
    """Answers 'Where did every conclusion come from?' with interactive DAG and verifiable provenance chains."""

    def __init__(self, api_client: ResearchApiClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.nodes_data: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Section
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 8px; padding: 10px;")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(10, 8, 10, 8)
        h_layout.setSpacing(4)

        top_line = QHBoxLayout()
        title = QLabel("VERIFIABLE CRYPTOGRAPHIC PROVENANCE & LINEAGE DAG")
        title.setStyleSheet("font-size: 10px; font-weight: 800; color: #3b82f6; letter-spacing: 0.5px;")
        badge = QLabel("CRYPTOGRAPHICALLY AUDITABLE")
        badge.setStyleSheet("font-size: 9px; font-weight: 700; color: #34d399; background: #064e3b; padding: 2px 8px; border-radius: 4px;")
        top_line.addWidget(title)
        top_line.addStretch()
        top_line.addWidget(badge)
        h_layout.addLayout(top_line)

        sub = QLabel("Explore the complete provenance chain linking papers, evidence anchors, hypotheses, experiment runs, and referee critiques.")
        sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        h_layout.addWidget(sub)
        layout.addWidget(header_card)

        # Vertical Splitter: Top DAG Visualizer, Bottom Split (Entity Table + JSON Inspector)
        vert_splitter = QSplitter(Qt.Vertical)

        # Top: Interactive DAG Canvas
        graph_card = QFrame()
        graph_card.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 8px; padding: 6px;")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(6, 6, 6, 6)
        self.dag_canvas = ProvenanceDAGCanvas()
        graph_layout.addWidget(self.dag_canvas)
        vert_splitter.addWidget(graph_card)

        # Bottom Splitter: Table + JSON Drawer
        bottom_splitter = QSplitter(Qt.Horizontal)

        # Left Column: Table
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 8px; padding: 8px;")
        tl = QVBoxLayout(table_container)
        tl.setContentsMargins(6, 6, 6, 6)
        tl.setSpacing(6)

        t_title = QLabel("AUDIT ENTITIES & LINEAGE RELATIONS")
        t_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #cbd5e1; letter-spacing: 0.5px;")
        tl.addWidget(t_title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Entity Type", "Relation", "Record ID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_item_selected)
        tl.addWidget(self.table)
        bottom_splitter.addWidget(table_container)

        # Right Column: Inspector Drawer
        inspector_container = QFrame()
        inspector_container.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 8px; padding: 8px;")
        il = QVBoxLayout(inspector_container)
        il.setContentsMargins(6, 6, 6, 6)
        il.setSpacing(6)

        i_title = QLabel("CRYPTOGRAPHIC PROVENANCE PAYLOAD")
        i_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #cbd5e1; letter-spacing: 0.5px;")
        il.addWidget(i_title)

        self.json_viewer = QTextBrowser()
        self.json_viewer.setStyleSheet("""
            QTextBrowser {
                background-color: #080d16;
                border: 1px solid #162238;
                border-radius: 6px;
                color: #38bdf8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        self.json_viewer.setText("// Select any record from the table to inspect its raw cryptographic hash and parent linkage.")
        il.addWidget(self.json_viewer)
        bottom_splitter.addWidget(inspector_container)

        bottom_splitter.setStretchFactor(0, 3)
        bottom_splitter.setStretchFactor(1, 2)
        vert_splitter.addWidget(bottom_splitter)

        vert_splitter.setStretchFactor(0, 3)
        vert_splitter.setStretchFactor(1, 2)
        layout.addWidget(vert_splitter)

    def set_knowledge(self, knowledge_payload: dict[str, Any] | None) -> None:
        self.table.setRowCount(0)
        self.json_viewer.setText("// Select any record from the table to inspect its raw cryptographic hash and parent linkage.")
        self.dag_canvas.update_data(knowledge_payload)

        if not knowledge_payload:
            return

        nodes = knowledge_payload.get("nodes", [])
        edges = knowledge_payload.get("edges", [])

        edge_map: dict[str, str] = {}
        for e in edges:
            tgt = e.get("target")
            rel = e.get("type", "LINKED")
            if tgt:
                edge_map[tgt] = rel

        self.table.setRowCount(len(nodes))
        for row, node in enumerate(nodes):
            nid = node.get("id", "")
            ntype = node.get("type", "Entity")
            rel = edge_map.get(nid, "ROOT")

            item_type = QTableWidgetItem(f"🏷️ {ntype}")
            item_rel = QTableWidgetItem(rel)
            item_id = QTableWidgetItem(nid)

            item_type.setData(Qt.UserRole, nid)
            self.table.setItem(row, 0, item_type)
            self.table.setItem(row, 1, item_rel)
            self.table.setItem(row, 2, item_id)

    def _on_item_selected(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        record_id = selected_items[0].data(Qt.UserRole)
        if not record_id:
            record_id = selected_items[2].text()

        try:
            prov = self.api_client.get_provenance(record_id)
            formatted = json.dumps(prov, indent=2)
            self.json_viewer.setText(formatted)
        except Exception as e:
            self.json_viewer.setText(f"// Record: {record_id}\n// Provenance: Auditable record active\n// {e}")
