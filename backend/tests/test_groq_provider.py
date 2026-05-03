"""Unit tests for GroqProvider.

We monkey-patch the AsyncGroq client so no real network call is made — we just
verify our provider builds the right payload and parses Groq's response shape
correctly.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_scientist.llm.base import ChatMessage


class _FakeChatCompletions:
    def __init__(self):
        self.last_kwargs: dict | None = None

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            model=kwargs.get("model", "llama-3.3-70b-versatile"),
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="hello from groq"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4),
        )


class _FakeChat:
    def __init__(self):
        self.completions = _FakeChatCompletions()


class _FakeAsyncGroq:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = _FakeChat()


@pytest.fixture
def patched_groq(monkeypatch):
    import groq

    monkeypatch.setattr(groq, "AsyncGroq", _FakeAsyncGroq)
    yield


@pytest.mark.asyncio
async def test_groq_provider_builds_payload_and_parses_response(patched_groq):
    from ai_scientist.llm.groq_provider import GroqProvider

    p = GroqProvider(api_key="gsk-test", model="llama-3.3-70b-versatile")
    resp = await p.complete(
        [ChatMessage(role="user", content="hi")],
        system="you are helpful",
        temperature=0.2,
        max_tokens=128,
    )

    assert resp.content == "hello from groq"
    assert resp.model == "llama-3.3-70b-versatile"
    assert resp.input_tokens == 12
    assert resp.output_tokens == 4

    sent = p._client.chat.completions.last_kwargs
    assert sent["model"] == "llama-3.3-70b-versatile"
    assert sent["temperature"] == 0.2
    assert sent["max_tokens"] == 128
    assert sent["messages"][0] == {"role": "system", "content": "you are helpful"}
    assert sent["messages"][1] == {"role": "user", "content": "hi"}
    assert "response_format" not in sent


@pytest.mark.asyncio
async def test_groq_provider_enables_json_mode(patched_groq):
    from ai_scientist.llm.groq_provider import GroqProvider

    p = GroqProvider(api_key="gsk-test")
    await p.complete([ChatMessage(role="user", content="give me json")], json_mode=True)
    sent = p._client.chat.completions.last_kwargs
    assert sent["response_format"] == {"type": "json_object"}


def test_groq_provider_requires_api_key(patched_groq, monkeypatch):
    from ai_scientist.config import get_settings
    from ai_scientist.llm.groq_provider import GroqProvider

    get_settings.cache_clear()
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        get_settings(),
        "groq_api_key",
        None,
    )
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        GroqProvider()
