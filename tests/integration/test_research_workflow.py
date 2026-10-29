from __future__ import annotations

from uuid import UUID
from sqlalchemy import select

from app.api.dependencies import AppServices
from app.storage.models import Critique, Experiment, Hypothesis, ProvenanceLink, Result


def test_bounded_research_workflow_persists_provenance(client, services: AppServices) -> None:
    create_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Optimization budget study",
            "research_question": "Does a longer optimization budget improve held-out accuracy?",
            "objective": "Demonstrate the audited vertical slice.",
        },
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    task_response = client.post(f"/api/v1/projects/{project_id}/research?wait=true")
    assert task_response.status_code == 202
    assert task_response.json()["status"] == "COMPLETED"

    hypotheses = client.get(f"/api/v1/projects/{project_id}/hypotheses")
    assert hypotheses.status_code == 200
    assert len(hypotheses.json()) == 1
    assert hypotheses.json()[0]["novelty_estimate"] in {"insufficient_evidence", "moderate_novelty", "moderate", "high"}

    papers_response = client.get(f"/api/v1/papers?project_id={project_id}")
    assert papers_response.status_code == 200
    papers_data = papers_response.json()
    assert len(papers_data) >= 1
    first_paper_id = papers_data[0]["id"]

    paper_detail_response = client.get(f"/api/v1/papers/{first_paper_id}")
    assert paper_detail_response.status_code == 200
    paper_detail = paper_detail_response.json()
    assert paper_detail["id"] == first_paper_id
    assert paper_detail["external_id"] == "fixture-001"
    assert paper_detail["authors"] == ["Test Author"]
    assert paper_detail["url"] == "https://example.invalid/papers/fixture-001"
    assert "abstract" in paper_detail
    assert len(paper_detail["evidence"]) >= 1

    with services.session_factory() as session:
        experiment = session.scalar(select(Experiment))
        result = session.scalar(select(Result))
        critique = session.scalar(select(Critique))
        links = session.scalars(select(ProvenanceLink)).all()

    assert experiment is not None
    assert result is not None
    assert critique is not None
    assert critique.outcome in {"ACCEPT_WITH_LIMITATIONS", "NEEDS_REVISION", "REJECT"}
    assert any(link.relationship == "MOTIVATED_BY" for link in links)
    assert any(link.relationship == "MEASURED_BY" for link in links)


def test_delete_project_cascades_all_entities(client, services: AppServices) -> None:
    # 1. Create project & run workflow
    create_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Project to Delete",
            "research_question": "Does deletion properly remove all downstream records?",
            "objective": "Test cascading deletion.",
        },
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    task_response = client.post(f"/api/v1/projects/{project_id}/research?wait=true")
    assert task_response.status_code == 202

    # 2. Delete project
    del_resp = client.delete(f"/api/v1/projects/{project_id}")
    assert del_resp.status_code == 204

    # 3. Confirm 404
    get_resp = client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 404

    # 4. Verify no dangling experiments or hypotheses for this project in DB
    with services.session_factory() as session:
        exp = session.scalar(select(Experiment).where(Experiment.project_id == UUID(project_id)))
        hyp = session.scalar(select(Hypothesis).where(Hypothesis.project_id == UUID(project_id)))
        assert exp is None
        assert hyp is None



