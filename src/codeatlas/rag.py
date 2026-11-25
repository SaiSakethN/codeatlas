"""Grounded repository question answering."""

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

from codeatlas.agents.evidence import (
    collect_evidence,
    format_evidence,
    normalize_citations,
    select_evidence,
    validate_citations,
)
from codeatlas.agents.prompts import FINAL_SYSTEM_PROMPT
from codeatlas.config import settings
from codeatlas.llm.factory import get_ai_provider


class CodeRAG:
    """Answer repository questions using retrieved source evidence."""

    def __init__(self, retriever, provider=None):
        self.retriever = retriever
        self.provider = provider or get_ai_provider()

    def ask(
        self,
        question: str,
        history: list[dict] | None = None,
    ) -> dict:
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        if len(question) > 4000:
            raise ValueError("Question is too long.")

        history = history or []

        previous_questions = [
            message.get("content", "") for message in history[-6:] if message.get("role") == "user"
        ]

        retrieval_query = question

        if previous_questions:
            retrieval_query = f"{previous_questions[-1][:500]}\n{question}"

        results = self.retriever.search(
            retrieval_query,
            top_k=settings.retrieval_top_k,
        )

        evidence = select_evidence(collect_evidence([], results))

        def failure(
            message: str,
            reason: str,
        ) -> dict:
            return {
                "answer": message,
                "sources": evidence,
                "citations_valid": False,
                "mode": "rag",
                "termination_reason": reason,
            }

        if not evidence:
            return failure(
                "I could not find sufficient source evidence to answer this question reliably.",
                "insufficient_evidence",
            )

        conversation = [
            {
                "role": message["role"],
                "content": str(message.get("content", ""))[:1000],
            }
            for message in history[-4:]
            if message.get("role")
            in {
                "user",
                "assistant",
            }
        ]

        context = format_evidence(evidence)

        messages = [
            {
                "role": "system",
                "content": FINAL_SYSTEM_PROMPT,
            },
            *conversation,
            {
                "role": "user",
                "content": (f"Question:\n{question}\n\nSource evidence:\n{context}"),
            },
        ]

        try:
            response = self.provider.chat(
                messages=messages,
            )

        except RateLimitError:
            return failure(
                "The hosted AI provider has reached its "
                "rate limit. Please try again shortly. "
                "Retrieved source evidence is still available.",
                "rate_limit",
            )

        except (httpx.TimeoutException, APITimeoutError):
            return failure(
                "The AI provider timed out. Please try again.",
                "model_timeout",
            )

        except (httpx.RequestError, APIConnectionError):
            return failure(
                "Could not connect to the AI provider. Please try again.",
                "model_connection_error",
            )

        except APIStatusError:
            return failure(
                "The AI provider rejected the request.",
                "model_api_error",
            )

        answer = normalize_citations((response.get("content") or "").strip())

        if not answer:
            return failure(
                "The AI provider returned an empty answer.",
                "empty_response",
            )

        return {
            "answer": answer,
            "sources": evidence,
            "citations_valid": validate_citations(
                answer,
                evidence,
            ),
            "mode": "rag",
            "termination_reason": "completed",
        }
