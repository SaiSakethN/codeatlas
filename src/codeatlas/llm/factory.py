"""Factory for selecting the configured AI provider."""

from codeatlas.config import settings
from codeatlas.llm.base import AIProvider
from codeatlas.llm.ollama_provider import OllamaProvider
from codeatlas.llm.openai_provider import OpenAIProvider


def get_ai_provider() -> AIProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()

    if settings.llm_provider == "openai":
        return OpenAIProvider()

    raise ValueError(f"Unsupported AI provider: {settings.llm_provider}")
