"""OpenAI-compatible cloud inference provider."""

from openai import OpenAI

from codeatlas.config import settings
from codeatlas.llm.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("Cloud API key is not configured.")

        if not settings.openai_model:
            raise ValueError("Cloud model is not configured.")

        if not settings.openai_embedding_model:
            raise ValueError("Cloud embedding model is not configured.")

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=120,
            max_retries=2,
        )

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        if not documents:
            return []

        response = self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=documents,
        )

        return [
            item.embedding
            for item in sorted(
                response.data,
                key=lambda item: item.index,
            )
        ]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_documents([query])[0]

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        normalized = []

        for message in messages:
            item = dict(message)
            item.pop("tool_name", None)

            if not item.get("tool_calls"):
                item.pop("tool_calls", None)

            normalized.append(item)

        kwargs = {
            "model": settings.openai_model,
            "messages": normalized,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        message = response.choices[0].message

        return {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [call.model_dump() for call in message.tool_calls or []],
        }
