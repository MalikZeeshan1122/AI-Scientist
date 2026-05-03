from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

Role = Literal["system", "user", "assistant"]
T = TypeVar("T", bound=BaseModel)


class ChatMessage(BaseModel):
    role: Role
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract LLM chat provider. Implementations wrap a vendor SDK."""

    name: str
    default_model: str

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        system: str | None = None,
        json_mode: bool = False,
    ) -> LLMResponse: ...

    async def complete_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> str:
        msgs = [ChatMessage(role="user", content=prompt)]
        resp = await self.complete(
            msgs, model=model, temperature=temperature, max_tokens=max_tokens, system=system
        )
        return resp.content.strip()

    async def complete_json(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> T:
        """Ask the LLM for JSON, parse + validate against `schema`."""
        instruction = (
            "You MUST reply with a single JSON object matching the schema below. "
            "Do not include markdown fences, prose, or explanations.\n\n"
            f"JSON schema:\n{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        full_system = f"{system}\n\n{instruction}" if system else instruction
        resp = await self.complete(
            [ChatMessage(role="user", content=prompt)],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=full_system,
            json_mode=True,
        )
        text = resp.content.strip()
        text = _strip_code_fences(text)
        return schema.model_validate_json(text)


class EmbeddingProvider(ABC):
    name: str
    default_model: str
    dimension: int

    @abstractmethod
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]: ...


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        first_newline = s.find("\n")
        if first_newline != -1:
            s = s[first_newline + 1 :]
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()
