"""Ollama implementation of the AI provider interface."""

import json
from uuid import uuid4

from ollama import Client

from codeatlas.config import settings
from codeatlas.llm.base import AIProvider


class OllamaProvider(AIProvider):
    def __init__(self):
        self.client = Client(
            host=settings.ollama_base_url,
            timeout=120,
        )

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        if not documents:
            return []

        response = self.client.embed(
            model=settings.ollama_embedding_model,
            input=[f"search_document: {document}" for document in documents],
        )

        return response.embeddings

    def embed_query(self, query: str) -> list[float]:
        response = self.client.embed(
            model=settings.ollama_embedding_model,
            input=f"search_query: {query}",
        )

        return response.embeddings[0]

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        normalized = []

        for message in messages:
            item = dict(message)
            item.pop("tool_call_id", None)

            if item.get("tool_calls"):
                calls = []

                for call in item["tool_calls"]:
                    function = call["function"]
                    arguments = function["arguments"]

                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)

                    calls.append(
                        {
                            "function": {
                                "name": function["name"],
                                "arguments": arguments,
                            }
                        }
                    )

                item["tool_calls"] = calls

            normalized.append(item)

        response = self.client.chat(
            model=settings.ollama_model,
            messages=normalized,
            tools=tools or [],
            think=False,
            options={
                "temperature": 0.1,
                "num_ctx": 8192,
                "num_predict": 1500,
            },
        )

        message = response.message

        tool_calls = []

        for call in message.tool_calls or []:
            tool_calls.append(
                {
                    "id": str(uuid4()),
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": json.dumps(call.function.arguments),
                    },
                }
            )

        return {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": tool_calls,
        }
