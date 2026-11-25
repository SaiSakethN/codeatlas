import pytest

from codeatlas.agents.evidence import (
    collect_evidence,
    validate_citations,
)
from codeatlas.agents.service import CodeAtlasAgent
from codeatlas.rag import CodeRAG

SOURCE = {
    "file_path": "auth.py",
    "start_line": 1,
    "end_line": 2,
    "content": "def login():\n    return True",
}


def tool_request():
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": '{"file_path": "auth.py"}',
                },
            }
        ],
    }


class FakeRegistry:
    def __init__(self):
        self.calls = 0
        self.retrieval_calls = 0

    def schemas(self):
        return []

    def execute(self, name, arguments):
        if name == "semantic_search":
            self.retrieval_calls += 1
            return []

        self.calls += 1
        return SOURCE


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None):
        self.calls += 1

        if self.calls == 1:
            return tool_request()

        return {
            "role": "assistant",
            "content": "The login function returns True [S1].",
            "tool_calls": [],
        }


def test_evidence_collection():
    evidence = collect_evidence([], SOURCE)

    assert len(evidence) == 1
    assert evidence[0]["id"] == "S1"


def test_duplicate_evidence():
    evidence = collect_evidence([], [SOURCE, SOURCE])

    assert len(evidence) == 1


def test_valid_citation():
    evidence = collect_evidence([], SOURCE)

    assert validate_citations(
        "Login returns True [S1].",
        evidence,
    )


def test_invalid_citation():
    evidence = collect_evidence([], SOURCE)

    assert not validate_citations(
        "Unsupported claim [S99].",
        evidence,
    )


def test_missing_citation():
    assert not validate_citations(
        "An answer without citations.",
        collect_evidence([], SOURCE),
    )


def test_agent_investigation():
    registry = FakeRegistry()

    agent = CodeAtlasAgent(
        registry,
        FakeProvider(),
    )

    result = agent.investigate("What does login do?")

    assert result["citations_valid"]
    assert len(result["sources"]) == 1
    assert len(result["trace"]) == 2

    assert result["trace"][0]["tool"] == "semantic_search"
    assert result["trace"][1]["tool"] == "read_file"

    assert registry.retrieval_calls == 1
    assert registry.calls == 1


def test_empty_question():
    agent = CodeAtlasAgent(
        FakeRegistry(),
        FakeProvider(),
    )

    with pytest.raises(ValueError):
        agent.investigate("")


def test_duplicate_tool_prevention(monkeypatch):
    from codeatlas.config import settings

    monkeypatch.setattr(
        settings,
        "agent_max_steps",
        3,
    )

    class RepeatingProvider:
        def chat(self, messages, tools=None):
            if tools is not None:
                return tool_request()

            return {
                "role": "assistant",
                "content": "Login returns True [S1].",
                "tool_calls": [],
            }

    registry = FakeRegistry()

    agent = CodeAtlasAgent(
        registry,
        RepeatingProvider(),
    )

    result = agent.investigate("Explain login.")

    assert registry.calls == 1
    assert result["steps"] == 3
    assert result["termination_reason"] == "step_limit"

    assert any(item["status"] == "error" for item in result["trace"])


def test_agent_without_evidence():
    class EmptyProvider:
        def chat(self, messages, tools=None):
            return {
                "role": "assistant",
                "content": "An unsupported answer.",
                "tool_calls": [],
            }

    agent = CodeAtlasAgent(
        FakeRegistry(),
        EmptyProvider(),
    )

    result = agent.investigate("Explain login.")

    assert not result["citations_valid"]
    assert result["sources"] == []


def test_rag_answer():
    class FakeRetriever:
        def search(self, query, top_k):
            return [SOURCE]

    class RAGProvider:
        def chat(self, messages, tools=None):
            return {"content": "Login returns True [S1]."}

    rag = CodeRAG(
        FakeRetriever(),
        RAGProvider(),
    )

    result = rag.ask("Explain login.")

    assert result["citations_valid"]
    assert result["mode"] == "rag"


def test_agent_handles_model_timeout():
    import httpx

    class TimeoutProvider:
        def chat(self, messages, tools=None):
            raise httpx.ReadTimeout("Inference timed out")

    agent = CodeAtlasAgent(
        FakeRegistry(),
        TimeoutProvider(),
    )

    result = agent.investigate("Explain login.")

    assert result["termination_reason"] == "model_timeout"
    assert not result["citations_valid"]
    assert result["answer"]


def test_agent_uses_initial_evidence_without_tool_calls():
    class RetrievalRegistry(FakeRegistry):
        def execute(self, name, arguments):
            if name == "semantic_search":
                return [SOURCE]

            raise AssertionError("Unexpected tool call")

    class DirectAnswerProvider:
        def chat(self, messages, tools=None):
            return {
                "role": "assistant",
                "content": "Login returns True [S1].",
                "tool_calls": [],
            }

    agent = CodeAtlasAgent(
        RetrievalRegistry(),
        DirectAnswerProvider(),
    )

    result = agent.investigate("Explain login.")

    assert result["citations_valid"]
    assert len(result["sources"]) == 1
    assert result["trace"][0]["tool"] == "semantic_search"


def test_rag_handles_rate_limit():
    import httpx
    from openai import RateLimitError

    from codeatlas.rag import CodeRAG

    class RateLimitedProvider:
        def chat(self, messages, tools=None):
            response = httpx.Response(
                status_code=429,
                request=httpx.Request(
                    "POST",
                    "https://example.com/v1/chat/completions",
                ),
            )

            raise RateLimitError(
                "Rate limit reached",
                response=response,
                body=None,
            )

    class Retriever:
        def search(self, query, top_k=3):
            return [
                {
                    "file_path": "auth.py",
                    "start_line": 1,
                    "end_line": 2,
                    "content": "def login():\n    return True",
                }
            ]

    rag = CodeRAG(
        retriever=Retriever(),
        provider=RateLimitedProvider(),
    )

    result = rag.ask("How does login work?")

    assert result["termination_reason"] == "rate_limit"
    assert result["citations_valid"] is False
    assert len(result["sources"]) == 1
    assert result["mode"] == "rag"


def test_normalizes_model_brackets_without_forging_citations():
    from codeatlas.agents.evidence import normalize_citations, validate_citations

    answer = normalize_citations("Implementation 【S1】; missing 【S99】.")
    assert answer == "Implementation [S1]; missing [S99]."
    assert not validate_citations(answer, [{"id": "S1"}])
    assert validate_citations(normalize_citations("Implementation 【S1】."), [{"id": "S1"}])
