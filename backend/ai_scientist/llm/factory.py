from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from .base import EmbeddingProvider, LLMProvider


@lru_cache(maxsize=4)
def get_llm(provider: str | None = None) -> LLMProvider:
    settings = get_settings()
    name = (provider or settings.default_provider).lower()
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if name == "google":
        from .google_provider import GoogleProvider

        return GoogleProvider()
    if name == "groq":
        from .groq_provider import GroqProvider

        return GroqProvider()
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name == "openrouter":
        from .openrouter_provider import OpenRouterProvider

        return OpenRouterProvider()
    raise ValueError(
        f"Unknown LLM provider: {name!r}. "
        "Use 'anthropic', 'google', 'groq', 'openai', or 'openrouter'."
    )


@lru_cache(maxsize=2)
def get_embedder(provider: str | None = None) -> EmbeddingProvider:
    settings = get_settings()
    name = (provider or settings.embed_provider).lower()
    if name == "google":
        from .google_provider import GoogleEmbedder

        return GoogleEmbedder()
    raise ValueError(f"Unknown embedding provider: {name!r}.")
