"""Compact, scientific research pipeline stepper widget: ✓ Literature → ✓ Evidence → ● Hypothesis → ○ Complete."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)

STAGES = [
    ("RETRIEVING", "Literature"),
    ("EXTRACTING", "Evidence"),
    ("HYPOTHESIZING", "Hypothesis"),
    ("PLANNING_EXPERIMENT", "Plan"),
    ("EXECUTING", "Sandbox"),
    ("ANALYZING", "Statistics"),
    ("CRITIQUING", "Critique"),
    ("COMPLETED", "Complete"),
]

STAGE_ORDER = [s[0] for s in STAGES]


class CompactStageNode(QFrame):
    """Compact individual step indicator in the scientific pipeline."""

    def __init__(self, key: str, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self.title = title

        self.setFixedHeight(26)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel("○")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 10px; font-weight: 700; color: #475569;")

        self.lbl_name = QLabel(self.title)
        self.lbl_name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.lbl_name.setStyleSheet("font-weight: 600; font-size: 10px; color: #64748b;")

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_name)

        self.set_state("PENDING")

    def set_state(self, state: str) -> None:
        """States: PENDING (subdued), ACTIVE (emphasized), COMPLETED (quiet), FAILED (error)"""
        if state == "COMPLETED":
            self.setStyleSheet("""
                CompactStageNode {
                    background-color: #062f22;
                    border: 1px solid #059669;
                    border-radius: 4px;
                }
            """)
            self.lbl_icon.setText("✓")
            self.lbl_icon.setStyleSheet("color: #34d399; font-size: 10px; font-weight: 800;")
            self.lbl_name.setStyleSheet("font-weight: 700; font-size: 10px; color: #a7f3d0;")
        elif state == "ACTIVE":
            self.setStyleSheet("""
                CompactStageNode {
                    background-color: #172554;
                    border: 1px solid #3b82f6;
                    border-radius: 4px;
                }
            """)
            self.lbl_icon.setText("●")
            self.lbl_icon.setStyleSheet("color: #60a5fa; font-size: 10px; font-weight: 800;")
            self.lbl_name.setStyleSheet("font-weight: 800; font-size: 10px; color: #93c5fd;")
        elif state == "FAILED":
            self.setStyleSheet("""
                CompactStageNode {
                    background-color: #450a0a;
                    border: 1px solid #dc2626;
                    border-radius: 4px;
                }
            """)
            self.lbl_icon.setText("✕")
            self.lbl_icon.setStyleSheet("color: #f87171; font-size: 10px; font-weight: 800;")
            self.lbl_name.setStyleSheet("font-weight: 700; font-size: 10px; color: #fca5a5;")
        else:  # PENDING
            self.setStyleSheet("""
                CompactStageNode {
                    background-color: #080d16;
                    border: 1px solid #141f33;
                    border-radius: 4px;
                }
            """)
            self.lbl_icon.setText("○")
            self.lbl_icon.setStyleSheet("color: #475569; font-size: 10px; font-weight: 700;")
            self.lbl_name.setStyleSheet("font-weight: 600; font-size: 10px; color: #475569;")


class StageTrackerWidget(QFrame):
    """Compact horizontal workflow pipeline stepper with connected step nodes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StageTrackerWidget")
        self.setStyleSheet("""
            QFrame#StageTrackerWidget {
                background-color: #080d16;
                border: 1px solid #162238;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(3)

        self.step_widgets: dict[str, CompactStageNode] = {}

        for i, (key, title) in enumerate(STAGES):
            step = CompactStageNode(key, title, self)
            self.step_widgets[key] = step
            layout.addWidget(step)

            if i < len(STAGES) - 1:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setStyleSheet("color: #1e304f; font-size: 10px; font-weight: 700; margin: 0px 1px;")
                layout.addWidget(arrow)

    def update_stage(self, current_stage: str, status: str = "RUNNING") -> None:
        if status == "FAILED":
            for key, widget in self.step_widgets.items():
                if key == current_stage:
                    widget.set_state("FAILED")
                elif key in STAGE_ORDER and current_stage in STAGE_ORDER and STAGE_ORDER.index(key) < STAGE_ORDER.index(current_stage):
                    widget.set_state("COMPLETED")
                else:
                    widget.set_state("PENDING")
            return

        if current_stage == "COMPLETED" or status == "COMPLETED":
            for widget in self.step_widgets.values():
                widget.set_state("COMPLETED")
            return

        if current_stage not in STAGE_ORDER:
            for widget in self.step_widgets.values():
                widget.set_state("PENDING")
            return

        current_idx = STAGE_ORDER.index(current_stage)
        for idx, (_key, widget) in enumerate(self.step_widgets.items()):
            if idx < current_idx:
                widget.set_state("COMPLETED")
            elif idx == current_idx:
                widget.set_state("ACTIVE")
            else:
                widget.set_state("PENDING")

    def reset(self) -> None:
        for widget in self.step_widgets.values():
            widget.set_state("PENDING")
