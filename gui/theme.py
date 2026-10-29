"""Scientific Research Workstation Design System and Dark Theme Stylesheet for AI Research Scientist GUI."""

from __future__ import annotations

# Scientific semantic color tokens
COLORS = {
    "bg_root": "#070b12",
    "bg_surface": "#0c1322",
    "bg_panel": "#10192c",
    "bg_card": "#131f36",
    "bg_card_hover": "#172642",
    "bg_input": "#080e1a",
    "border_subtle": "#162238",
    "border_medium": "#1e304f",
    "border_active": "#3b82f6",
    "text_primary": "#f8fafc",
    "text_secondary": "#cbd5e1",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",
    "accent_blue": "#3b82f6",
    "accent_cyan": "#06b6d4",
    "accent_green": "#10b981",
    "accent_amber": "#f59e0b",
    "accent_red": "#ef4444",
    "accent_purple": "#8b5cf6",
}

DARK_STYLESHEET = """
/* Global Reset & Base Typography */
QMainWindow, QDialog {
    background-color: #070b12;
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif;
    font-size: 12px;
}

QWidget {
    background-color: transparent;
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif;
}

/* Custom Slim Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 2px 0px;
}
QScrollBar::handle:vertical {
    background: #1e304f;
    min-height: 24px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #3b82f6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px 2px;
}
QScrollBar::handle:horizontal {
    background: #1e304f;
    min-width: 24px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #3b82f6;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    width: 0px;
}

/* Three-Region Top Command Bar */
#TopBarWidget {
    background-color: #090e1a;
    border-bottom: 1px solid #162238;
}

/* Left Sidebar & Workspace Nav */
#SidebarWidget {
    background-color: #090e1a;
    border-right: 1px solid #162238;
}

/* Project Header */
#ProjectHeaderWidget {
    background-color: #0c1322;
    border: 1px solid #1a2942;
    border-radius: 8px;
}

/* Scientific Workstation Cards & Containers */
QFrame.workstation-card {
    background-color: #0c1322;
    border: 1px solid #1a2942;
    border-radius: 8px;
}

QFrame.workstation-card-elevated {
    background-color: #10192c;
    border: 1px solid #1e304f;
    border-radius: 8px;
}

QFrame.panel-container {
    background-color: #090e1a;
    border: 1px solid #162238;
    border-radius: 8px;
}

/* PushButtons */
QPushButton {
    background-color: #10192c;
    color: #cbd5e1;
    border: 1px solid #1e304f;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #172642;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0c1322;
}

QPushButton:disabled {
    background-color: #080d16;
    color: #475569;
    border-color: #131d2e;
}

/* Specialized Buttons */
QPushButton.primary-btn {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
}
QPushButton.primary-btn:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}

QPushButton.success-btn {
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #10b981;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
}
QPushButton.success-btn:hover {
    background-color: #047857;
    border-color: #34d399;
}

QPushButton.danger-btn {
    background-color: #7f1d1d;
    color: #fca5a5;
    border: 1px solid #991b1b;
    border-radius: 6px;
    font-weight: 600;
    font-size: 11px;
}
QPushButton.danger-btn:hover {
    background-color: #991b1b;
    color: #ffffff;
    border-color: #ef4444;
}

QPushButton.nav-item {
    text-align: left;
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton.nav-item:hover {
    background-color: #10192c;
    color: #f1f5f9;
    border-color: #1e304f;
}
QPushButton.nav-item:checked, QPushButton.nav-item-active {
    background-color: #172642;
    color: #60a5fa;
    border: 1px solid #2563eb;
    font-weight: 700;
}

/* Inputs & Editors */
QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {
    background-color: #080e1a;
    color: #f8fafc;
    border: 1px solid #1a2942;
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: #2563eb;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #0c1322;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #475569;
}

/* Lists */
QListWidget {
    background-color: transparent;
    border: none;
    padding: 2px;
    outline: none;
}

QListWidget::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #334155;
    border-radius: 4px;
    background: #090e1a;
    margin-right: 6px;
}

QListWidget::indicator:checked {
    background-color: #2563eb;
    border: 1px solid #60a5fa;
}

QListWidget::item {
    background-color: #0c1322;
    border: 1px solid #162238;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 4px;
    color: #e2e8f0;
}

QListWidget::item:hover {
    background-color: #10192c;
    border-color: #1e304f;
}

QListWidget::item:selected {
    background-color: #172642;
    border: 1px solid #3b82f6;
    color: #ffffff;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #080e1a;
    border: 1px solid #162238;
    gridline-color: #121c2e;
    border-radius: 6px;
    color: #e2e8f0;
    selection-background-color: #172642;
    selection-color: #60a5fa;
    outline: none;
    font-size: 11px;
}

QHeaderView::section {
    background-color: #0c1322;
    color: #94a3b8;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #1a2942;
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Modern Tab Widget */
QTabWidget::pane {
    border: 1px solid #162238;
    background: #080e1a;
    border-radius: 8px;
    top: 2px;
    padding: 4px;
}

QTabBar {
    background: transparent;
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background: #0c1322;
    color: #94a3b8;
    border: 1px solid #162238;
    border-radius: 6px;
    padding: 6px 14px;
    margin-right: 4px;
    margin-bottom: 2px;
    font-weight: 600;
    font-size: 11px;
}

QTabBar::tab:hover {
    background: #10192c;
    color: #cbd5e1;
    border-color: #1e304f;
}

QTabBar::tab:selected {
    background-color: #172642;
    color: #60a5fa;
    border: 1px solid #3b82f6;
    font-weight: 700;
}

/* Splitter */
QSplitter::handle {
    background-color: #121c2e;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #3b82f6;
}

/* Progress Bars */
QProgressBar {
    border: 1px solid #1a2942;
    border-radius: 4px;
    background-color: #080e1a;
    height: 10px;
    text-align: center;
    color: #f8fafc;
    font-size: 9px;
    font-weight: 700;
}
QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 3px;
}
"""

STATUS_COLORS = {
    "CREATED": ("#38bdf8", "#082f49"),
    "QUEUED": ("#fbbf24", "#451a03"),
    "RUNNING": ("#60a5fa", "#172554"),
    "COMPLETED": ("#34d399", "#064e3b"),
    "FAILED": ("#f87171", "#450a0a"),
    "ACCEPT": ("#34d399", "#064e3b"),
    "ACCEPT_WITH_LIMITATIONS": ("#34d399", "#064e3b"),
    "NEEDS_REVISION": ("#fbbf24", "#451a03"),
    "REJECT": ("#f87171", "#450a0a"),
    "PASS": ("#34d399", "#064e3b"),
    "WARNING": ("#fbbf24", "#451a03"),
    "FAIL": ("#f87171", "#450a0a"),
    "INCONCLUSIVE": ("#94a3b8", "#1e293b"),
}

SOURCE_QUALITY_BADGES = {
    "PEER-REVIEWED": ("#34d399", "#064e3b", "PEER-REVIEWED"),
    "PREPRINT": ("#60a5fa", "#172554", "PREPRINT"),
    "DATABASE": ("#c084fc", "#4c1d95", "DATABASE"),
    "REVIEW": ("#38bdf8", "#082f49", "REVIEW"),
    "GENERAL WEB": ("#fbbf24", "#451a03", "GENERAL WEB"),
    "REFERENCE": ("#94a3b8", "#1e293b", "REFERENCE"),
}
