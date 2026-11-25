"""Groq-hosted chat inference provider."""

from openai import OpenAI

from codeatlas.config import settings


class GroqProvider:
    """Generate responses and structured tool calls using Groq."""

    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout=settings.groq_timeout_seconds,
            max_retries=0,
        )

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
            "model": settings.groq_model,
            "messages": normalized,
            "reasoning_effort": settings.groq_reasoning_effort,
            "max_completion_tokens": settings.groq_max_output_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        message = choice.message

        if response.usage:
            print(
                f"[Groq] Input tokens: "
                f"{response.usage.prompt_tokens} | "
                f"Output tokens: "
                f"{response.usage.completion_tokens} | "
                f"Total: {response.usage.total_tokens}",
                flush=True,
            )

        print(
            f"[Groq] Finish reason: {choice.finish_reason}",
            flush=True,
        )

        return {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [call.model_dump() for call in message.tool_calls or []],
        }
