"""Verify hosted structured tool calling."""

import json
import time

from codeatlas.llm.factory import get_ai_provider

provider = get_ai_provider()

tools = [
    {
        "type": "function",
        "function": {
            "name": "find_symbol",
            "description": ("Locate a Python class or function inside a repository."),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                    }
                },
                "required": ["symbol_name"],
                "additionalProperties": False,
            },
        },
    }
]

started = time.perf_counter()

response = provider.chat(
    messages=[
        {
            "role": "system",
            "content": (
                "You are a repository investigation agent. "
                "Use the available tool to locate symbols. "
                "Never invent symbol locations."
            ),
        },
        {
            "role": "user",
            "content": ("Find the HTTPAdapter class in this repository."),
        },
    ],
    tools=tools,
)

print(json.dumps(response, indent=2))

calls = response.get("tool_calls") or []

assert calls, "No tool calls returned."

function = calls[0]["function"]

assert function["name"] == "find_symbol"

arguments = json.loads(function["arguments"])

assert arguments["symbol_name"] == "HTTPAdapter"

print(
    "Duration:",
    round(time.perf_counter() - started, 2),
    "seconds",
)

print("Hosted tool calling: PASSED")
