from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import AppServices, get_services, get_session
from app.storage.database import delete_project_cascade
from app.schemas.api import (
    CreateExperimentRequest,
    CreateProjectRequest,
    ExperimentResponse,
    HypothesisResponse,
    ProjectResponse,
    ProvenanceResponse,
    ResultResponse,
    TaskResponse,
)
from app.storage.models import (
    Artifact,
    Critique,
    Evidence,
    Experiment,
    ExperimentRun,
    Hypothesis,
    Metric,
    Paper,
    ProvenanceLink,
    ResearchProject,
    ResearchQuestion,
    ResearchTask,
    Result,
    Source,
)
from app.experiments.catalog import ExperimentCatalog
from app.literature.pdf_reader import PDFSectionExtractor
from app.literature.providers import RetrievedPaper
from app.literature.vector_store import global_vector_store
from app.reporting.manuscript_generator import generate_manuscript

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: CreateProjectRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    existing = session.scalar(select(ResearchProject).where(ResearchProject.name == payload.name))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this name already exists.",
        )
    project = ResearchProject(
        name=payload.name,
        objective=payload.objective,
        provenance={"creation_method": "api", "claims_status": "NO_CLAIMS_YET"},
    )
    session.add(project)
    session.flush()
    question = ResearchQuestion(
        project_id=project.id,
        text=payload.research_question,
        provenance={"creation_method": "api", "project_id": str(project.id)},
    )
    session.add(question)
    session.flush()
    return ProjectResponse(
        id=project.id,
        name=project.name,
        status=project.status,
        research_question=question.text,
        objective=project.objective,
        created_at=project.created_at,
    )


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectResponse]:
    projects = session.scalars(select(ResearchProject).order_by(ResearchProject.created_at.desc())).all()
    results = []
    for project in projects:
        question = session.scalar(select(ResearchQuestion).where(ResearchQuestion.project_id == project.id))
        results.append(
            ProjectResponse(
                id=project.id,
                name=project.name,
                status=project.status,
                research_question=question.text if question else "",
                objective=project.objective,
                created_at=project.created_at,
            )
        )
    return results


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _get_project_or_404(session, project_id)
    question = _question_for_project(session, project_id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        status=project.status,
        research_question=question.text,
        objective=project.objective,
        created_at=project.created_at,
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_project(project_id: UUID, session: Session = Depends(get_session)) -> Response:
    deleted = delete_project_cascade(session, project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects/{project_id}/manuscript")
def get_project_manuscript(
    project_id: UUID,
    format: str = Query(default="all", description="Format to return: markdown, latex, html, or all"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    project = _get_project_or_404(session, project_id)
    payload = generate_manuscript(session, project.id)
    if format == "markdown":
        return {"project_id": str(project.id), "markdown": payload["markdown"]}
    elif format == "latex":
        return {"project_id": str(project.id), "latex": payload["latex"]}
    elif format == "html":
        return {"project_id": str(project.id), "html": payload["html"]}
    return payload


@router.post("/projects/{project_id}/research", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def start_research(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    wait: bool = Query(default=False, description="Run the bounded workflow before responding."),
    iterations: int = Query(default=1, ge=1, le=5, description="Number of autonomous discovery iterations (1-5)."),
    session: Session = Depends(get_session),
    services: AppServices = Depends(get_services),
) -> TaskResponse:
    project = _get_project_or_404(session, project_id)
    if project.status == "RUNNING":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project already has an active task.")
    task = ResearchTask(
        project_id=project_id,
        trace_id=uuid4(),
        provenance={"dispatch": "in_process_bounded_v1", "max_iterations": iterations},
    )
    session.add(task)
    session.flush()
    task_id = task.id
    session.commit()
    if wait:
        services.orchestrator.run_task(task_id)
        session.refresh(task)
    else:
        background_tasks.add_task(services.orchestrator.run_task, task_id)
    return _task_response(task)


@router.get("/projects/{project_id}/status", response_model=TaskResponse)
def get_project_status(project_id: UUID, session: Session = Depends(get_session)) -> TaskResponse:
    _get_project_or_404(session, project_id)
    task = session.scalar(
        select(ResearchTask)
        .where(ResearchTask.project_id == project_id)
        .order_by(ResearchTask.created_at.desc())
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No research task exists for this project.")
    return _task_response(task)


@router.get("/projects/{project_id}/hypotheses", response_model=list[HypothesisResponse])
def list_hypotheses(project_id: UUID, session: Session = Depends(get_session)) -> list[HypothesisResponse]:
    _get_project_or_404(session, project_id)
    records = session.scalars(
        select(Hypothesis).where(Hypothesis.project_id == project_id).order_by(Hypothesis.created_at.asc())
    ).all()
    return [
        HypothesisResponse(
            id=record.id,
            statement=record.statement,
            mechanism=record.mechanism,
            confidence=record.confidence,
            novelty_estimate=record.novelty_estimate,
            supporting_evidence_ids=[UUID(identifier) for identifier in record.supporting_evidence_ids],
        )
        for record in records
    ]


@router.get("/projects/{project_id}/evolution")
def get_hypothesis_evolution(
    project_id: UUID, session: Session = Depends(get_session)
) -> dict[str, Any]:
    project = _get_project_or_404(session, project_id)
    hypotheses = session.scalars(
        select(Hypothesis).where(Hypothesis.project_id == project_id).order_by(Hypothesis.created_at.asc())
    ).all()

    iterations_data: list[dict[str, Any]] = []
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

        iteration_num = int((hyp.provenance or {}).get("iteration", idx))
        metrics_dict: dict[str, float] = {}
        if run:
            metric_records = session.scalars(select(Metric).where(Metric.run_id == run.id)).all()
            metrics_dict = {m.name: m.value for m in metric_records}

        iterations_data.append({
            "iteration": iteration_num,
            "hypothesis_id": str(hyp.id),
            "statement": hyp.statement,
            "mechanism": hyp.mechanism,
            "assumptions": hyp.assumptions or [],
            "predictions": hyp.predictions or [],
            "confidence": hyp.confidence,
            "novelty_estimate": hyp.novelty_estimate,
            "testability_score": hyp.testability_score,
            "estimated_cost": hyp.estimated_cost,
            "provenance": hyp.provenance,
            "experiment_id": str(exp.id) if exp else None,
            "run_id": str(run.id) if run else None,
            "metrics": metrics_dict,
            "statistics": result.statistics if result else {},
            "critique_outcome": critique.outcome if critique else None,
            "critique_findings": critique.findings if critique else [],
            "created_at": hyp.created_at.isoformat() if hyp.created_at else None,
        })

    return {
        "project_id": str(project.id),
        "total_iterations": len(iterations_data),
        "completed": project.status == "COMPLETED",
        "evolution_tree": iterations_data,
    }


@router.get("/papers")
def list_papers(project_id: UUID, session: Session = Depends(get_session)) -> list[dict[str, object]]:
    _get_project_or_404(session, project_id)
    papers = session.scalars(select(Paper).where(Paper.project_id == project_id)).all()
    return [
        {
            "id": str(paper.id),
            "external_id": paper.external_id,
            "title": paper.title,
            "authors": paper.authors,
            "url": paper.url,
            "provenance": paper.provenance,
        }
        for paper in papers
    ]


@router.get("/papers/{paper_id}")
def get_paper(paper_id: UUID, session: Session = Depends(get_session)) -> dict[str, object]:
    paper = session.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")
    evidence = session.scalars(select(Evidence).where(Evidence.paper_id == paper_id)).all()
    return {
        "id": str(paper.id),
        "external_id": paper.external_id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors,
        "url": paper.url,
        "evidence": [
            {"id": str(item.id), "text": item.text, "locator": item.locator, "kind": item.evidence_kind}
            for item in evidence
        ],
        "provenance": paper.provenance,
    }


@router.get("/literature/search/semantic")
def search_literature_semantic(
    query: str = Query(..., min_length=1),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    min_citations: int | None = Query(None),
    journal: str | None = Query(None),
    section_type: str | None = Query(None),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
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


@router.get("/papers/{paper_id}/sections")
def get_paper_sections(paper_id: UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    paper = session.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")
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


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: UUID, session: Session = Depends(get_session)) -> ExperimentResponse:
    experiment = session.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return _experiment_response(experiment)


@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: CreateExperimentRequest, session: Session = Depends(get_session)
) -> ExperimentResponse:
    _get_project_or_404(session, payload.project_id)
    hypothesis = session.get(Hypothesis, payload.hypothesis_id)
    if hypothesis is None or hypothesis.project_id != payload.project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hypothesis not found for this project.")
    planned = ExperimentCatalog().build_for_hypothesis(hypothesis.statement)
    experiment = Experiment(
        project_id=payload.project_id,
        hypothesis_id=payload.hypothesis_id,
        template_id=planned.template_id,
        template_revision=planned.template_revision,
        kind=planned.specification["classification"],
        specification=planned.specification,
        provenance={"planning_method": "api_registered_template_catalog_v1"},
    )
    session.add(experiment)
    session.flush()
    session.add(
        ProvenanceLink(
            child_type="Experiment",
            child_id=experiment.id,
            parent_type="Hypothesis",
            parent_id=hypothesis.id,
            relationship="TESTS",
            locator=None,
        )
    )
    return _experiment_response(experiment)


@router.post("/experiments/{experiment_id}/run", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def run_experiment(
    experiment_id: UUID,
    background_tasks: BackgroundTasks,
    wait: bool = Query(default=False),
    session: Session = Depends(get_session),
    services: AppServices = Depends(get_services),
) -> TaskResponse:
    experiment = session.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    task = ResearchTask(
        project_id=experiment.project_id,
        trace_id=uuid4(),
        stage="PLANNING_EXPERIMENT",
        provenance={"dispatch": "in_process_experiment_only_v1", "experiment_id": str(experiment_id)},
    )
    session.add(task)
    session.flush()
    task_id = task.id
    session.commit()
    if wait:
        services.orchestrator.run_experiment_task(task_id, experiment_id)
        session.refresh(task)
    else:
        background_tasks.add_task(services.orchestrator.run_experiment_task, task_id, experiment_id)
    return _task_response(task)


@router.get("/experiments/{experiment_id}/results", response_model=ResultResponse)
def get_experiment_results(experiment_id: UUID, session: Session = Depends(get_session)) -> ResultResponse:
    run = session.scalar(
        select(ExperimentRun)
        .where(ExperimentRun.experiment_id == experiment_id)
        .order_by(ExperimentRun.created_at.desc())
    )
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No experiment run exists.")
    if run.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Experiment run failed: {run.stderr or 'Execution error'}",
        )
    result = session.scalar(select(Result).where(Result.run_id == run.id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Experiment run has no analysis yet.")
    critique = session.scalar(select(Critique).where(Critique.run_id == run.id))
    metric_records = session.scalars(select(Metric).where(Metric.run_id == run.id)).all()
    metrics = {metric.name: metric.value for metric in metric_records}
    metrics["mean_difference"] = float(result.statistics["mean_difference"])
    return ResultResponse(
        run_id=run.id,
        status=run.status,
        metrics=metrics,
        statistics=result.statistics,
        critique_outcome=critique.outcome if critique else None,
    )


@router.get("/knowledge")
def get_knowledge(project_id: UUID, session: Session = Depends(get_session)) -> dict[str, object]:
    """Expose the first provenance-derived graph; graph DB traversal is a later milestone."""

    _get_project_or_404(session, project_id)
    paper_ids = session.scalars(select(Paper.id).where(Paper.project_id == project_id)).all()
    hypothesis_ids = session.scalars(select(Hypothesis.id).where(Hypothesis.project_id == project_id)).all()
    experiment_ids = session.scalars(select(Experiment.id).where(Experiment.project_id == project_id)).all()
    permitted = {str(item) for item in [*paper_ids, *hypothesis_ids, *experiment_ids]}
    links = session.scalars(select(ProvenanceLink)).all()
    edges = [
        {
            "source": str(link.parent_id),
            "target": str(link.child_id),
            "type": link.relationship,
        }
        for link in links
        if str(link.child_id) in permitted or str(link.parent_id) in permitted
    ]
    nodes = [
        *[{"id": str(item), "type": "Paper"} for item in paper_ids],
        *[{"id": str(item), "type": "Hypothesis"} for item in hypothesis_ids],
        *[{"id": str(item), "type": "Experiment"} for item in experiment_ids],
    ]
    return {"nodes": nodes, "edges": edges, "limitations": ["Provenance graph only; no contradiction inference yet."]}


@router.get("/provenance/{record_id}", response_model=ProvenanceResponse)
def get_provenance(record_id: UUID, session: Session = Depends(get_session)) -> ProvenanceResponse:
    candidates: list[tuple[str, object | None]] = [
        ("ResearchProject", session.get(ResearchProject, record_id)),
        ("Source", session.get(Source, record_id)),
        ("Paper", session.get(Paper, record_id)),
        ("Evidence", session.get(Evidence, record_id)),
        ("Hypothesis", session.get(Hypothesis, record_id)),
        ("Experiment", session.get(Experiment, record_id)),
        ("ExperimentRun", session.get(ExperimentRun, record_id)),
        ("Result", session.get(Result, record_id)),
        ("Critique", session.get(Critique, record_id)),
        ("Artifact", session.get(Artifact, record_id)),
    ]
    match = next(((record_type, record) for record_type, record in candidates if record is not None), None)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditable record not found.")
    record_type, record = match
    parents = session.scalars(
        select(ProvenanceLink).where(
            ProvenanceLink.child_type == record_type, ProvenanceLink.child_id == record_id
        )
    ).all()
    return ProvenanceResponse(
        record_id=record_id,
        record_type=record_type,
        provenance=record.provenance,  # type: ignore[union-attr]
        parents=[
            {
                "record_type": link.parent_type,
                "record_id": str(link.parent_id),
                "relationship": link.relationship,
                "locator": link.locator,
            }
            for link in parents
        ],
    )


def _get_project_or_404(session: Session, project_id: UUID) -> ResearchProject:
    project = session.get(ResearchProject, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _question_for_project(session: Session, project_id: UUID) -> ResearchQuestion:
    question = session.scalar(select(ResearchQuestion).where(ResearchQuestion.project_id == project_id))
    if question is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project has no research question.")
    return question


def _task_response(task: ResearchTask) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        status=task.status,
        trace_id=task.trace_id,
        error_code=task.error_code,
        error_message=task.error_message,
    )


def _experiment_response(experiment: Experiment) -> ExperimentResponse:
    return ExperimentResponse(
        id=experiment.id,
        project_id=experiment.project_id,
        hypothesis_id=experiment.hypothesis_id,
        template_id=experiment.template_id,
        kind=experiment.kind,
        specification=experiment.specification,
    )
