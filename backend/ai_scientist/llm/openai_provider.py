"""OpenAI LLM provider.

Talks directly to ``https://api.openai.com/v1/chat/completions`` over httpx.

Very low default RPM caps (e.g. **3 RPM** on some free/new OpenAI orgs) break long
pipelines that hit chat completions many times — especially parallel scoring via
``asyncio.gather``.

Mitigations:

* **Serialization inside each process**: every chat POST waits on one shared asyncio
  lock so overlapping pipelines cannot send concurrent requests from the same worker.
  Multiple uvicorn workers or other programs using the same key still share OpenAI's
  org RPM — spacing cannot coordinate across processes.
* **Configurable pacing**: ``AI_SCIENTIST_OPENAI_MIN_INTERVAL_S`` enforces a minimum
  wall-clock gap between POSTs (default leaves slack below ``ceil(60 / limit RPM)``
  for a **3 RPM** bucket — roughly **32–38** seconds apart).
* **429 backoff**: honor ``Retry-After`` / OpenAI's ``try again in Ns``, then wait at
  least ``min_interval + openai_rate_limit_extra_sleep_s`` so rolling RPM windows can
  drain before we POST again.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

import httpx

from ..config import get_settings
from .base import ChatMessage, LLMProvider, LLMResponse

OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_TIMEOUT_S = 60.0
_MAX_RATE_LIMIT_ATTEMPTS = 36
_RATE_LIMIT_WAIT_CAP_S = 180.0

logger = logging.getLogger(__name__)
_openai_pacing_disabled_logged = False

# Serialize ALL OpenAI chat POSTs across the whole interpreter — avoids accidental
# double-send even if multiple pipeline runners overlap two cached providers.
_openai_chat_serial_lock = asyncio.Lock()
_last_openai_post_mono = 0.0


def _parse_openai_rate_limit_wait_s(response: httpx.Response) -> float:
    """How long OpenAI asks us to wait before retrying a 429."""
    ra = response.headers.get("retry-after")
    if ra:
        try:
            return min(float(ra), _RATE_LIMIT_WAIT_CAP_S)
        except ValueError:
            pass
    try:
        body = response.json()
        msg = str((body.get("error") or {}).get("message") or "")
        m = re.search(r"try again in ([\d.]+)\s*s", msg, re.IGNORECASE)
        if m:
            return min(float(m.group(1)) + 2.0, _RATE_LIMIT_WAIT_CAP_S)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return 28.0


def reset_openai_request_clock_for_tests() -> None:
    """Test helper — resets pacing baseline."""
    global _last_openai_post_mono
    _last_openai_post_mono = 0.0


async def _throttle_gap_between_posts() -> None:
    global _last_openai_post_mono
    interval = float(get_settings().openai_min_interval_s or 0.0)
    if interval <= 0:
        return
    now = time.monotonic()
    if _last_openai_post_mono <= 0:
        return
    gap = interval - (now - _last_openai_post_mono)
    if gap > 0:
        await asyncio.sleep(gap)


def _mark_post_finished() -> None:
    global _last_openai_post_mono
    _last_openai_post_mono = time.monotonic()


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = OPENAI_BASE,
        organization: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it in .env, the "
                "environment, or via the in-app sidebar / Settings page."
            )
        self.default_model = model or settings.openai_model
        self._base_url = base_url.rstrip("/")
        self._organization = organization

        global _openai_pacing_disabled_logged
        if not _openai_pacing_disabled_logged:
            iv = float(settings.openai_min_interval_s or 0.0)
            if iv <= 0:
                _openai_pacing_disabled_logged = True
                logger.warning(
                    "OpenAI pacing disabled (AI_SCIENTIST_OPENAI_MIN_INTERVAL_S=%s); "
                    "orgs capped around ~3 RPM will see HTTP 429. Use ~35s+ between POSTs.",
                    settings.openai_min_interval_s,
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
        }
        if self._organization:
            headers["OpenAI-Organization"] = self._organization

        async with _openai_chat_serial_lock:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_S) as client:
                for attempt in range(_MAX_RATE_LIMIT_ATTEMPTS):
                    await _throttle_gap_between_posts()

                    r = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    _mark_post_finished()

                    if r.status_code == 429:
                        if attempt >= _MAX_RATE_LIMIT_ATTEMPTS - 1:
                            detail = r.text[:1500]
                            raise RuntimeError(f"OpenAI API 429: {detail}")
                        parsed = _parse_openai_rate_limit_wait_s(r)
                        min_iv = float(get_settings().openai_min_interval_s or 0.0)
                        extra = float(get_settings().openai_rate_limit_extra_sleep_s)
                        # If pacing is enabled, never undershoot org RPM spacing after a 429.
                        backoff = parsed if min_iv <= 0 else max(parsed, min_iv + extra)
                        await asyncio.sleep(backoff)
                        continue

                    if r.status_code >= 400:
                        detail = r.text[:1500]
                        raise RuntimeError(f"OpenAI API {r.status_code}: {detail}")

                    data = r.json()
                    break

                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError(f"OpenAI returned no choices: {data!r}")
                text = (choices[0].get("message") or {}).get("content") or ""
                usage = data.get("usage") or {}
                return LLMResponse(
                    content=text.strip(),
                    model=data.get("model") or (model or self.default_model),
                    input_tokens=usage.get("prompt_tokens"),
                    output_tokens=usage.get("completion_tokens"),
                )
