"""PySide6 Desktop Application Entrypoint for Autonomous AI Research Scientist."""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from sqlalchemy import select

from app.core.config import Settings
from app.storage.database import create_database_engine, create_session_factory
from app.storage.models import ResearchProject, ResearchQuestion
from gui.main_window import MainWindow


def preload_projects(window: MainWindow) -> None:
    """Preload projects from the live API, or fallback to local database."""
    try:
        projects = window.api_client.list_projects()
        if projects:
            window.reload_projects_list()
            return
    except Exception:
        pass

    try:
        settings = Settings()
        engine = create_database_engine(settings.database_url)
        factory = create_session_factory(engine)
        with factory() as session:
            projects = session.scalars(select(ResearchProject).order_by(ResearchProject.created_at.desc())).all()
            for p in projects:
                q = session.scalar(select(ResearchQuestion).where(ResearchQuestion.project_id == p.id))
                payload = {
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "research_question": q.text if q else "",
                    "created_at": str(p.created_at),
                }
                window.add_project(payload)
    except Exception as err:
        print(f"[GUI] Note: Could not preload local DB projects: {err}")


def main() -> None:
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("Autonomous AI Research Scientist")
    app.setOrganizationName("AI Research Lab")

    window = MainWindow(api_url="http://127.0.0.1:8000")
    preload_projects(window)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
