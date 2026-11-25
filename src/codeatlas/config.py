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
    api_token: str = ""
    api_requests_per_minute: int = 60
    max_repositories: int = 5

    ollama_timeout_seconds: int = 300
    ollama_context_window: int = 8192
    ollama_max_output_tokens: int = 768
    ollama_keep_alive: str = "5m"

    chat_provider: Literal["ollama", "openai", "groq"] | None = None

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_timeout_seconds: int = 60
    groq_max_output_tokens: int = 1024
    groq_reasoning_effort: Literal["low", "medium", "high"] = "low"


settings = Settings()


def initialize_workspace() -> None:
    """Create required runtime directories."""

    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
