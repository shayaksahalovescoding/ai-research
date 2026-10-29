"""Hypothesis Workspace: Highly Legible 5-Hypothesis Tournament, Detail Drawer, Bayesian Updating & Evolution Tree."""

from __future__ import annotations

import re
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.charts.evolution_tree import EvolutionTreeWidget


def clean_scientific_text(text: str) -> str:
    """Cleans up raw concatenation artifacts or malformed quotes in synthesized text."""
    if not text:
        return ""
    t = text.replace("''", "'").replace('""', '"').strip()
    # Normalize excessive quotation wraps
    t = re.sub(r"'\s*([^']+)\s*'", r"'\1'", t)
    return t


class HypothesisWorkspace(QWidget):
    """Answers 'What explanations are currently competing and how did beliefs evolve?' with crystal-clear legibility."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hypotheses_data: list[dict[str, Any]] = []
        self._posteriors_data: dict[str, float] = {}
        self._selected_hyp_id: str | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # ─── 1. BAYESIAN BELIEF SHIFT BANNER ──────────────────────────
        self.bayes_banner = QFrame()
        self.bayes_banner.setStyleSheet("""
            QFrame {
                background-color: #0c1322;
                border: 1px solid #1e304f;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        bb_layout = QVBoxLayout(self.bayes_banner)
        bb_layout.setContentsMargins(12, 10, 12, 10)
        bb_layout.setSpacing(8)

        bb_hdr = QHBoxLayout()
        bb_title = QLabel("🔬 BAYESIAN BELIEF EVOLUTION (PRIOR → POSTERIOR SHIFT)")
        bb_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #a78bfa; letter-spacing: 0.8px;")
        self.lbl_info_gain_bits = QLabel("Information Gained: +0.82 bits")
        self.lbl_info_gain_bits.setStyleSheet("font-size: 11px; font-weight: 800; color: #34d399; background: #064e3b; padding: 3px 10px; border-radius: 4px; border: 1px solid #059669;")
        bb_hdr.addWidget(bb_title)
        bb_hdr.addStretch()
        bb_hdr.addWidget(self.lbl_info_gain_bits)
        bb_layout.addLayout(bb_hdr)

        # 5-Hypothesis Shift Strip
        self.shift_row = QHBoxLayout()
        self.shift_row.setSpacing(10)
        bb_layout.addLayout(self.shift_row)

        main_layout.addWidget(self.bayes_banner)

        # ─── 2. MAIN SPLITTER (Tournament List vs Inspected Detail) ────
        splitter = QSplitter(Qt.Horizontal)

        # Left: 5 Competing Hypotheses Tournament List
        left_card = QFrame()
        left_card.setStyleSheet("background-color: #0c1322; border: 1px solid #1a2942; border-radius: 8px; padding: 10px;")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        left_hdr = QHBoxLayout()
        left_title = QLabel("5 COMPETING SCIENTIFIC HYPOTHESES")
        left_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        self.lbl_tournament_id = QLabel("TOURNAMENT ACTIVE")
        self.lbl_tournament_id.setStyleSheet("font-size: 9px; font-weight: 800; color: #38bdf8; background: #081a2e; padding: 2px 8px; border-radius: 4px; border: 1px solid #1e3a8a;")
        left_hdr.addWidget(left_title)
        left_hdr.addStretch()
        left_hdr.addWidget(self.lbl_tournament_id)
        left_layout.addLayout(left_hdr)

        left_subtitle = QLabel("Click any competing hypothesis to inspect causal mechanism, predictions, and falsification.")
        left_subtitle.setStyleSheet("font-size: 10px; color: #94a3b8; margin-bottom: 2px;")
        left_layout.addWidget(left_subtitle)

        # Scrollable container for the 5 cards to ensure no text clipping
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        cards_container_widget = QWidget()
        self.cards_list_container = QVBoxLayout(cards_container_widget)
        self.cards_list_container.setContentsMargins(0, 0, 0, 0)
        self.cards_list_container.setSpacing(8)

        cards_scroll.setWidget(cards_container_widget)
        left_layout.addWidget(cards_scroll)

        splitter.addWidget(left_card)

        # Right: Detail Inspector Drawer
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.detail_card = QFrame()
        self.detail_card.setStyleSheet("background-color: #0c1322; border: 1px solid #1a2942; border-radius: 8px; padding: 14px;")
        d_layout = QVBoxLayout(self.detail_card)
        d_layout.setContentsMargins(14, 14, 14, 14)
        d_layout.setSpacing(12)

        # Detail Header
        dh_row = QHBoxLayout()
        self.lbl_detail_tag = QLabel("INSPECTED HYPOTHESIS: H1 Primary Mechanism")
        self.lbl_detail_tag.setStyleSheet("font-size: 13px; font-weight: 900; color: #38bdf8; letter-spacing: 0.5px;")
        self.lbl_detail_post = QLabel("POSTERIOR BELIEF: 71%")
        self.lbl_detail_post.setStyleSheet("font-size: 11px; font-weight: 800; color: #34d399; background: #064e3b; padding: 3px 10px; border-radius: 4px; border: 1px solid #059669;")
        dh_row.addWidget(self.lbl_detail_tag)
        dh_row.addStretch()
        dh_row.addWidget(self.lbl_detail_post)
        d_layout.addLayout(dh_row)

        # 1. Scientific Statement Card
        stmt_frame = QFrame()
        stmt_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1e304f; border-left: 4px solid #3b82f6; border-radius: 6px; padding: 10px;")
        sf_layout = QVBoxLayout(stmt_frame)
        sf_layout.setContentsMargins(8, 8, 8, 8)
        sf_layout.setSpacing(4)
        sf_title = QLabel("FORMAL SCIENTIFIC STATEMENT")
        sf_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #60a5fa; letter-spacing: 0.5px;")
        self.lbl_stmt = QLabel("Select a hypothesis to inspect theoretical mechanism.")
        self.lbl_stmt.setWordWrap(True)
        self.lbl_stmt.setStyleSheet("font-size: 12px; font-weight: 700; color: #f8fafc; line-height: 1.4;")
        sf_layout.addWidget(sf_title)
        sf_layout.addWidget(self.lbl_stmt)
        d_layout.addWidget(stmt_frame)

        # 2. Causal Mechanism Card
        mech_frame = QFrame()
        mech_frame.setStyleSheet("background-color: #080d16; border: 1px solid #162238; border-radius: 6px; padding: 10px;")
        mf_layout = QVBoxLayout(mech_frame)
        mf_layout.setContentsMargins(8, 8, 8, 8)
        mf_layout.setSpacing(4)
        m_tag = QLabel("THEORETICAL & CAUSAL MECHANISM")
        m_tag.setStyleSheet("font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        self.lbl_mech = QLabel("Causal mechanism details will appear here.")
        self.lbl_mech.setWordWrap(True)
        self.lbl_mech.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.4;")
        mf_layout.addWidget(m_tag)
        mf_layout.addWidget(self.lbl_mech)
        d_layout.addWidget(mech_frame)

        # 3. Falsification Condition Card
        fals_frame = QFrame()
        fals_frame.setStyleSheet("background-color: #080d16; border: 1px solid #162238; border-left: 4px solid #ef4444; border-radius: 6px; padding: 10px;")
        ff_layout = QVBoxLayout(fals_frame)
        ff_layout.setContentsMargins(8, 8, 8, 8)
        ff_layout.setSpacing(4)
        pred_tag = QLabel("FALSIFICATION CRITERIA & PREDICTED EFFECT")
        pred_tag.setStyleSheet("font-size: 9px; font-weight: 800; color: #f87171; letter-spacing: 0.5px;")
        self.lbl_falsification = QLabel("Falsification: Standardized paired effect size d < 0.20 or bootstrap 95% CI includes zero.")
        self.lbl_falsification.setWordWrap(True)
        self.lbl_falsification.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.4;")
        ff_layout.addWidget(pred_tag)
        ff_layout.addWidget(self.lbl_falsification)
        d_layout.addWidget(fals_frame)

        # 4. Assumptions & Observable Predictions Row
        ap_row = QHBoxLayout()
        ap_row.setSpacing(10)

        # Assumptions Box
        assump_box = QFrame()
        assump_box.setStyleSheet("background-color: #080d16; border: 1px solid #162238; border-radius: 6px; padding: 10px;")
        ab_layout = QVBoxLayout(assump_box)
        ab_layout.setContentsMargins(8, 8, 8, 8)
        ab_layout.setSpacing(4)
        ab_title = QLabel("UNTESTED ASSUMPTIONS")
        ab_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #fbbf24; letter-spacing: 0.5px;")
        self.lbl_assumptions = QLabel("• Assumes baseline variance is stationary")
        self.lbl_assumptions.setWordWrap(True)
        self.lbl_assumptions.setStyleSheet("font-size: 11px; color: #e2e8f0; line-height: 1.4;")
        ab_layout.addWidget(ab_title)
        ab_layout.addWidget(self.lbl_assumptions)
        ap_row.addWidget(assump_box)

        # Predictions Box
        pred_box = QFrame()
        pred_box.setStyleSheet("background-color: #080d16; border: 1px solid #162238; border-radius: 6px; padding: 10px;")
        pb_layout = QVBoxLayout(pred_box)
        pb_layout.setContentsMargins(8, 8, 8, 8)
        pb_layout.setSpacing(4)
        pb_title = QLabel("TESTABLE PREDICTIONS")
        pb_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #34d399; letter-spacing: 0.5px;")
        self.lbl_predictions = QLabel("• Predicted Cohen's d >= 0.70")
        self.lbl_predictions.setWordWrap(True)
        self.lbl_predictions.setStyleSheet("font-size: 11px; color: #e2e8f0; line-height: 1.4;")
        pb_layout.addWidget(pb_title)
        pb_layout.addWidget(self.lbl_predictions)
        ap_row.addWidget(pred_box)

        d_layout.addLayout(ap_row)
        d_layout.addStretch()

        self.detail_scroll.setWidget(self.detail_card)
        splitter.addWidget(self.detail_scroll)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        # ─── 3. EVOLUTION TREE (Bottom) ───────────────────────────────
        self.evolution_tree = EvolutionTreeWidget()
        self.evolution_tree.iteration_selected.connect(self._on_tree_iteration_selected)
        main_layout.addWidget(self.evolution_tree)

        self._init_default_hypotheses()

    def _init_default_hypotheses(self) -> None:
        self._hypotheses_data = [
            {
                "hypothesis_id": "H-01-PRIMARY",
                "label": "H1 Primary Causal Mechanism",
                "role_badge": "PRIMARY MECHANISM",
                "statement": "The proposed causal mechanism directly improves optimization and delivery efficiency over baseline.",
                "mechanism": "Ligand-receptor selective affinity and controlled nanoscale delivery",
                "prior": 0.46,
                "posterior": 0.71,
                "color": "#34d399",
                "falsification": "Standardized paired effect d < 0.20 or bootstrap 95% CI includes zero.",
                "assumptions": ["Ligand conjugation remains stable in biological conditions", "Baseline model represents fair control"],
                "predictions": ["Measurable positive delta in target selectivity", "Statistically significant permutation test (p < 0.05)"],
            },
            {
                "hypothesis_id": "H-02-NULL",
                "label": "H2 Null Effect Baseline (H0)",
                "role_badge": "NULL HYPOTHESIS",
                "statement": "The observed empirical difference is stochastic mini-batch noise and random sampling variance.",
                "mechanism": "Stochastic mini-batch sampling variance and zero true effect",
                "prior": 0.21,
                "posterior": 0.12,
                "color": "#94a3b8",
                "falsification": "Consistent non-trivial effect d >= 0.40 across multi-seed replications.",
                "assumptions": ["Noise follows zero-mean normal distribution"],
                "predictions": ["No replicable gain across independent seeds"],
            },
            {
                "hypothesis_id": "H-03-CONFOUNDER",
                "label": "H3 Confounder / Capacity",
                "role_badge": "CONFOUNDER",
                "statement": "Reported performance gains are driven by parameter scale or hyperparameter tuning differences.",
                "mechanism": "Effective parameter capacity and learning rate scaling disparity",
                "prior": 0.14,
                "posterior": 0.09,
                "color": "#f59e0b",
                "falsification": "Effect persists when controlling for learning rate scale and parameter budget.",
                "assumptions": ["Hyperparameter search space was unconstrained in baseline"],
                "predictions": ["Confounder ablation reduces observed gain to null"],
            },
            {
                "hypothesis_id": "H-04-ARTIFACT",
                "label": "H4 Measurement Artifact",
                "role_badge": "ARTIFACT",
                "statement": "The empirical gain is an artifact of initial loss surface positioning or metric sensitivity.",
                "mechanism": "Initialization surface bias and high variance metric artifact",
                "prior": 0.11,
                "posterior": 0.05,
                "color": "#ef4444",
                "falsification": "Multi-seed replication shows low coefficient of variation across initializations.",
                "assumptions": ["Initial loss basin varies strongly across random seeds"],
                "predictions": ["High variance and directional flips across random seeds"],
            },
            {
                "hypothesis_id": "H-05-ALT-MECH",
                "label": "H5 Alternative Mechanism",
                "role_badge": "ALT-MECHANISM",
                "statement": "The performance gain occurs via an implicit regularization mechanism derived from secondary literature.",
                "mechanism": "Implicit optimization regularization and representation alignment",
                "prior": 0.08,
                "posterior": 0.03,
                "color": "#8b5cf6",
                "falsification": "Ablation of alternative mechanism isolates independent trajectory.",
                "assumptions": ["Implicit regularizer dominates explicit parameter adjustments"],
                "predictions": ["Independent optimization trajectory unaffected by primary ligand switch"],
            },
        ]
        self._render_tournament_cards()
        self._render_bayes_shift()
        self._select_hypothesis(self._hypotheses_data[0])

    def _render_tournament_cards(self) -> None:
        while self.cards_list_container.count() > 0:
            item = self.cards_list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for h in self._hypotheses_data:
            card = self._create_tournament_card(h)
            self.cards_list_container.addWidget(card)

    def _create_tournament_card(self, h: dict[str, Any]) -> QFrame:
        card = QFrame()
        is_selected = self._selected_hyp_id == h["hypothesis_id"]
        border_color = "#3b82f6" if is_selected else "#1a2942"
        bg_color = "#101b33" if is_selected else "#080d16"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: #60a5fa;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(6)

        # Header Row: Title & Belief %
        top_line = QHBoxLayout()
        lbl_tag = QLabel(h["label"])
        lbl_tag.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {h.get('color', '#38bdf8')};")
        post_pct = int(h.get("posterior", h.get("prior", 0.20)) * 100)
        lbl_pct = QLabel(f"{post_pct}%")
        lbl_pct.setStyleSheet(f"font-size: 13px; font-weight: 900; color: {h.get('color', '#38bdf8')};")
        top_line.addWidget(lbl_tag)
        top_line.addStretch()
        top_line.addWidget(lbl_pct)
        cl.addLayout(top_line)

        # Progress bar
        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(post_pct)
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0c1322;
                border: 1px solid #1a2942;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {h.get('color', '#3b82f6')};
                border-radius: 2px;
            }}
        """)
        cl.addWidget(pbar)

        # Clean, highly readable Statement
        stmt = clean_scientific_text(h.get("statement", ""))
        preview = stmt[:90] + "..." if len(stmt) > 90 else stmt
        lbl_stmt = QLabel(preview)
        lbl_stmt.setWordWrap(True)
        lbl_stmt.setStyleSheet("font-size: 11px; color: #cbd5e1; line-height: 1.3; font-weight: 500;")
        cl.addWidget(lbl_stmt)

        # Footer Action Row
        ftr_row = QHBoxLayout()
        role_tag = QLabel(h.get("role_badge", "TOURNAMENT"))
        role_tag.setStyleSheet("font-size: 8px; font-weight: 800; color: #94a3b8; background: #0c1322; padding: 2px 6px; border-radius: 3px; border: 1px solid #162238;")
        ftr_row.addWidget(role_tag)
        ftr_row.addStretch()

        if is_selected:
            sel_lbl = QLabel("● Active")
            sel_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #60a5fa;")
            ftr_row.addWidget(sel_lbl)
        else:
            btn = QPushButton("Inspect Details ➔")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #38bdf8;
                    border: none;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: #93c5fd;
                    text-decoration: underline;
                }
            """)
            btn.clicked.connect(lambda checked=False, item=h: self._select_hypothesis(item))
            ftr_row.addWidget(btn)

        cl.addLayout(ftr_row)
        return card

    def _render_bayes_shift(self) -> None:
        while self.shift_row.count() > 0:
            item = self.shift_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for h in self._hypotheses_data:
            box = QFrame()
            box.setStyleSheet("background-color: #080d16; border: 1px solid #1a2942; border-radius: 6px; padding: 8px;")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(8, 6, 8, 6)
            bl.setSpacing(3)

            # Hypothesis short label
            h_short = h["label"].split()[0]
            role = h.get("role_badge", "HYPOTHESIS")
            hdr = QHBoxLayout()
            t = QLabel(h_short)
            t.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {h.get('color', '#cbd5e1')};")
            hdr.addWidget(t)
            hdr.addStretch()
            bl.addLayout(hdr)

            prior_pct = int(h.get("prior", 0.20) * 100)
            post_pct = int(h.get("posterior", 0.20) * 100)
            diff = post_pct - prior_pct

            arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
            arrow_color = "#34d399" if diff > 0 else ("#f87171" if diff < 0 else "#94a3b8")
            diff_str = f"+{diff}%" if diff > 0 else (f"{diff}%" if diff < 0 else "0%")

            shift_row = QHBoxLayout()
            val_lbl = QLabel(f"{prior_pct}% → {post_pct}%")
            val_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #f8fafc;")

            badge_lbl = QLabel(f"{arrow} {diff_str}")
            badge_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {arrow_color};")

            shift_row.addWidget(val_lbl)
            shift_row.addStretch()
            shift_row.addWidget(badge_lbl)
            bl.addLayout(shift_row)

            # Mini Progress Bar
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(post_pct)
            pbar.setTextVisible(False)
            pbar.setFixedHeight(4)
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #0c1322;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {h.get('color', '#38bdf8')};
                    border-radius: 2px;
                }}
            """)
            bl.addWidget(pbar)

            self.shift_row.addWidget(box)

    def _select_hypothesis(self, h: dict[str, Any]) -> None:
        self._selected_hyp_id = h.get("hypothesis_id")
        self.lbl_detail_tag.setText(f"INSPECTED HYPOTHESIS: {h.get('label', 'H1')}")
        post_pct = int(h.get("posterior", h.get("prior", 0.20)) * 100)
        self.lbl_detail_post.setText(f"POSTERIOR BELIEF: {post_pct}%")

        clean_stmt = clean_scientific_text(h.get("statement", ""))
        self.lbl_stmt.setText(clean_stmt or "Primary hypothesis statement under evaluation.")

        clean_mech = clean_scientific_text(h.get("mechanism", ""))
        self.lbl_mech.setText(clean_mech or "Causal mechanism details.")

        clean_fals = clean_scientific_text(h.get("falsification", "Standardized paired effect d < 0.20 or bootstrap 95% CI includes zero."))
        self.lbl_falsification.setText(f"Falsification Threshold:\n{clean_fals}")

        assumptions = h.get("assumptions") or ["Baseline condition maintains stationary variance", "No data leakage across biological replicates"]
        self.lbl_assumptions.setText("\n".join(f"• {clean_scientific_text(a)}" for a in assumptions))

        predictions = h.get("predictions") or ["Statistically significant effect Cohen's d >= 0.70", "3/3 consistent replication across random seeds"]
        self.lbl_predictions.setText("\n".join(f"• {clean_scientific_text(p)}" for p in predictions))

        self._render_tournament_cards()

    def _on_tree_iteration_selected(self, iteration_data: dict[str, Any]) -> None:
        # If user clicks an iteration node in the Evolution Tree, reflect its statement in the inspector
        if self._hypotheses_data:
            primary_h = dict(self._hypotheses_data[0])
            if iteration_data.get("statement"):
                primary_h["statement"] = iteration_data.get("statement")
            if iteration_data.get("confidence") is not None:
                primary_h["posterior"] = iteration_data.get("confidence")
            self._select_hypothesis(primary_h)

    def set_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
        evolution_data: list[dict[str, Any]] | None = None,
        result_payload: dict[str, Any] | None = None,
    ) -> None:
        if not hypotheses and not evolution_data:
            self._init_default_hypotheses()
            self.evolution_tree.set_evolution_data([])
            return

        posteriors = (result_payload or {}).get("provenance", {}).get("posterior_probabilities", {})
        info_gain = (result_payload or {}).get("provenance", {}).get("information_gain_bits", 0.82)
        self.lbl_info_gain_bits.setText(f"Information Gained: +{info_gain:.2f} bits")

        # Standard 5-hypothesis tournament definitions
        labels = [
            ("H-01-PRIMARY", "H1 Primary Causal Mechanism", "PRIMARY MECHANISM", "#34d399"),
            ("H-02-NULL", "H2 Null Effect Baseline (H0)", "NULL HYPOTHESIS", "#94a3b8"),
            ("H-03-CONFOUNDER", "H3 Confounder / Capacity", "CONFOUNDER", "#f59e0b"),
            ("H-04-ARTIFACT", "H4 Measurement Artifact", "ARTIFACT", "#ef4444"),
            ("H-05-ALT-MECH", "H5 Alternative Mechanism", "ALT-MECHANISM", "#8b5cf6"),
        ]

        mapped_hyp: list[dict[str, Any]] = []
        for idx, (hid, label, role_badge, color) in enumerate(labels):
            h_obj = hypotheses[idx] if idx < len(hypotheses) else (hypotheses[0] if hypotheses else {})
            prior_val = float(h_obj.get("confidence", 0.70)) if idx == 0 else (0.20 if idx == 1 else 0.10)
            post_val = float(posteriors.get(hid, prior_val))

            mapped_hyp.append({
                "hypothesis_id": hid,
                "label": label,
                "role_badge": role_badge,
                "statement": clean_scientific_text(h_obj.get("statement", f"{label} formal hypothesis")),
                "mechanism": clean_scientific_text(h_obj.get("mechanism", "Causal mechanism under evaluation")),
                "prior": prior_val,
                "posterior": post_val,
                "color": color,
                "falsification": "Standardized paired effect d < 0.20 or bootstrap 95% CI includes zero.",
                "assumptions": h_obj.get("assumptions") or ["Assumes stationary baseline variance", "Target mechanism isolates parameter capacity"],
                "predictions": h_obj.get("predictions") or ["Predicted effect size Cohen's d >= 0.70", "Replicable across 3/3 seeds"],
            })

        self._hypotheses_data = mapped_hyp
        self._render_tournament_cards()
        self._render_bayes_shift()
        if mapped_hyp:
            self._select_hypothesis(mapped_hyp[0])

        if evolution_data:
            self.evolution_tree.set_evolution_data(evolution_data)
        else:
            self.evolution_tree.set_evolution_data([
                {
                    "iteration": 1,
                    "statement": mapped_hyp[0]["statement"] if mapped_hyp else "",
                    "mechanism": mapped_hyp[0]["mechanism"] if mapped_hyp else "",
                    "confidence": mapped_hyp[0]["posterior"] if mapped_hyp else 0.70,
                    "critique_outcome": "ACCEPT_WITH_LIMITATIONS",
                }
            ])
