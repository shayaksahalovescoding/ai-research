from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.dependencies import AppServices, build_services
from app.api.routes import router
from app.core.config import Settings


def create_app(services: AppServices | None = None) -> FastAPI:
    active_services = services or build_services(Settings())

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logging.basicConfig(
            level=active_services.settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        yield
        active_services.engine.dispose()

    application = FastAPI(
        title="Autonomous AI Research Scientist",
        version="0.1.0",
        description=(
            "An auditable, safety-conscious ML research workflow. Generated text and sandbox "
            "results are never treated as truth without their stored provenance."
        ),
        lifespan=lifespan,
    )
    application.state.services = active_services
    application.include_router(router, prefix="/api/v1", tags=["research"])

    @application.get("/healthz", tags=["operations"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": "autonomous-ai-research-scientist"}

    return application


app = create_app()

