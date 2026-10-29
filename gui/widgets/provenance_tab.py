"""Ultra-modern Provenance & Lineage Audit Explorer Tab with Interactive DAG Canvas."""

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


class ProvenanceTab(QWidget):
    def __init__(self, api_client: ResearchApiClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.nodes_data: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Section
        header_box = QHBoxLayout()
        header_left = QVBoxLayout()
        header_left.setSpacing(2)
        header_lbl = QLabel("🕸️ Audit Lineage & Interactive Provenance DAG")
        header_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
        sub_lbl = QLabel(
            "Visual Directed Acyclic Graph (DAG) and cryptographic provenance chains connecting papers, evidence, hypotheses, and sandbox runs."
        )
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        header_left.addWidget(header_lbl)
        header_left.addWidget(sub_lbl)
        header_box.addLayout(header_left)
        header_box.addStretch()
        layout.addLayout(header_box)

        # Main Vertical Splitter: Top Graph, Bottom Inspector Table
        vert_splitter = QSplitter(Qt.Vertical)

        # Top: Interactive DAG Canvas
        graph_card = QFrame()
        graph_card.setStyleSheet("""
            QFrame {
                background-color: #0b111e;
                border: 1px solid #172033;
                border-radius: 10px;
                padding: 6px;
            }
        """)
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(6, 6, 6, 6)
        self.dag_canvas = ProvenanceDAGCanvas()
        graph_layout.addWidget(self.dag_canvas)
        vert_splitter.addWidget(graph_card)

        # Bottom Horizontal Splitter: Table + JSON Inspector
        bottom_splitter = QSplitter(Qt.Horizontal)

        # Left Column: Lineage Table
        left_container = QFrame()
        left_container.setStyleSheet("background: #0a0f1d; border: 1px solid #172033; border-radius: 10px; padding: 6px;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)

        table_title = QLabel("AUDIT NODES & LINEAGE LINKS")
        table_title.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 10px; letter-spacing: 0.5px;")
        left_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Entity Type", "Relationship", "Record ID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_item_selected)

        left_layout.addWidget(self.table)
        bottom_splitter.addWidget(left_container)

        # Right Column: JSON Inspector
        right_container = QFrame()
        right_container.setStyleSheet("background: #0a0f1d; border: 1px solid #172033; border-radius: 10px; padding: 6px;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        inspector_title = QLabel("PROVENANCE PAYLOAD INSPECTOR (JSON)")
        inspector_title.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 10px; letter-spacing: 0.5px;")
        right_layout.addWidget(inspector_title)

        self.json_viewer = QTextBrowser()
        self.json_viewer.setStyleSheet("""
            QTextBrowser {
                background-color: #080d16;
                border: 1px solid #172033;
                border-radius: 8px;
                color: #38bdf8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        self.json_viewer.setText("// Select any record from the lineage table to inspect its raw cryptographic provenance.")
        right_layout.addWidget(self.json_viewer)

        bottom_splitter.addWidget(right_container)
        bottom_splitter.setStretchFactor(0, 3)
        bottom_splitter.setStretchFactor(1, 2)

        vert_splitter.addWidget(bottom_splitter)
        vert_splitter.setStretchFactor(0, 3)
        vert_splitter.setStretchFactor(1, 2)

        layout.addWidget(vert_splitter)

    def set_knowledge(self, knowledge_payload: dict[str, Any] | None) -> None:
        self.table.setRowCount(0)
        self.json_viewer.setText("// Select any record from the lineage table to inspect its raw cryptographic provenance.")
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
            self.json_viewer.setText(f"// Error loading provenance for {record_id}:\n// {e}")
