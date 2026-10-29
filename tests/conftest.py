from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import AppServices, build_services
from app.core.config import Settings
from app.execution.sandbox import DeterministicSandboxDouble
from app.literature.providers import LiteratureSearchResult, RetrievedPaper
from app.main import create_app
from app.storage.models import Base


class FixtureLiteratureProvider:
    """Clearly labelled test provider; it is not wired in production."""

    def search(self, query: str) -> LiteratureSearchResult:
        return LiteratureSearchResult(
            provider_name="fixture-literature-provider",
            query=query,
            request_url="https://example.invalid/test-fixture",
            raw_payload={"fixture": "true", "entry_count": 1},
            papers=[
                RetrievedPaper(
                    external_id="fixture-001",
                    title="A fixture paper about controlled optimization experiments",
                    abstract=(
                        "This fixture abstract describes a controlled machine-learning experiment. "
                        "It reports that optimization settings can affect held-out accuracy."
                    ),
                    authors=["Test Author"],
                    published_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    url="https://example.invalid/papers/fixture-001",
                )
            ],
        )


@pytest.fixture()
def services(tmp_path) -> AppServices:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'research.db'}",
        artifact_root=tmp_path / "artifacts",
        sandbox_volume="test_artifacts",
    )
    built = build_services(
        settings,
        literature_provider=FixtureLiteratureProvider(),
        sandbox_runner=DeterministicSandboxDouble(),
    )
    Base.metadata.create_all(built.engine)
    yield built
    built.engine.dispose()


@pytest.fixture()
def client(services: AppServices) -> TestClient:
    with TestClient(create_app(services)) as test_client:
        yield test_client

