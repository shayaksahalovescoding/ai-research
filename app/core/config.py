from __future__ import annotations

from pathlib import Path

from pydantic import Field, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded only from the environment or `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./research.db"
    arxiv_base_url: HttpUrl = "https://export.arxiv.org/api/query"
    arxiv_max_results: PositiveInt = Field(default=8, le=25)
    sandbox_image: str = "ai-research-experiment:dev"
    sandbox_volume: str = "research_artifacts"
    sandbox_timeout_seconds: PositiveInt = Field(default=45, le=300)
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = Field(default=1.0, gt=0, le=4)
    artifact_root: Path = Path("artifacts")
    research_max_iterations: PositiveInt = Field(default=3, le=10)
    max_experiments_per_project: PositiveInt = Field(default=8, le=25)
    max_total_runtime_seconds: PositiveInt = Field(default=300, le=1800)
    min_information_gain_epsilon: float = Field(default=0.02, ge=0.0)
    replication_seed_count: PositiveInt = Field(default=3, ge=2, le=10)
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3:latest"
    log_level: str = "INFO"
