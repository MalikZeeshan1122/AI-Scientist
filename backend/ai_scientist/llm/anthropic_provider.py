from __future__ import annotations

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .base import ChatMessage, LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from anthropic import AsyncAnthropic

        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured. Set it in .env or the environment."
            )
        self.default_model = model or settings.anthropic_model
        self._client = AsyncAnthropic(api_key=self.api_key)

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
        # Anthropic separates system prompts from messages.
        system_chunks: list[str] = []
        normalised: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                system_chunks.append(m.content)
            else:
                normalised.append({"role": m.role, "content": m.content})
        if system:
            system_chunks.insert(0, system)
        sys_prompt = "\n\n".join(system_chunks) if system_chunks else None

        resp = await self._client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=sys_prompt or "You are a helpful AI research assistant.",
            messages=normalised,
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")
        return LLMResponse(
            content=text,
            model=resp.model,
            input_tokens=getattr(resp.usage, "input_tokens", None),
            output_tokens=getattr(resp.usage, "output_tokens", None),
        )
