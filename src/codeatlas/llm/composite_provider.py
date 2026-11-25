"""Compose independent embedding and chat providers."""

from typing import Protocol

from codeatlas.llm.base import AIProvider


class ChatProvider(Protocol):
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict: ...


class CompositeProvider(AIProvider):
    """Expose independent AI services through one interface."""

    def __init__(
        self,
        embedding_provider: AIProvider,
        chat_provider: ChatProvider,
    ):
        self.embedding_provider = embedding_provider
        self.chat_provider = chat_provider

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        return self.embedding_provider.embed_documents(documents)

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        return self.embedding_provider.embed_query(query)

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        return self.chat_provider.chat(
            messages=messages,
            tools=tools,
        )
