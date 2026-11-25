"""Tests for AI provider composition."""

from codeatlas.llm.base import AIProvider
from codeatlas.llm.composite_provider import CompositeProvider


class FakeEmbeddingProvider(AIProvider):
    def embed_documents(self, documents):
        return [[0.1, 0.2, 0.3] for _ in documents]

    def embed_query(self, query):
        return [0.4, 0.5, 0.6]

    def chat(self, messages, tools=None):
        raise AssertionError("Chat must not use the embedding provider.")


class FakeChatProvider:
    def chat(self, messages, tools=None):
        return {
            "role": "assistant",
            "content": "Hosted response",
            "tool_calls": tools or [],
        }


def create_provider():
    return CompositeProvider(
        embedding_provider=FakeEmbeddingProvider(),
        chat_provider=FakeChatProvider(),
    )


def test_composite_document_embeddings():
    provider = create_provider()

    result = provider.embed_documents(["Python", "FastAPI"])

    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]


def test_composite_query_embedding():
    provider = create_provider()

    assert provider.embed_query("Python") == [
        0.4,
        0.5,
        0.6,
    ]


def test_composite_chat():
    provider = create_provider()

    response = provider.chat([{"role": "user", "content": "Hello"}])

    assert response["content"] == "Hosted response"


def test_composite_forwards_tools():
    provider = create_provider()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "find_symbol",
            },
        }
    ]

    response = provider.chat(
        messages=[
            {
                "role": "user",
                "content": "Find HTTPAdapter",
            }
        ],
        tools=tools,
    )

    assert response["tool_calls"] == tools
