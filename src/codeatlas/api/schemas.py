"""Validated public API inputs."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(max_length=250)

    @field_validator("url")
    @classmethod
    def github_url(cls, value: str) -> str:
        match = re.fullmatch(
            r"https://github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+)/?", value.strip()
        )
        if not match or match[2].removesuffix(".git") in {"", ".", ".."}:
            raise ValueError("Use a public HTTPS GitHub repository URL.")
        return f"https://github.com/{match[1]}/{match[2].removesuffix('.git')}"


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=4000)
    mode: Literal["rag", "agent"] = "rag"
    history: list[Message] = Field(default_factory=list, max_length=6)

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be blank.")
        return value.strip()
