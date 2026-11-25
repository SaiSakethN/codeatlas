"""Shared state for repository investigations."""

from typing import TypedDict


class AgentState(TypedDict):
    question: str
    messages: list[dict]
    evidence: list[dict]
    trace: list[dict]
    seen_calls: list[str]
    steps: int
    answer: str
    citations_valid: bool
    started_at: float
    termination_reason: str
