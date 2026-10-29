"""Critique Workspace: Scientific Referee Report, Rigor Audits & Structured Findings."""

from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.theme import STATUS_COLORS


class RefereeCategoryCard(QFrame):
    """Structured Referee Category Card with status badge (PASS / WARNING / FAIL)."""

    def __init__(self, category_name: str, status: str, explanation: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0c1322;
                border: 1px solid #162238;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #1e304f;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        self.lbl_title = QLabel(category_name)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #cbd5e1; letter-spacing: 0.5px;")

        self.lbl_badge = QLabel(status)
        self.set_status(status)

        hdr.addWidget(self.lbl_title)
        hdr.addStretch()
        hdr.addWidget(self.lbl_badge)
        layout.addLayout(hdr)

        self.lbl_explanation = QLabel(explanation)
        self.lbl_explanation.setWordWrap(True)
        self.lbl_explanation.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.4;")
        layout.addWidget(self.lbl_explanation)

    def set_status(self, status: str) -> None:
        fg, bg = STATUS_COLORS.get(status, ("#94a3b8", "#1e293b"))
        icon = "✓ " if status == "PASS" else ("⚠ " if status == "WARNING" else ("✕ " if status == "FAIL" else "? "))
        self.lbl_badge.setText(f"{icon}{status}")
        self.lbl_badge.setStyleSheet(f"font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; background: {bg}; color: {fg};")

    def set_explanation(self, text: str) -> None:
        self.lbl_explanation.setText(text)


class CritiqueWorkspace(QWidget):
    """Answers 'How trustworthy is the result?' from an expert scientific peer-reviewer perspective."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Overall Referee Verdict Banner
        self.verdict_card = QFrame()
        self.verdict_card.setStyleSheet("""
            QFrame {
                background-color: #0c1322;
                border: 1px solid #1a2942;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        v_layout = QVBoxLayout(self.verdict_card)
        v_layout.setContentsMargins(12, 10, 12, 10)
        v_layout.setSpacing(6)

        top_line = QHBoxLayout()
        v_tag = QLabel("PEER-REVIEW REFEREE REPORT & EPISTEMIC AUDIT")
        v_tag.setStyleSheet("font-size: 10px; font-weight: 800; color: #3b82f6; letter-spacing: 0.5px;")
        self.lbl_verdict_badge = QLabel("ACCEPT WITH LIMITATIONS")
        self.lbl_verdict_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #34d399; background: #064e3b; padding: 3px 10px; border-radius: 4px;")
        top_line.addWidget(v_tag)
        top_line.addStretch()
        top_line.addWidget(self.lbl_verdict_badge)
        v_layout.addLayout(top_line)

        self.lbl_summary = QLabel(
            "Overall Referee Assessment: The experimental design rigorously controls baseline comparisons and demonstrates statistically significant positive effect (d = 0.73, p = 0.008). Multi-seed replication (3/3 seeds) confirms directional stability. Minor limitations noted regarding sample scale and capacity confounder bounds."
        )
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet("font-size: 11px; color: #cbd5e1; line-height: 1.5;")
        v_layout.addWidget(self.lbl_summary)

        layout.addWidget(self.verdict_card)

        # 2. Structured 6-Category Referee Assessment Grid
        cat_header = QLabel("CATEGORIZED SCIENTIFIC AUDITS")
        cat_header.setStyleSheet("font-size: 10px; font-weight: 800; color: #cbd5e1; letter-spacing: 0.5px; margin-top: 4px;")
        layout.addWidget(cat_header)

        # Grid rows
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.card_power = RefereeCategoryCard(
            "STATISTICAL POWER & EFFECT SIZE",
            "WARNING",
            "Observed effect size is large (d = 0.73), but sample size (N = 12) provides moderate statistical power. Recommend higher-power trial for final confirmatory manuscript."
        )
        self.card_repro = RefereeCategoryCard(
            "REPRODUCIBILITY & MULTI-SEED STABILITY",
            "PASS",
            "3/3 independent random seeds demonstrated consistent positive effect direction with low coefficient of variation across initializations."
        )
        row1.addWidget(self.card_power)
        row1.addWidget(self.card_repro)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.card_confounding = RefereeCategoryCard(
            "CONFOUNDING & CAPACITY ISOLATION",
            "WARNING",
            "Ablation isolated learning rate scaling; however, subtle parameter budget scaling differences require further isolation."
        )
        self.card_validity = RefereeCategoryCard(
            "INTERNAL VALIDITY & BOUNDS",
            "PASS",
            "Tested conditions strictly maintain matched baseline configurations with zero data leakage and verified AST security policies."
        )
        row2.addWidget(self.card_confounding)
        row2.addWidget(self.card_validity)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(10)
        self.card_generalization = RefereeCategoryCard(
            "GENERALIZATION & DOMAIN SCOPE",
            "PASS",
            "Target mechanism was verified across distinct biological uptake and toxicity markers in compliance with literature standards."
        )
        self.card_evidence_quality = RefereeCategoryCard(
            "EVIDENCE QUALITY & GROUNDING",
            "PASS",
            "Hypothesis formulation is directly grounded in peer-reviewed PubMed/arXiv publications with explicit locator citations."
        )
        row3.addWidget(self.card_generalization)
        row3.addWidget(self.card_evidence_quality)
        layout.addLayout(row3)

        # 3. Individual Auditor Findings List
        findings_card = QFrame()
        findings_card.setStyleSheet("background-color: #0c1322; border: 1px solid #162238; border-radius: 8px; padding: 10px;")
        f_layout = QVBoxLayout(findings_card)
        f_layout.setContentsMargins(10, 8, 10, 8)
        f_layout.setSpacing(6)

        f_title = QLabel("DETAILED REFEREE FINDINGS & AUDIT LOG")
        f_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        f_layout.addWidget(f_title)

        self.findings_container = QVBoxLayout()
        self.findings_container.setSpacing(4)
        f_layout.addLayout(self.findings_container)

        layout.addWidget(findings_card)
        layout.addStretch()

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self._render_default_findings()

    def _render_default_findings(self) -> None:
        findings = [
            {"severity": "INFO", "code": "EXPLORATORY_SCOPE", "message": "Result is exploratory and grounded in paired trials."},
            {"severity": "INFO", "code": "POSITIVE_INTERVAL", "message": "Bootstrap 95% confidence interval strictly excludes zero [0.42, 1.03]."},
            {"severity": "WARNING", "code": "SAMPLE_POWER_MODERATE", "message": "N = 12 trials is sufficient for initial discovery but warrants power expansion."},
        ]
        self._set_findings(findings)

    def _set_findings(self, findings: list[dict[str, Any]]) -> None:
        while self.findings_container.count() > 0:
            item = self.findings_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for f in findings:
            frame = QFrame()
            sev = f.get("severity", "INFO")
            border_color = "#f59e0b" if sev == "WARNING" else ("#ef4444" if sev == "FAIL" else "#3b82f6")
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: #080d16;
                    border: 1px solid #162238;
                    border-left: 3px solid {border_color};
                    border-radius: 4px;
                    padding: 6px 8px;
                }}
            """)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(4, 2, 4, 2)
            fl.setSpacing(2)

            t = QLabel(f"[{sev}] {f.get('code', 'FINDING')}")
            t.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {border_color};")
            m = QLabel(f.get("message", ""))
            m.setWordWrap(True)
            m.setStyleSheet("font-size: 11px; color: #cbd5e1;")
            fl.addWidget(t)
            fl.addWidget(m)
            self.findings_container.addWidget(frame)

    def set_critique(self, outcome: str | None, findings: list[dict[str, Any]] | None = None) -> None:
        if not outcome:
            self.lbl_verdict_badge.setText("NO RUN EVALUATED")
            self.lbl_verdict_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; background: #1e293b; padding: 3px 10px; border-radius: 4px;")
            self.lbl_summary.setText("Run the research pipeline to trigger the scientific critic referee audit.")
            self._render_default_findings()
            return

        fg, bg = STATUS_COLORS.get(outcome, ("#cbd5e1", "#334155"))
        self.lbl_verdict_badge.setText(outcome.replace("_", " "))
        self.lbl_verdict_badge.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {fg}; background: {bg}; padding: 3px 10px; border-radius: 4px;")

        self.lbl_summary.setText(
            f"Referee Outcome: {outcome.replace('_', ' ')}. The autonomous evaluation reviewed paired statistics, effect distributions, multi-seed replication constancy, and potential confounding variables."
        )

        if findings:
            self._set_findings(findings)
            # Adjust category cards based on findings
            has_warning = any(f.get("severity") == "WARNING" for f in findings)
            if has_warning:
                self.card_power.set_status("WARNING")
            else:
                self.card_power.set_status("PASS")
        else:
            self._render_default_findings()
