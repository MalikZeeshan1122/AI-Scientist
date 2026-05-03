"""Unit tests for OpenRouterProvider.

We use ``respx`` to intercept the underlying httpx call and verify that the
provider builds the correct chat-completions payload, attaches the right
auth/attribution headers, and parses OpenRouter's OpenAI-compatible response.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from ai_scientist.llm.base import ChatMessage


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    from ai_scientist.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_openrouter_provider_builds_payload_and_parses_response(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-1234567890abcdef")
    monkeypatch.setenv("AI_SCIENTIST_OPENROUTER_MODEL", "openai/gpt-4o-mini")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openrouter_provider import (
        OPENROUTER_BASE,
        OpenRouterProvider,
    )

    get_settings.cache_clear()
    p = OpenRouterProvider()

    body = {
        "model": "openai/gpt-4o-mini",
        "choices": [
            {"message": {"content": "hi from openrouter"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
    }

    with respx.mock(assert_all_called=True) as router:
        route = router.post(f"{OPENROUTER_BASE}/chat/completions").mock(
            return_value=httpx.Response(200, json=body)
        )
        resp = await p.complete(
            [ChatMessage(role="user", content="hi")],
            system="you are helpful",
            temperature=0.3,
            max_tokens=256,
        )

    assert resp.content == "hi from openrouter"
    assert resp.model == "openai/gpt-4o-mini"
    assert resp.input_tokens == 5
    assert resp.output_tokens == 3

    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer sk-or-test-1234567890abcdef"
    assert sent.headers["http-referer"]  # attribution
    assert sent.headers["x-title"]
    payload = json.loads(sent.content.decode())
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["temperature"] == 0.3
    assert payload["max_tokens"] == 256
    assert payload["messages"][0] == {"role": "system", "content": "you are helpful"}
    assert payload["messages"][1] == {"role": "user", "content": "hi"}
    assert "response_format" not in payload


@pytest.mark.asyncio
async def test_openrouter_provider_enables_json_mode(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openrouter_provider import (
        OPENROUTER_BASE,
        OpenRouterProvider,
    )

    get_settings.cache_clear()
    p = OpenRouterProvider()

    body = {
        "model": "openai/gpt-4o-mini",
        "choices": [{"message": {"content": "{}"}}],
    }
    with respx.mock(assert_all_called=True) as router:
        route = router.post(f"{OPENROUTER_BASE}/chat/completions").mock(
            return_value=httpx.Response(200, json=body)
        )
        await p.complete(
            [ChatMessage(role="user", content="give me json")],
            json_mode=True,
        )

    payload = json.loads(route.calls.last.request.content.decode())
    assert payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_openrouter_provider_surfaces_api_errors(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openrouter_provider import (
        OPENROUTER_BASE,
        OpenRouterProvider,
    )

    get_settings.cache_clear()
    p = OpenRouterProvider()

    with respx.mock(assert_all_called=True) as router:
        router.post(f"{OPENROUTER_BASE}/chat/completions").mock(
            return_value=httpx.Response(
                402, json={"error": {"message": "insufficient credits"}}
            )
        )
        with pytest.raises(RuntimeError, match="OpenRouter API 402"):
            await p.complete([ChatMessage(role="user", content="hi")])


def test_openrouter_provider_requires_api_key(monkeypatch):
    from ai_scientist.config import get_settings
    from ai_scientist.llm.openrouter_provider import OpenRouterProvider

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "openrouter_api_key", None)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider()
