"""Common interface for AI inference providers."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Contract implemented by all AI providers."""

    @abstractmethod
    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        """Convert documents into embedding vectors."""

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Convert a search query into an embedding vector."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Generate a response with optional tool calls."""
