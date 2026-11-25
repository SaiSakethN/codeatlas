"""Public interface for CodeAtlas investigations."""

import time

from codeatlas.agents.graph import build_agent_graph
from codeatlas.agents.prompts import AGENT_SYSTEM_PROMPT
from codeatlas.config import settings
from codeatlas.llm.factory import get_ai_provider


class CodeAtlasAgent:
    def __init__(self, registry, provider=None):
        self.provider = provider or get_ai_provider()

        self.graph = build_agent_graph(
            self.provider,
            registry,
        )

    def investigate(self, question: str) -> dict:
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        if len(question) > 4000:
            raise ValueError("Question is too long.")

        started_at = time.monotonic()

        initial_state = {
            "question": question,
            "messages": [
                {
                    "role": "system",
                    "content": AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            "evidence": [],
            "trace": [],
            "seen_calls": [],
            "steps": 0,
            "answer": "",
            "citations_valid": False,
            "started_at": started_at,
            "termination_reason": "",
        }

        result = self.graph.invoke(
            initial_state,
            config={"recursion_limit": (settings.agent_max_steps * 2 + 5)},
        )

        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["evidence"],
            "trace": result["trace"],
            "steps": result["steps"],
            "citations_valid": result["citations_valid"],
            "termination_reason": result["termination_reason"],
            "duration_seconds": round(
                time.monotonic() - started_at,
                2,
            ),
        }
