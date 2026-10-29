"""Academic Manuscript & Research Paper Exporter Modal Dialog for PySide6 GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from PySide6.QtGui import QGuiApplication, QPageSize, QPdfWriter, QTextDocument
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class ManuscriptModal(QDialog):
    """Publication-ready academic manuscript viewer, exporter (PDF/LaTeX/Markdown) and editor."""

    def __init__(self, manuscript_data: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manuscript = manuscript_data
        self.setWindowTitle(f"📄 Academic Manuscript: {self.manuscript.get('title', 'Research Paper')}")
        self.resize(1020, 760)
        self.setMinimumSize(850, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Hero Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #0e1626;
                border: 1px solid #1c2a42;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(12, 10, 12, 10)
        h_layout.setSpacing(6)

        top_row = QHBoxLayout()
        title_lbl = QLabel(self.manuscript.get("title", "Autonomous Research Paper"))
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        citations = self.manuscript.get("citation_count", 0)
        badge_lbl = QLabel(f"📚 {citations} Citations")
        badge_lbl.setStyleSheet("font-size: 10px; font-weight: 700; background: #172554; color: #93c5fd; padding: 3px 8px; border-radius: 4px;")
        top_row.addWidget(badge_lbl)

        format_badge = QLabel("ARXIV / OVERLEAF READY")
        format_badge.setStyleSheet("font-size: 10px; font-weight: 700; background: #064e3b; color: #a7f3d0; padding: 3px 8px; border-radius: 4px;")
        top_row.addWidget(format_badge)
        h_layout.addLayout(top_row)

        meta_lbl = QLabel(f"Generated on {self.manuscript.get('created_date', 'today')} • Autonomous AI Research Scientist Engine")
        meta_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        h_layout.addWidget(meta_lbl)

        layout.addWidget(header_card)

        # Main Format Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #172033;
                background: #090e18;
                border-radius: 10px;
                padding: 4px;
            }
        """)

        # Tab 1: Rendered Academic Paper (HTML)
        self.browser_html = QTextBrowser()
        self.browser_html.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #1e293b;
                border: none;
                border-radius: 8px;
                padding: 24px;
                font-family: 'Charter', 'Georgia', serif;
                font-size: 13px;
            }
        """)
        self.browser_html.setHtml(self.manuscript.get("html", ""))
        self.tabs.addTab(self.browser_html, "📖 Formatted Article")

        # Tab 2: Markdown Source
        self.txt_markdown = QPlainTextEdit()
        self.txt_markdown.setStyleSheet("""
            QPlainTextEdit {
                background-color: #070a12;
                color: #e2e8f0;
                border: none;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 14px;
                line-height: 1.5;
            }
        """)
        self.txt_markdown.setPlainText(self.manuscript.get("markdown", ""))
        self.tabs.addTab(self.txt_markdown, "📝 Markdown (.md)")

        # Tab 3: LaTeX Source
        self.txt_latex = QPlainTextEdit()
        self.txt_latex.setStyleSheet("""
            QPlainTextEdit {
                background-color: #070a12;
                color: #38bdf8;
                border: none;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 14px;
                line-height: 1.5;
            }
        """)
        self.txt_latex.setPlainText(self.manuscript.get("latex", ""))
        self.tabs.addTab(self.txt_latex, "📐 LaTeX (.tex)")

        layout.addWidget(self.tabs)

        # Bottom Action Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.btn_copy = QPushButton("📋 Copy Current View")
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #131d2e;
                color: #cbd5e1;
                border: 1px solid #22324e;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1a273e;
                color: #ffffff;
                border-color: #3b82f6;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_current_tab)
        action_bar.addWidget(self.btn_copy)

        action_bar.addStretch()

        # Export Markdown
        self.btn_export_md = QPushButton("💾 Export Markdown (.md)")
        self.btn_export_md.setStyleSheet("""
            QPushButton {
                background-color: #131d2e;
                color: #cbd5e1;
                border: 1px solid #22324e;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1a273e;
                border-color: #3b82f6;
            }
        """)
        self.btn_export_md.clicked.connect(self._export_markdown)
        action_bar.addWidget(self.btn_export_md)

        # Export LaTeX
        self.btn_export_tex = QPushButton("📐 Export LaTeX (.tex)")
        self.btn_export_tex.setStyleSheet("""
            QPushButton {
                background-color: #1e1b4b;
                color: #c7d2fe;
                border: 1px solid #4338ca;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #312e81;
                border-color: #6366f1;
            }
        """)
        self.btn_export_tex.clicked.connect(self._export_latex)
        action_bar.addWidget(self.btn_export_tex)

        # Export PDF
        self.btn_export_pdf = QPushButton("📥 Export PDF Document")
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #06b6d4);
                color: #ffffff;
                border: 1px solid #60a5fa;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #0891b2);
                border-color: #93c5fd;
            }
        """)
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        action_bar.addWidget(self.btn_export_pdf)

        # Close
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #0b111e;
                color: #94a3b8;
                border: 1px solid #172033;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #141f33;
                color: #f8fafc;
            }
        """)
        btn_close.clicked.connect(self.accept)
        action_bar.addWidget(btn_close)

        layout.addLayout(action_bar)

    def _copy_current_tab(self) -> None:
        idx = self.tabs.currentIndex()
        clipboard = QGuiApplication.clipboard()
        if idx == 0:
            clipboard.setText(self.browser_html.toPlainText())
        elif idx == 1:
            clipboard.setText(self.txt_markdown.toPlainText())
        elif idx == 2:
            clipboard.setText(self.txt_latex.toPlainText())
        QMessageBox.information(self, "Copied", "Content copied to system clipboard.")

    def _export_markdown(self) -> None:
        default_name = f"{self._safe_filename(self.manuscript.get('title', 'paper'))}.md"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Manuscript as Markdown", default_name, "Markdown Files (*.md)")
        if not file_path:
            return
        try:
            content = self.txt_markdown.toPlainText()
            Path(file_path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Successfully exported Markdown to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save Markdown:\n{e}")

    def _export_latex(self) -> None:
        default_name = f"{self._safe_filename(self.manuscript.get('title', 'paper'))}.tex"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Manuscript as LaTeX", default_name, "LaTeX Files (*.tex)")
        if not file_path:
            return
        try:
            content = self.txt_latex.toPlainText()
            Path(file_path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Successfully exported LaTeX to:\n{file_path}\nReady for arXiv or Overleaf submission.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save LaTeX:\n{e}")

    def _export_pdf(self) -> None:
        default_name = f"{self._safe_filename(self.manuscript.get('title', 'paper'))}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Manuscript as PDF", default_name, "PDF Files (*.pdf)")
        if not file_path:
            return
        try:
            doc = QTextDocument()
            doc.setHtml(self.manuscript.get("html", ""))
            writer = QPdfWriter(file_path)
            writer.setPageSize(QPageSize(QPageSize.A4))
            doc.print_(writer)
            QMessageBox.information(self, "PDF Export Complete", f"Successfully compiled and exported PDF to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF:\n{e}")

    @staticmethod
    def _safe_filename(title: str) -> str:
        return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in title)[:48].strip("_")
