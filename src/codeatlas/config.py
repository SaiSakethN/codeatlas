"""Central configuration for CodeAtlas."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_DIR = PROJECT_ROOT / "workspace"
REPOSITORIES_DIR = WORKSPACE_DIR / "repositories"
INDEXES_DIR = WORKSPACE_DIR / "indexes"


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CodeAtlas"
    app_version: str = "0.1.0"
    environment: Literal["development", "production"] = "development"

    llm_provider: Literal["ollama", "openai"] = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    ollama_embedding_model: str = "nomic-embed-text"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = ""
    openai_embedding_model: str = ""

    embedding_batch_size: int = 16
    retrieval_top_k: int = 6

    agent_max_steps: int = 8
    agent_timeout_seconds: int = 180

    max_repository_files: int = 2000
    max_file_size: int = 500_000

    frontend_url: str = "http://localhost:3000"


settings = Settings()


def initialize_workspace() -> None:
    """Create required runtime directories."""

    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
