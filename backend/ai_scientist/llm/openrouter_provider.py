"""OpenRouter LLM provider.

OpenRouter exposes an OpenAI-compatible chat-completions API at
``https://openrouter.ai/api/v1/chat/completions``. We talk to it directly with
``httpx`` to avoid pulling the full ``openai`` SDK.

Docs: https://openrouter.ai/docs
"""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .base import ChatMessage, LLMProvider, LLMResponse

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT_S = 60.0


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = OPENROUTER_BASE,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured. Set it in .env, the "
                "environment, or via the in-app Settings page."
            )
        self.default_model = model or settings.openrouter_model
        self._base_url = base_url.rstrip("/")
        # OpenRouter recommends sending HTTP-Referer + X-Title so that analytics
        # and free-tier rate buckets attribute usage to your app.
        self._extra_headers = {
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }

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
        normalised: list[dict[str, Any]] = []
        if system:
            normalised.append({"role": "system", "content": system})
        for m in messages:
            normalised.append({"role": m.role, "content": m.content})

        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": normalised,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_S) as client:
            r = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if r.status_code >= 400:
                # Surface OpenRouter's error body so the user sees the cause
                # (insufficient credits, invalid model id, rate limit, etc.).
                detail = r.text[:500]
                raise RuntimeError(
                    f"OpenRouter API {r.status_code}: {detail}"
                )
            data = r.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data!r}")
        text = (choices[0].get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
        return LLMResponse(
            content=text.strip(),
            model=data.get("model") or (model or self.default_model),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
