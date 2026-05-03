"""Unit tests for OpenAIProvider.

Identical wire format to OpenRouter; we just verify auth, payload, error
surfacing, and the missing-key guard against the real OpenAI base URL.
"""

from __future__ import annotations

import asyncio

import json

import httpx
import pytest
import respx

from ai_scientist.llm.base import ChatMessage


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch):
    monkeypatch.setenv("AI_SCIENTIST_OPENAI_MIN_INTERVAL_S", "0")
    monkeypatch.setenv("AI_SCIENTIST_OPENAI_RATE_LIMIT_EXTRA_SLEEP_S", "0")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openai_provider import reset_openai_request_clock_for_tests

    reset_openai_request_clock_for_tests()
    get_settings.cache_clear()
    yield
    reset_openai_request_clock_for_tests()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_openai_provider_builds_payload_and_parses_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-1234567890abcdef")
    monkeypatch.setenv("AI_SCIENTIST_OPENAI_MODEL", "gpt-4o-mini")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openai_provider import OPENAI_BASE, OpenAIProvider

    get_settings.cache_clear()
    p = OpenAIProvider()

    body = {
        "model": "gpt-4o-mini",
        "choices": [
            {"message": {"content": "hi from openai"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
    }

    with respx.mock(assert_all_called=True) as router:
        route = router.post(f"{OPENAI_BASE}/chat/completions").mock(
            return_value=httpx.Response(200, json=body)
        )
        resp = await p.complete(
            [ChatMessage(role="user", content="hi")],
            system="you are helpful",
            temperature=0.3,
            max_tokens=256,
        )

    assert resp.content == "hi from openai"
    assert resp.model == "gpt-4o-mini"
    assert resp.input_tokens == 5
    assert resp.output_tokens == 3

    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer sk-test-1234567890abcdef"
    # No HTTP-Referer / X-Title — that's an OpenRouter-only thing
    assert "http-referer" not in sent.headers
    assert "x-title" not in sent.headers

    payload = json.loads(sent.content.decode())
    assert payload["model"] == "gpt-4o-mini"
    assert payload["temperature"] == 0.3
    assert payload["messages"][0] == {"role": "system", "content": "you are helpful"}
    assert payload["messages"][1] == {"role": "user", "content": "hi"}


@pytest.mark.asyncio
async def test_openai_provider_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openai_provider import OPENAI_BASE, OpenAIProvider

    get_settings.cache_clear()
    p = OpenAIProvider()

    async def instant_sleep(_t: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", instant_sleep)

    ok = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "after retry"}}],
        "usage": {},
    }

    with respx.mock(assert_all_called=False) as router:
        router.post(f"{OPENAI_BASE}/chat/completions").mock(
            side_effect=[
                httpx.Response(
                    429,
                    json={
                        "error": {
                            "message": "Please try again in 20s.",
                            "code": "rate_limit_exceeded",
                        }
                    },
                ),
                httpx.Response(200, json=ok),
            ]
        )
        resp = await p.complete([ChatMessage(role="user", content="hi")])

    assert resp.content == "after retry"


@pytest.mark.asyncio
async def test_openai_provider_surfaces_api_errors(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openai_provider import OPENAI_BASE, OpenAIProvider

    get_settings.cache_clear()
    p = OpenAIProvider()

    async def instant_sleep(_t: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", instant_sleep)

    with respx.mock(assert_all_called=True) as router:
        router.post(f"{OPENAI_BASE}/chat/completions").mock(
            return_value=httpx.Response(
                429, json={"error": {"message": "rate limit"}}
            )
        )
        with pytest.raises(RuntimeError, match="OpenAI API 429"):
            await p.complete([ChatMessage(role="user", content="hi")])


def test_parse_openai_rate_limit_wait_s_retry_after():
    from ai_scientist.llm.openai_provider import _parse_openai_rate_limit_wait_s

    r = httpx.Response(
        429,
        headers={"retry-after": "5"},
        json={"error": {"message": "slow down"}},
    )
    assert _parse_openai_rate_limit_wait_s(r) == 5.0


def test_parse_openai_rate_limit_wait_s_message():
    from ai_scientist.llm.openai_provider import _parse_openai_rate_limit_wait_s

    r = httpx.Response(
        429,
        json={
            "error": {
                "message": "Please try again in 12.5s. Visit https://example.com"
            }
        },
    )
    assert abs(_parse_openai_rate_limit_wait_s(r) - 14.5) < 0.01


def test_openai_provider_requires_api_key(monkeypatch):
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openai_provider import OpenAIProvider

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "openai_api_key", None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIProvider()


def test_factory_returns_openai_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.factory import get_llm
    from ai_scientist.llm.openai_provider import OpenAIProvider

    get_settings.cache_clear()
    get_llm.cache_clear()
    provider = get_llm("openai")
    assert isinstance(provider, OpenAIProvider)
