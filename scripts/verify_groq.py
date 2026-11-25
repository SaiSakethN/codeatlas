"""Verify Groq hosted inference."""

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
    timeout=60,
    max_retries=0,
)

started = time.perf_counter()

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "Answer concisely and accurately.",
        },
        {
            "role": "user",
            "content": "Explain Python decorators in two sentences.",
        },
    ],
    reasoning_effort="low",
    max_completion_tokens=512,
)

print("Model:", response.model)
print("Answer:", response.choices[0].message.content)
print("Finish reason:", response.choices[0].finish_reason)
print("Duration:", round(time.perf_counter() - started, 2), "seconds")
print("Token usage:", response.usage)
