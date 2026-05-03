"""Groq LLM provider.

Groq exposes an OpenAI-compatible chat-completions API and ships a real async
SDK (`AsyncGroq`), which fits cleanly into our async pipeline. Default model is
`llama-3.3-70b-versatile` — Groq's flagship instruct model, free-tier friendly.
"""

from __future__ import annotations

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .base import ChatMessage, LLMProvider, LLMResponse


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from groq import AsyncGroq

        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. Set it in .env or the environment."
            )
        self.default_model = model or settings.groq_model
        self._client = AsyncGroq(api_key=self.api_key)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
    )
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        system: str | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        # Groq follows the OpenAI chat-completion shape: system messages live in
        # the same `messages` array as user/assistant turns.
        normalised: list[dict[str, Any]] = []
        if system:
            normalised.append({"role": "system", "content": system})
        for m in messages:
            normalised.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": normalised,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        text = (choice.message.content or "").strip()

        usage = getattr(resp, "usage", None)
        return LLMResponse(
            content=text,
            model=resp.model,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
