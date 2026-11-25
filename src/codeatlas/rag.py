"""Conversational repository question answering."""

from codeatlas.agents.evidence import (
    collect_evidence,
    format_evidence,
    select_evidence,
    validate_citations,
)
from codeatlas.agents.prompts import FINAL_SYSTEM_PROMPT
from codeatlas.config import settings
from codeatlas.llm.factory import get_ai_provider


class CodeRAG:
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
            item["content"][:500] for item in history[-6:] if item.get("role") == "user"
        ]

        search_query = "\n".join([*previous_questions[-1:], question])

        results = self.retriever.search(
            search_query,
            top_k=settings.retrieval_top_k,
        )

        evidence = select_evidence(collect_evidence([], results))

        if not evidence:
            return {
                "answer": "Insufficient repository evidence.",
                "sources": [],
                "citations_valid": False,
                "mode": "rag",
            }

        conversation = [
            {
                "role": item["role"],
                "content": item["content"][:1000],
            }
            for item in history[-4:]
            if item.get("role") in {"user", "assistant"}
        ]

        response = self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": FINAL_SYSTEM_PROMPT,
                },
                *conversation,
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{question}\n\n"
                        f"Current source evidence:\n"
                        f"{format_evidence(evidence)}"
                    ),
                },
            ]
        )

        answer = response["content"]

        return {
            "answer": answer,
            "sources": evidence,
            "citations_valid": validate_citations(
                answer,
                evidence,
            ),
            "mode": "rag",
        }
