from __future__ import annotations

import asyncio
import time

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .base import ChatMessage, EmbeddingProvider, LLMProvider, LLMResponse


class _MinIntervalLimiter:
    """Coalesces concurrent calls to be at least `interval_s` apart.

    Cheap shared rate limit; protects free-tier RPM quotas without backoff after-the-fact.
    """

    def __init__(self, interval_s: float = 4.5) -> None:
        self.interval_s = interval_s
        self._lock = asyncio.Lock()
        self._next_at: float = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            sleep_for = self._next_at - now
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
                now = time.monotonic()
            self._next_at = now + self.interval_s


# 15 RPM free-tier on gemini-2.0-flash -> ~4 s between calls is safe.
# Shared across all GoogleProvider instances created in the same process.
_GOOGLE_RATE_LIMITER = _MinIntervalLimiter(interval_s=4.5)


def _translate_google_error(exc: Exception) -> Exception:
    """Convert google-genai SDK errors into clean RuntimeErrors with actionable messages.

    The handler chain in api/main.py reliably catches RuntimeError; broad SDK errors
    sometimes escape the generic Exception handler before CORS headers are attached.
    """
    try:
        from google.genai import errors as gerrors
    except Exception:
        return exc
    if isinstance(exc, gerrors.ClientError):
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        msg = (str(exc).split("{", 1)[0]).strip().rstrip(".") or "Google API client error"
        if code == 429 or "RESOURCE_EXHAUSTED" in str(exc):
            # Try to surface the suggested retry-delay if present
            import re
            m = re.search(r"retry in ([\d.]+)s", str(exc))
            hint = f" Retry suggested in ~{m.group(1)}s." if m else ""
            return RuntimeError(
                f"Gemini quota exceeded ({code}).{hint} "
                "Either wait, switch to a higher-quota model "
                "(AI_SCIENTIST_GOOGLE_MODEL=gemini-2.0-flash-lite), "
                "or upgrade to a paid Gemini plan at https://ai.google.dev."
            )
        if code in (401, 403):
            return RuntimeError(
                f"Gemini auth failed ({code}). Check GOOGLE_API_KEY in backend/.env."
            )
        if code == 404:
            return RuntimeError(
                f"Gemini model not found ({code}). Check AI_SCIENTIST_GOOGLE_MODEL "
                f"and AI_SCIENTIST_GOOGLE_EMBED_MODEL in backend/.env. Detail: {msg}"
            )
        return RuntimeError(f"Gemini API error ({code}): {msg}")
    if isinstance(exc, gerrors.ServerError):
        return RuntimeError(f"Gemini server error: {exc}")
    return exc


def _gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


class GoogleProvider(LLMProvider):
    name = "google"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from google import genai

        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured. Set it in .env or the environment."
            )
        self.default_model = model or settings.google_model
        self._client = genai.Client(api_key=self.api_key)

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
        from google.genai import types as gtypes

        contents = [
            gtypes.Content(role=_gemini_role(m.role), parts=[gtypes.Part(text=m.content)])
            for m in messages
            if m.role != "system"
        ]
        sys_prompt = system or next(
            (m.content for m in messages if m.role == "system"), None
        )
        # Gemini 2.5 enables internal "thinking" by default, which consumes output
        # tokens before producing visible text and can return empty responses on small
        # max_tokens budgets. Disable it so max_tokens applies to the actual answer.
        thinking_cfg = None
        try:
            thinking_cfg = gtypes.ThinkingConfig(thinking_budget=0)
        except (AttributeError, TypeError):
            thinking_cfg = None

        cfg = gtypes.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=sys_prompt,
            response_mime_type="application/json" if json_mode else None,
            thinking_config=thinking_cfg,
        )
        await _GOOGLE_RATE_LIMITER.wait()
        try:
            resp = await self._client.aio.models.generate_content(
                model=model or self.default_model,
                contents=contents,
                config=cfg,
            )
        except Exception as exc:
            raise _translate_google_error(exc) from exc
        text = (resp.text or "").strip()
        usage = getattr(resp, "usage_metadata", None)
        return LLMResponse(
            content=text,
            model=model or self.default_model,
            input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
            output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
        )


class GoogleEmbedder(EmbeddingProvider):
    name = "google"
    # gemini-embedding-001 returns 3072-dim vectors by default.
    # Chroma auto-detects from the first batch, so this is informational only.
    dimension = 3072

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from google import genai

        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is required for embeddings (or switch embed provider)."
            )
        self.default_model = model or settings.google_embed_model
        self._client = genai.Client(api_key=self.api_key)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
    )
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = await self._client.aio.models.embed_content(
                model=model or self.default_model,
                contents=texts,
            )
        except Exception as exc:
            raise _translate_google_error(exc) from exc
        # google-genai returns either .embeddings (list of objects with .values) or .embedding
        out: list[list[float]] = []
        embeddings = getattr(resp, "embeddings", None)
        if embeddings:
            for e in embeddings:
                values = getattr(e, "values", None) or e
                out.append(list(values))
        elif getattr(resp, "embedding", None):
            out.append(list(resp.embedding.values))
        return out
