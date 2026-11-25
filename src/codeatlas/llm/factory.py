"""Factory for configurable AI providers."""

from codeatlas.config import settings
from codeatlas.llm.base import AIProvider
from codeatlas.llm.composite_provider import CompositeProvider
from codeatlas.llm.groq_provider import GroqProvider
from codeatlas.llm.ollama_provider import OllamaProvider
from codeatlas.llm.openai_provider import OpenAIProvider


def get_ai_provider() -> AIProvider:
    embedding_name = settings.llm_provider

    chat_name = settings.chat_provider or embedding_name

    if embedding_name == "ollama":
        embedding_provider = OllamaProvider()

    elif embedding_name == "openai":
        embedding_provider = OpenAIProvider()

    else:
        raise ValueError(f"Unsupported embedding provider: {embedding_name}")

    if chat_name == embedding_name:
        return embedding_provider

    if chat_name == "groq":
        chat_provider = GroqProvider()

    elif chat_name == "ollama":
        chat_provider = OllamaProvider()

    elif chat_name == "openai":
        chat_provider = OpenAIProvider()

    else:
        raise ValueError(f"Unsupported chat provider: {chat_name}")

    return CompositeProvider(
        embedding_provider=embedding_provider,
        chat_provider=chat_provider,
    )
