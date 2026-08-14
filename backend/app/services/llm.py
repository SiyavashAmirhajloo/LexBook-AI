"""LLM abstraction layer.

Provider-agnostic interface as required by docs/tech-stack.md.
Default: Gemini via the Google Generative AI REST API (no SDK needed).
Falls back to a deterministic local echo if GEMINI_API_KEY is missing.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

import httpx
from functools import lru_cache


@dataclass
class LLMMessage:
    role: str          # "user" | "assistant" | "system"
    content: str


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield tokens as they arrive from the model."""

    async def generate(self, messages: list[LLMMessage], system: str | None = None) -> str:
        """Collect all tokens into a single string (non-streaming convenience)."""
        chunks = []
        async for token in self.stream(messages, system=system):
            chunks.append(token)
        return "".join(chunks)


class GeminiProvider(LLMProvider):
    """Gemini via the Google Generative AI REST API (streamGenerateContent)."""

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"

    def __init__(self) -> None:
        self._api_key = os.getenv("GEMINI_API_KEY", "")
        self._model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    def _url(self) -> str:
        return self.API_URL.format(model=self._model) + f"?key={self._api_key}&alt=sse"

    @staticmethod
    def _format_contents(messages: list[LLMMessage], system: str | None = None) -> dict:
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})

        for m in messages:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        return {"contents": contents}

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
    ) -> AsyncIterator[str]:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is required for GeminiProvider")

        body = self._format_contents(messages, system=system)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self._url(),
                headers={"Content-Type": "application/json"},
                json=body,
            ) as resp:
                if resp.status_code != 200:
                    error = await resp.aread()
                    raise RuntimeError(f"Gemini API {resp.status_code}: {error[:300]}")

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                        candidates = data.get("candidates", [])
                        if not candidates:
                            continue
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if "text" in part:
                                yield part["text"]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return GeminiProvider()
    # Future: groq, openrouter, ollama go here.
    raise ValueError(f"Unknown LLM provider: {provider}")
