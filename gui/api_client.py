"""HTTP API Client and asynchronous worker threads for GUI."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import httpx
from PySide6.QtCore import QObject, QThread, Signal


class ResearchApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def healthcheck(self) -> dict[str, Any]:
        resp = self.client.get("/healthz")
        resp.raise_for_status()
        return resp.json()

    def create_project(self, name: str, research_question: str, objective: str = "") -> dict[str, Any]:
        payload = {
            "name": name,
            "research_question": research_question,
            "objective": objective,
        }
        resp = self.client.post("/api/v1/projects", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_project(self, project_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get(f"/api/v1/projects/{project_id}")
        resp.raise_for_status()
        return resp.json()

    def list_projects(self) -> list[dict[str, Any]]:
        resp = self.client.get("/api/v1/projects")
        resp.raise_for_status()
        return resp.json()

    def delete_project(self, project_id: str | UUID) -> bool:
        resp = self.client.delete(f"/api/v1/projects/{project_id}")
        resp.raise_for_status()
        return True

    def get_project_status(self, project_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get(f"/api/v1/projects/{project_id}/status")
        resp.raise_for_status()
        return resp.json()

    def start_research(self, project_id: str | UUID, wait: bool = True, iterations: int = 2) -> dict[str, Any]:
        resp = self.client.post(
            f"/api/v1/projects/{project_id}/research",
            params={"wait": str(wait).lower(), "iterations": iterations},
            timeout=180.0,
        )
        resp.raise_for_status()
        return resp.json()

    def list_hypotheses(self, project_id: str | UUID) -> list[dict[str, Any]]:
        resp = self.client.get(f"/api/v1/projects/{project_id}/hypotheses")
        resp.raise_for_status()
        return resp.json()

    def get_evolution(self, project_id: str | UUID) -> dict[str, Any]:
        try:
            resp = self.client.get(f"/api/v1/projects/{project_id}/evolution")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            from sqlalchemy import select

            from app.core.config import Settings
            from app.storage.database import create_database_engine, create_session_factory
            from app.storage.models import Critique, Experiment, ExperimentRun, Hypothesis, Metric, Result

            settings = Settings()
            engine = create_database_engine(settings.database_url)
            factory = create_session_factory(engine)
            with factory() as session:
                hypotheses = session.scalars(
                    select(Hypothesis).where(Hypothesis.project_id == UUID(str(project_id))).order_by(Hypothesis.created_at.asc())
                ).all()
                iterations_data = []
                for idx, hyp in enumerate(hypotheses, start=1):
                    exp = session.scalar(
                        select(Experiment).where(Experiment.hypothesis_id == hyp.id).order_by(Experiment.created_at.desc())
                    )
                    run = None
                    result = None
                    critique = None
                    if exp:
                        run = session.scalar(
                            select(ExperimentRun).where(ExperimentRun.experiment_id == exp.id).order_by(ExperimentRun.created_at.desc())
                        )
                        if run:
                            result = session.scalar(select(Result).where(Result.run_id == run.id))
                            critique = session.scalar(select(Critique).where(Critique.run_id == run.id))
                    iter_num = int((hyp.provenance or {}).get("iteration", idx))
                    metrics_dict: dict[str, float] = {}
                    if run:
                        metric_rows = session.scalars(select(Metric).where(Metric.run_id == run.id)).all()
                        metrics_dict = {m.name: m.value for m in metric_rows}

                    iterations_data.append({
                        "iteration": iter_num,
                        "hypothesis_id": str(hyp.id),
                        "statement": hyp.statement,
                        "mechanism": hyp.mechanism,
                        "assumptions": hyp.assumptions or [],
                        "predictions": hyp.predictions or [],
                        "confidence": hyp.confidence,
                        "novelty_estimate": hyp.novelty_estimate,
                        "testability_score": hyp.testability_score,
                        "estimated_cost": hyp.estimated_cost,
                        "experiment_id": str(exp.id) if exp else None,
                        "run_id": str(run.id) if run else None,
                        "metrics": metrics_dict,
                        "statistics": result.statistics if result else {},
                        "critique_outcome": critique.outcome if critique else None,
                        "critique_findings": critique.findings if critique else [],
                    })
                return {
                    "project_id": str(project_id),
                    "total_iterations": len(iterations_data),
                    "evolution_tree": iterations_data,
                }

    def list_papers(self, project_id: str | UUID) -> list[dict[str, Any]]:
        resp = self.client.get("/api/v1/papers", params={"project_id": str(project_id)})
        resp.raise_for_status()
        return resp.json()

    def get_paper(self, paper_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get(f"/api/v1/papers/{paper_id}")
        resp.raise_for_status()
        return resp.json()

    def get_paper_sections(self, paper_id: str | UUID) -> dict[str, Any]:
        try:
            resp = self.client.get(f"/api/v1/papers/{paper_id}/sections")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            from uuid import UUID
            from app.core.config import Settings
            from app.literature.pdf_reader import PDFSectionExtractor
            from app.literature.providers import RetrievedPaper
            from app.storage.database import create_database_engine, create_session_factory
            from app.storage.models import Paper

            settings = Settings()
            engine = create_database_engine(settings.database_url)
            factory = create_session_factory(engine)
            with factory() as session:
                paper = session.get(Paper, UUID(str(paper_id)))
                if not paper:
                    return {"sections": []}
                retrieved = RetrievedPaper(
                    external_id=paper.external_id,
                    title=paper.title,
                    abstract=paper.abstract,
                    authors=paper.authors or [],
                    published_at=paper.created_at,
                    url=paper.url,
                    source_provider=(paper.provenance or {}).get("source_provider", "arXiv"),
                )
                sections = PDFSectionExtractor.extract_from_paper(retrieved)
                return {
                    "paper_id": str(paper.id),
                    "external_id": paper.external_id,
                    "title": paper.title,
                    "total_sections": len(sections),
                    "sections": [
                        {
                            "section_type": sec.section_type,
                            "heading": sec.heading,
                            "content": sec.content,
                            "locator": sec.locator,
                            "page_number": sec.page_number,
                        }
                        for sec in sections
                    ],
                }

    def search_literature_semantic(
        self,
        query: str,
        year_min: int | None = None,
        year_max: int | None = None,
        min_citations: int | None = None,
        journal: str | None = None,
        section_type: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        try:
            params: dict[str, Any] = {"query": query, "limit": limit}
            if year_min is not None:
                params["year_min"] = year_min
            if year_max is not None:
                params["year_max"] = year_max
            if min_citations is not None:
                params["min_citations"] = min_citations
            if journal:
                params["journal"] = journal
            if section_type:
                params["section_type"] = section_type

            resp = self.client.get("/api/v1/literature/search/semantic", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            from app.literature.vector_store import global_vector_store
            results = global_vector_store.search(
                query=query,
                year_min=year_min,
                year_max=year_max,
                min_citations=min_citations,
                journal=journal,
                section_type=section_type,
                limit=limit,
            )
            return {
                "query": query,
                "total_results": len(results),
                "vector_store_chunks": global_vector_store.count(),
                "results": results,
            }

    def get_knowledge(self, project_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get("/api/v1/knowledge", params={"project_id": str(project_id)})
        resp.raise_for_status()
        return resp.json()

    def get_provenance(self, record_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get(f"/api/v1/provenance/{record_id}")
        resp.raise_for_status()
        return resp.json()

    def get_experiment(self, experiment_id: str | UUID) -> dict[str, Any]:
        try:
            resp = self.client.get(f"/api/v1/experiments/{experiment_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            from uuid import UUID
            from app.core.config import Settings
            from app.storage.database import create_database_engine, create_session_factory
            from app.storage.models import Experiment

            settings = Settings()
            engine = create_database_engine(settings.database_url)
            factory = create_session_factory(engine)
            with factory() as session:
                exp = session.get(Experiment, UUID(str(experiment_id)))
                if not exp:
                    return {}
                return {
                    "id": str(exp.id),
                    "project_id": str(exp.project_id),
                    "hypothesis_id": str(exp.hypothesis_id),
                    "template_id": exp.template_id,
                    "kind": exp.kind,
                    "specification": exp.specification or {},
                }

    def get_experiment_results(self, experiment_id: str | UUID) -> dict[str, Any]:
        resp = self.client.get(f"/api/v1/experiments/{experiment_id}/results")
        resp.raise_for_status()
        return resp.json()

    def get_manuscript(self, project_id: str | UUID, format: str = "all") -> dict[str, Any]:
        try:
            resp = self.client.get(f"/api/v1/projects/{project_id}/manuscript", params={"format": format})
            resp.raise_for_status()
            return resp.json()
        except Exception:
            # Fallback to local DB manuscript generator
            from app.core.config import Settings
            from app.storage.database import create_database_engine, create_session_factory
            from app.reporting.manuscript_generator import generate_manuscript

            settings = Settings()
            engine = create_database_engine(settings.database_url)
            factory = create_session_factory(engine)
            with factory() as session:
                return generate_manuscript(session, str(project_id))


class WorkflowWorker(QThread):
    """Executes the research workflow in a background thread without freezing the UI."""

    started_signal = Signal(str)
    stage_changed = Signal(str)
    completed_signal = Signal(dict)
    failed_signal = Signal(str)

    def __init__(self, client: ResearchApiClient, project_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.client = client
        self.project_id = project_id
        self._is_running = True

    def run(self) -> None:
        try:
            self.started_signal.emit(self.project_id)
            # Trigger workflow synchronously on the backend
            result = self.client.start_research(self.project_id, wait=True)
            if result.get("status") == "COMPLETED":
                self.completed_signal.emit(result)
            elif result.get("status") == "FAILED":
                err = result.get("error_message") or result.get("error_code") or "Unknown error"
                self.failed_signal.emit(f"Workflow failed: {err}")
            else:
                self.completed_signal.emit(result)
        except Exception as e:
            self.failed_signal.emit(f"Network / Execution Error: {e}")


class HealthMonitorWorker(QThread):
    """Background worker that periodically checks backend server health."""

    status_updated = Signal(bool, str)

    def __init__(self, client: ResearchApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.client = client
        self._is_running = True

    def run(self) -> None:
        while self._is_running:
            try:
                res = self.client.healthcheck()
                if res.get("status") == "ok":
                    self.status_updated.emit(True, "Online")
                else:
                    self.status_updated.emit(False, "Degraded")
            except Exception:
                self.status_updated.emit(False, "Offline")
            time.sleep(5)

    def stop(self) -> None:
        self._is_running = False
        self.wait(1000)
