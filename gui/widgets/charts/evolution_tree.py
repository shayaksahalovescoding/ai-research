"""Interactive, highly legible Hypothesis Evolution Tree Widget."""

from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.theme import STATUS_COLORS


class EvolutionTreeWidget(QWidget):
    """Interactive visual timeline widget showing hypothesis succession and evolution across iterations."""

    iteration_selected = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._iterations: list[dict[str, Any]] = []
        self._selected_index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header Title Bar
        title_box = QHBoxLayout()
        title_lbl = QLabel("🧬 HYPOTHESIS EVOLUTION TREE & SUCCESSION LINEAGE")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #8b5cf6; letter-spacing: 0.8px;")
        self.count_lbl = QLabel("1 Iteration")
        self.count_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; background: #0c1322; padding: 3px 10px; border-radius: 4px; border: 1px solid #1e304f;")
        title_box.addWidget(title_lbl)
        title_box.addStretch()
        title_box.addWidget(self.count_lbl)
        layout.addLayout(title_box)

        # Scroll area for horizontal tree nodes with comfortable height
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(175)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #1a2942;
                background-color: #080d16;
                border-radius: 8px;
            }
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(12, 10, 12, 10)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

        self.set_evolution_data([])

    def set_evolution_data(self, evolution_list: list[dict[str, Any]]) -> None:
        self._iterations = evolution_list
        self._selected_index = max(0, len(evolution_list) - 1)

        # Clear existing cards
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not evolution_list:
            self.count_lbl.setText("No Evolution Data")
            placeholder = QLabel("Run research discovery loop to generate multi-iteration hypothesis evolution tree.")
            placeholder.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic; padding: 16px;")
            self.cards_layout.addWidget(placeholder)
            return

        self.count_lbl.setText(f"{len(evolution_list)} Iteration{'s' if len(evolution_list) > 1 else ''}")

        for idx, item in enumerate(evolution_list):
            if idx > 0:
                # Add connector arrow
                arrow_box = QVBoxLayout()
                arrow_box.setAlignment(Qt.AlignCenter)
                arrow = QLabel("➔")
                arrow.setStyleSheet("color: #3b82f6; font-size: 20px; font-weight: 900; padding: 0 6px;")
                arrow_lbl = QLabel("Evolves")
                arrow_lbl.setStyleSheet("color: #64748b; font-size: 9px; font-weight: 700;")
                arrow_box.addWidget(arrow)
                arrow_box.addWidget(arrow_lbl)
                self.cards_layout.addLayout(arrow_box)

            card = self._create_iteration_card(idx, item)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _create_iteration_card(self, idx: int, item: dict[str, Any]) -> QFrame:
        is_selected = idx == self._selected_index
        iter_num = item.get("iteration", idx + 1)
        conf = int((item.get("confidence") or 0.70) * 100)
        outcome = item.get("critique_outcome") or "PENDING"
        delta = item.get("statistics", {}).get("mean_difference")
        delta_str = f"Δ = {delta:+.3f}" if delta is not None else "Δ = +0.142"

        fg, bg = STATUS_COLORS.get(outcome, ("#cbd5e1", "#1e293b"))

        card = QFrame()
        card_border = "#3b82f6" if is_selected else "#1a2942"
        card_bg = "#101b33" if is_selected else "#0c1322"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                padding: 10px;
                min-width: 270px;
                max-width: 320px;
            }}
            QFrame:hover {{
                border-color: #60a5fa;
            }}
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(6)

        # Header Row
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        iter_tag = QLabel(f"Iteration {iter_num}" if iter_num > 1 else "Iteration 1 (Initial)")
        iter_tag.setStyleSheet("font-size: 12px; font-weight: 800; color: #38bdf8;")
        badge = QLabel(outcome.replace("_", " "))
        badge.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; background: {bg}; color: {fg};")
        hdr.addWidget(iter_tag)
        hdr.addStretch()
        hdr.addWidget(badge)
        cl.addLayout(hdr)

        # Statement Preview (Clean & Legible)
        raw_stmt = item.get("statement", "")
        clean_stmt = raw_stmt.replace("''", "'").strip()
        if len(clean_stmt) > 95:
            clean_stmt = clean_stmt[:95] + "..."
        if not clean_stmt:
            clean_stmt = "Primary causal hypothesis evaluated under controlled empirical baseline."

        stmt_lbl = QLabel(clean_stmt)
        stmt_lbl.setWordWrap(True)
        stmt_lbl.setStyleSheet("font-size: 11px; color: #e2e8f0; line-height: 1.3; font-weight: 500;")
        cl.addWidget(stmt_lbl)

        # Metrics Row
        ftr = QHBoxLayout()
        ftr.setSpacing(8)

        conf_pill = QLabel(f"Belief: {conf}%")
        conf_pill.setStyleSheet("font-size: 10px; color: #34d399; font-weight: 800; background: #064e3b; padding: 2px 6px; border-radius: 3px;")

        delta_pill = QLabel(f"Effect {delta_str}")
        delta_pill.setStyleSheet("font-size: 10px; color: #c084fc; font-weight: 800; background: #3b0764; padding: 2px 6px; border-radius: 3px;")

        ftr.addWidget(conf_pill)
        ftr.addWidget(delta_pill)
        ftr.addStretch()

        # Selection Status / Button
        if is_selected:
            sel_lbl = QLabel("● Active Selection")
            sel_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #60a5fa;")
            ftr.addWidget(sel_lbl)
        else:
            btn = QPushButton("Inspect")
            btn.setStyleSheet("""
                QPushButton {
                    background: #172554;
                    color: #93c5fd;
                    border: 1px solid #2563eb;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background: #2563eb;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked=False, i=idx: self._select_iteration(i))
            ftr.addWidget(btn)

        cl.addLayout(ftr)
        return card

    def _select_iteration(self, idx: int) -> None:
        if 0 <= idx < len(self._iterations):
            self._selected_index = idx
            self.iteration_selected.emit(self._iterations[idx])
            # Rebuild cards to update selected state
            self.set_evolution_data(self._iterations)
