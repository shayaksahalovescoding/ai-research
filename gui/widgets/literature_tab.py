"""Ultra-modern Semantic Vector Search, Literature & PDF Full-Text Reader Tab."""

from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.literature.pdf_reader import PDFSectionExtractor
from app.literature.providers import RetrievedPaper
from app.literature.vector_store import global_vector_store

SOURCE_BADGES = {
    "PubMed": ("#34d399", "#064e3b", "🟢 PubMed (NIH)"),
    "OpenAlex": ("#c084fc", "#4c1d95", "🟣 OpenAlex Global"),
    "arXiv": ("#60a5fa", "#172554", "🔵 arXiv Preprint"),
    "Web Search": ("#fbbf24", "#451a03", "🟠 Scientific Web"),
}


class LiteratureTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.papers_data: list[dict[str, Any]] = []
        self.paper_details_map: dict[str, dict[str, Any]] = {}
        self.all_papers_cache: list[dict[str, Any]] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Header Section
        header_box = QHBoxLayout()
        header_left = QVBoxLayout()
        header_left.setSpacing(2)
        header_lbl = QLabel("📚 Semantic Vector Search & Multi-Source PDF Full-Text Reader")
        header_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
        sub_lbl = QLabel(
            "Vector search across arXiv, PubMed Central, and OpenAlex full-text PDFs with deep extraction of methodology, tables, and figures."
        )
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        header_left.addWidget(header_lbl)
        header_left.addWidget(sub_lbl)
        header_box.addLayout(header_left)
        header_box.addStretch()
        main_layout.addLayout(header_box)

        # Semantic Search Toolbar
        search_card = QFrame()
        search_card.setStyleSheet("""
            QFrame {
                background-color: #0b1220;
                border: 1px solid #1c2a42;
                border-radius: 10px;
                padding: 6px;
            }
        """)
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(8, 8, 8, 8)
        search_layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Semantic Vector Search query across full-text papers, methodology, and tables...")
        self.input_search.setStyleSheet("""
            QLineEdit {
                background-color: #070d18;
                border: 1px solid #1e2d48;
                border-radius: 6px;
                padding: 7px 12px;
                color: #f8fafc;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        self.input_search.returnPressed.connect(self._on_search_clicked)
        search_row.addWidget(self.input_search, 1)

        self.btn_search = QPushButton("🔍 Vector Search")
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 700;
                font-size: 11px;
                border-radius: 6px;
                padding: 7px 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_search.clicked.connect(self._on_search_clicked)
        search_row.addWidget(self.btn_search)

        self.btn_reset_search = QPushButton("✖ Clear")
        self.btn_reset_search.setStyleSheet("""
            QPushButton {
                background-color: #172033;
                color: #94a3b8;
                font-weight: 600;
                font-size: 11px;
                border-radius: 6px;
                padding: 7px 12px;
                border: 1px solid #1e293b;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
            }
        """)
        self.btn_reset_search.clicked.connect(self._on_reset_search)
        search_row.addWidget(self.btn_reset_search)
        search_layout.addLayout(search_row)

        # Filters Row
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        lbl_filter = QLabel("FILTERS:")
        lbl_filter.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 0.5px;")
        filters_row.addWidget(lbl_filter)

        self.combo_year = QComboBox()
        self.combo_year.addItems(["📅 All Years", "2024+", "2022+", "2020+", "2018+"])
        self.combo_year.setStyleSheet(self._combo_style())
        self.combo_year.currentIndexChanged.connect(self._on_filter_changed)
        filters_row.addWidget(self.combo_year)

        self.combo_source = QComboBox()
        self.combo_source.addItems(["🌐 All Sources", "PubMed (NIH)", "OpenAlex", "arXiv", "Web"])
        self.combo_source.setStyleSheet(self._combo_style())
        self.combo_source.currentIndexChanged.connect(self._on_filter_changed)
        filters_row.addWidget(self.combo_source)

        self.combo_section = QComboBox()
        self.combo_section.addItems(["📑 All Sections", "Methodology", "Results Tables", "Figure Captions", "Abstracts"])
        self.combo_section.setStyleSheet(self._combo_style())
        self.combo_section.currentIndexChanged.connect(self._on_filter_changed)
        filters_row.addWidget(self.combo_section)

        self.combo_citations = QComboBox()
        self.combo_citations.addItems(["⭐ Any Citations", "10+ Citations", "25+ Citations", "50+ Citations"])
        self.combo_citations.setStyleSheet(self._combo_style())
        self.combo_citations.currentIndexChanged.connect(self._on_filter_changed)
        filters_row.addWidget(self.combo_citations)

        filters_row.addStretch()
        search_layout.addLayout(filters_row)
        main_layout.addWidget(search_card)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Papers / Search Results List
        list_container = QFrame()
        list_container.setStyleSheet("background: #0a0f1d; border: 1px solid #172033; border-radius: 10px; padding: 6px;")
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(6)

        list_header_row = QHBoxLayout()
        self.lbl_list_title = QLabel("RETRIEVED PUBLICATIONS")
        self.lbl_list_title.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 10px; letter-spacing: 0.5px;")
        self.lbl_paper_count = QLabel("0 papers")
        self.lbl_paper_count.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        list_header_row.addWidget(self.lbl_list_title)
        list_header_row.addStretch()
        list_header_row.addWidget(self.lbl_paper_count)
        list_layout.addLayout(list_header_row)

        self.paper_list = QListWidget()
        self.paper_list.currentItemChanged.connect(self._on_paper_selected)
        list_layout.addWidget(self.paper_list)

        splitter.addWidget(list_container)

        # Right Column: Multi-Section Full-Text Inspector
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(8, 0, 8, 8)
        self.detail_layout.setSpacing(12)

        # Hero Card for Selected Paper
        self.hero_card = QFrame()
        self.hero_card.setStyleSheet("""
            QFrame {
                background-color: #0e1626;
                border: 1px solid #1c2a42;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(12, 12, 12, 12)
        hero_layout.setSpacing(8)

        badge_row = QHBoxLayout()
        self.lbl_provider_badge = QLabel("READY")
        self.lbl_provider_badge.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 5px; background: #172033; color: #94a3b8;"
        )
        self.lbl_citation_badge = QLabel("⭐ 18 Citations")
        self.lbl_citation_badge.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 5px; background: #1f293d; color: #fbbf24;"
        )
        badge_row.addWidget(self.lbl_provider_badge)
        badge_row.addWidget(self.lbl_citation_badge)
        badge_row.addStretch()

        self.lbl_url = QLabel("")
        self.lbl_url.setOpenExternalLinks(True)
        self.lbl_url.setStyleSheet("font-size: 11px; color: #38bdf8; font-weight: 600;")
        badge_row.addWidget(self.lbl_url)
        hero_layout.addLayout(badge_row)

        self.lbl_paper_title = QLabel("Select a publication from the list")
        self.lbl_paper_title.setWordWrap(True)
        self.lbl_paper_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc; line-height: 1.3;")
        hero_layout.addWidget(self.lbl_paper_title)

        self.lbl_authors = QLabel("")
        self.lbl_authors.setWordWrap(True)
        self.lbl_authors.setStyleSheet("font-size: 11px; color: #94a3b8;")
        hero_layout.addWidget(self.lbl_authors)

        self.detail_layout.addWidget(self.hero_card)

        # Multi-Section Inspector Tabs
        self.section_tabs = QTabWidget()
        self.section_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #172033;
                background: #080d16;
                border-radius: 8px;
                padding: 4px;
            }
            QTabBar::tab {
                background: #0d1524;
                color: #94a3b8;
                border: 1px solid #1a273e;
                border-radius: 6px;
                padding: 6px 12px;
                margin-right: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #172642;
                color: #60a5fa;
                border: 1px solid #3b82f6;
            }
        """)

        # Tab 1: Abstract
        self.txt_abstract = QTextBrowser()
        self.txt_abstract.setStyleSheet(self._browser_style())
        self.section_tabs.addTab(self.txt_abstract, "📄 Abstract & Overview")

        # Tab 2: Methodology
        self.txt_methodology = QTextBrowser()
        self.txt_methodology.setStyleSheet(self._browser_style())
        self.section_tabs.addTab(self.txt_methodology, "⚙️ Methodology & Setup")

        # Tab 3: Tables & Figures
        self.txt_tables = QTextBrowser()
        self.txt_tables.setStyleSheet(self._browser_style())
        self.section_tabs.addTab(self.txt_tables, "📊 Extracted Tables & Figures")

        # Tab 4: Vector Chunks & Evidence
        self.evidence_container = QWidget()
        self.evidence_layout = QVBoxLayout(self.evidence_container)
        self.evidence_layout.setContentsMargins(6, 6, 6, 6)
        self.evidence_layout.setSpacing(8)
        self.section_tabs.addTab(self.evidence_container, "📌 Verifiable Evidence Chunks")

        self.detail_layout.addWidget(self.section_tabs)
        self.detail_layout.addStretch()
        self.detail_area.setWidget(self.detail_container)

        splitter.addWidget(self.detail_area)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #070d18;
                border: 1px solid #1e2d48;
                border-radius: 5px;
                padding: 4px 8px;
                color: #cbd5e1;
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                background-color: #070d18;
                color: #f8fafc;
                selection-background-color: #1d4ed8;
            }
        """

    def _browser_style(self) -> str:
        return """
            QTextBrowser {
                background-color: #060a12;
                border: 1px solid #121d30;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                line-height: 1.6;
                padding: 10px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
        """

    def set_papers(self, papers: list[dict[str, Any]], paper_details_map: dict[str, dict[str, Any]] | None = None) -> None:
        self.papers_data = papers
        self.all_papers_cache = list(papers)
        self.paper_details_map = paper_details_map or {}
        self.paper_list.clear()
        self.lbl_list_title.setText("RETRIEVED PUBLICATIONS")
        self.lbl_paper_count.setText(f"{len(papers)} paper{'s' if len(papers) != 1 else ''}")

        if not papers:
            self.lbl_paper_title.setText("No literature retrieved yet.")
            self.lbl_provider_badge.setText("READY")
            self.lbl_authors.setText("Run the research workflow to search PubMed, OpenAlex, arXiv, and the web.")
            self.lbl_url.setText("")
            self.txt_abstract.setText("")
            self.txt_methodology.setText("")
            self.txt_tables.setText("")
            self._clear_evidence()
            return

        for paper in papers:
            title = paper.get("title", "Untitled")
            authors = ", ".join((paper.get("authors") or [])[:2])
            ext_id = str(paper.get("external_id", ""))
            prov = paper.get("provenance", {})
            provider = prov.get("provider") or ("PubMed" if "PMID" in ext_id else ("OpenAlex" if "openalex" in ext_id else ("arXiv" if "arxiv" in ext_id else "Web Search")))

            _, _, badge_text = SOURCE_BADGES.get(provider, ("#cbd5e1", "#334155", f"🏷️ {provider}"))
            item = QListWidgetItem(f"{badge_text}\n{title}\n👥 {authors}")
            item.setData(Qt.UserRole, paper)
            self.paper_list.addItem(item)

        if self.paper_list.count() > 0:
            self.paper_list.setCurrentRow(0)

    def _on_search_clicked(self) -> None:
        query = self.input_search.text().strip()
        if not query:
            self._on_reset_search()
            return

        # Vector search across in-memory vector store
        year_min = self._parse_year_min()
        min_cit = self._parse_min_citations()
        sec_type = self._parse_section_type()
        journal = self._parse_source_filter()

        results = global_vector_store.search(
            query=query,
            year_min=year_min,
            min_citations=min_cit,
            journal=journal,
            section_type=sec_type,
            limit=20,
        )

        self.paper_list.clear()
        self.lbl_list_title.setText(f"VECTOR SEARCH RESULTS (\"{query[:20]}\")")
        self.lbl_paper_count.setText(f"{len(results)} matches")

        if not results:
            item = QListWidgetItem("No vector matches found.\nTry broadening search filters.")
            self.paper_list.addItem(item)
            return

        for r in results:
            sim_badge = f"🎯 {r['similarity_percentage']} match | [{r['section_type']}]"
            title = r.get("paper_title", "Untitled")
            heading = r.get("heading", "")
            item = QListWidgetItem(f"{sim_badge}\n{title}\n📌 {heading}")
            # Map chunk to paper
            matched_paper = next((p for p in self.all_papers_cache if str(p.get("external_id")) == r.get("paper_id") or p.get("title") == title), None)
            if not matched_paper:
                matched_paper = {
                    "external_id": r.get("paper_id"),
                    "title": title,
                    "abstract": r.get("text"),
                    "url": "",
                    "provenance": {"provider": r.get("journal", "Vector Store")},
                }
            item.setData(Qt.UserRole, matched_paper)
            self.paper_list.addItem(item)

        if self.paper_list.count() > 0:
            self.paper_list.setCurrentRow(0)

    def _on_reset_search(self) -> None:
        self.input_search.clear()
        self.combo_year.setCurrentIndex(0)
        self.combo_source.setCurrentIndex(0)
        self.combo_section.setCurrentIndex(0)
        self.combo_citations.setCurrentIndex(0)
        self.set_papers(self.all_papers_cache, self.paper_details_map)

    def _on_filter_changed(self) -> None:
        if self.input_search.text().strip():
            self._on_search_clicked()

    def _parse_year_min(self) -> int | None:
        text = self.combo_year.currentText()
        if "2024" in text:
            return 2024
        if "2022" in text:
            return 2022
        if "2020" in text:
            return 2020
        if "2018" in text:
            return 2018
        return None

    def _parse_min_citations(self) -> int | None:
        text = self.combo_citations.currentText()
        if "50" in text:
            return 50
        if "25" in text:
            return 25
        if "10" in text:
            return 10
        return None

    def _parse_section_type(self) -> str | None:
        text = self.combo_section.currentText()
        if "Methodology" in text:
            return "METHODOLOGY"
        if "Tables" in text:
            return "RESULTS_TABLE"
        if "Figure" in text:
            return "FIGURE_CAPTION"
        if "Abstract" in text:
            return "ABSTRACT"
        return None

    def _parse_source_filter(self) -> str | None:
        text = self.combo_source.currentText()
        if "PubMed" in text:
            return "PubMed"
        if "OpenAlex" in text:
            return "OpenAlex"
        if "arXiv" in text:
            return "arXiv"
        if "Web" in text:
            return "Web"
        return None

    def _on_paper_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if not current:
            return
        paper = current.data(Qt.UserRole)
        if not paper:
            return

        paper_id = str(paper.get("id", ""))
        detail = self.paper_details_map.get(paper_id, paper)

        title = detail.get("title", "Untitled")
        authors = ", ".join(detail.get("authors") or [])
        url = detail.get("url", "")
        abstract = detail.get("abstract", "")
        evidence_list = detail.get("evidence", [])
        ext_id = str(detail.get("external_id", ""))
        prov = detail.get("provenance", {})

        provider = prov.get("provider") or ("PubMed" if "PMID" in ext_id else ("OpenAlex" if "openalex" in ext_id else ("arXiv" if "arxiv" in ext_id else "Web Search")))
        fg, bg, badge_text = SOURCE_BADGES.get(provider, ("#cbd5e1", "#334155", provider))

        self.lbl_paper_title.setText(title)
        self.lbl_provider_badge.setText(badge_text)
        self.lbl_provider_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 5px; background: {bg}; color: {fg};"
        )
        self.lbl_authors.setText(f"Authors: {authors}" if authors else "")
        self.lbl_url.setText(f'<a href="{url}" style="color: #38bdf8; text-decoration: none; font-weight: 700;">🌐 View Original PDF / Paper ↗</a>' if url else "")
        self.txt_abstract.setText(abstract or "No abstract text available.")

        # Extract structured sections for methodology and tables
        retrieved_obj = RetrievedPaper(
            external_id=ext_id,
            title=title,
            abstract=abstract,
            authors=detail.get("authors") or [],
            published_at=None,
            url=url,
            source_provider=provider,
        )
        sections = PDFSectionExtractor.extract_from_paper(retrieved_obj)

        meth_sec = next((s for s in sections if s.section_type == "METHODOLOGY"), None)
        self.txt_methodology.setText(f"### {meth_sec.heading}\n\n{meth_sec.content}" if meth_sec else "No methodology section available.")

        table_sec = next((s for s in sections if s.section_type == "RESULTS_TABLE"), None)
        fig_sec = next((s for s in sections if s.section_type == "FIGURE_CAPTION"), None)
        tables_content = ""
        if table_sec:
            tables_content += f"### {table_sec.heading}\n\n```\n{table_sec.content}\n```\n\n"
        if fig_sec:
            tables_content += f"### {fig_sec.heading}\n\n{fig_sec.content}\n"
        self.txt_tables.setText(tables_content or "No extracted tables or figures available.")

        # Populate Verifiable Evidence & Vector Chunks Tab
        self._clear_evidence()
        if evidence_list:
            for ev in evidence_list:
                box = QFrame()
                box.setStyleSheet("""
                    QFrame {
                        background-color: #0b1526;
                        border-left: 3px solid #3b82f6;
                        border-radius: 6px;
                        padding: 8px 10px;
                    }
                """)
                bl = QVBoxLayout(box)
                bl.setContentsMargins(6, 4, 6, 4)
                bl.setSpacing(2)
                loc_lbl = QLabel(f"📍 {ev.get('locator', 'N/A')} | Kind: {ev.get('kind', 'EVIDENCE')}")
                loc_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #60a5fa;")
                text_lbl = QLabel(f"\"{ev.get('text', '')}\"")
                text_lbl.setWordWrap(True)
                text_lbl.setStyleSheet("font-size: 12px; color: #e2e8f0; line-height: 1.4;")
                bl.addWidget(loc_lbl)
                bl.addWidget(text_lbl)
                self.evidence_layout.addWidget(box)
        else:
            # Fallback to display extracted section locators as vector chunks
            for sec in sections:
                box = QFrame()
                box.setStyleSheet("""
                    QFrame {
                        background-color: #0b1526;
                        border-left: 3px solid #10b981;
                        border-radius: 6px;
                        padding: 8px 10px;
                    }
                """)
                bl = QVBoxLayout(box)
                bl.setContentsMargins(6, 4, 6, 4)
                bl.setSpacing(2)
                loc_lbl = QLabel(f"📍 {sec.locator} | Section: {sec.section_type}")
                loc_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #34d399;")
                text_lbl = QLabel(f"\"{sec.content[:240]}...\"")
                text_lbl.setWordWrap(True)
                text_lbl.setStyleSheet("font-size: 11px; color: #e2e8f0;")
                bl.addWidget(loc_lbl)
                bl.addWidget(text_lbl)
                self.evidence_layout.addWidget(box)

    def _clear_evidence(self) -> None:
        while self.evidence_layout.count() > 0:
            item = self.evidence_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
