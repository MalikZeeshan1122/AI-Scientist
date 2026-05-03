"""Unit tests for the .env writer + /settings API."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_scientist import settings_store


@pytest.fixture
def tmp_env(monkeypatch, tmp_path: Path):
    """Point settings_store at an isolated `.env` per test."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# header comment\n"
        "GOOGLE_API_KEY=existing-google\n"
        "GROQ_API_KEY=existing-groq\n"
        "AI_SCIENTIST_DEFAULT_PROVIDER=google\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_store, "env_path", lambda: env_file)
    yield env_file


def test_mask_secret_short_value():
    assert settings_store.mask_secret("abc") == "***"
    assert settings_store.mask_secret(None) is None
    assert settings_store.mask_secret("") is None


def test_mask_secret_long_value():
    assert settings_store.mask_secret("sk-or-v1-1234567890abcd") == "sk-o…abcd"


def test_read_env_file_skips_comments_and_blank_lines(tmp_env):
    parsed = settings_store.read_env_file()
    assert parsed["GOOGLE_API_KEY"] == "existing-google"
    assert parsed["GROQ_API_KEY"] == "existing-groq"
    assert parsed["AI_SCIENTIST_DEFAULT_PROVIDER"] == "google"


def test_write_env_updates_replaces_value_in_place(tmp_env, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings_store.write_env_updates({"GROQ_API_KEY": "new-groq-value"})
    text = tmp_env.read_text(encoding="utf-8")
    assert "GROQ_API_KEY=new-groq-value" in text
    assert "existing-groq" not in text
    # Order + comments preserved
    assert text.splitlines()[0] == "# header comment"
    # Process env updated in-place so downstream code sees it
    assert os.environ["GROQ_API_KEY"] == "new-groq-value"


def test_write_env_updates_appends_new_keys(tmp_env):
    settings_store.write_env_updates({"OPENROUTER_API_KEY": "sk-or-test"})
    text = tmp_env.read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=sk-or-test" in text
    assert "# Added via Settings UI" in text


def test_write_env_updates_clears_value(tmp_env, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "existing-groq")
    settings_store.write_env_updates({"GROQ_API_KEY": ""})
    text = tmp_env.read_text(encoding="utf-8")
    assert "GROQ_API_KEY=existing-groq" not in text
    assert "# GROQ_API_KEY=" in text  # commented sentinel
    assert "GROQ_API_KEY" not in os.environ


def test_write_env_updates_rejects_unknown_keys(tmp_env):
    # AWS_SECRET_ACCESS_KEY ends in _KEY but not _API_KEY → still rejected.
    with pytest.raises(ValueError, match="Refusing to edit"):
        settings_store.write_env_updates({"AWS_SECRET_ACCESS_KEY": "boom"})


def test_write_env_updates_accepts_custom_api_key(tmp_env):
    settings_store.write_env_updates({"COHERE_API_KEY": "cohere-test"})
    text = tmp_env.read_text(encoding="utf-8")
    assert "COHERE_API_KEY=cohere-test" in text


def test_is_editable_key_validates_pattern():
    assert settings_store.is_editable_key("OPENAI_API_KEY")
    assert settings_store.is_editable_key("COHERE_API_KEY")
    assert settings_store.is_editable_key("MISTRAL_API_KEY")
    assert settings_store.is_editable_key("AI_SCIENTIST_OPENAI_MODEL")

    # Hard rejections
    assert not settings_store.is_editable_key("PATH")
    assert not settings_store.is_editable_key("AWS_SECRET_ACCESS_KEY")
    # Lowercase / shell metacharacters not allowed
    assert not settings_store.is_editable_key("openai_api_key")
    assert not settings_store.is_editable_key("FOO; rm -rf /")
    assert not settings_store.is_editable_key("FOO\nBAR_API_KEY")
    # Too short / no _API_KEY suffix
    assert not settings_store.is_editable_key("X_API_KEY")  # 1-char prefix, < min
    assert not settings_store.is_editable_key("RANDOM_TOKEN")


def test_write_env_updates_rejects_dangerous_custom_key(tmp_env):
    with pytest.raises(ValueError, match="Refusing to edit"):
        settings_store.write_env_updates({"PATH": "/tmp"})
    with pytest.raises(ValueError, match="Refusing to edit"):
        settings_store.write_env_updates({"FOO; rm -rf /": "boom"})


def test_write_env_updates_quotes_values_with_whitespace(tmp_env):
    settings_store.write_env_updates(
        {"AI_SCIENTIST_OPENROUTER_MODEL": "openai/gpt-4o mini"}
    )
    text = tmp_env.read_text(encoding="utf-8")
    assert 'AI_SCIENTIST_OPENROUTER_MODEL="openai/gpt-4o mini"' in text
    # Round-trips back to the unquoted value
    parsed = settings_store.read_env_file()
    assert parsed["AI_SCIENTIST_OPENROUTER_MODEL"] == "openai/gpt-4o mini"


@pytest.fixture
def client(tmp_env, monkeypatch):
    # Make sure the API reads the same fake env file.
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    from ai_scientist.config import get_settings

    get_settings.cache_clear()
    from ai_scientist.api.main import create_app

    app = create_app()
    return TestClient(app)


def test_get_settings_endpoint_returns_masked_keys(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyABCDEFGHIJKLMNOP")
    r = client.get("/settings")
    assert r.status_code == 200
    body = r.json()
    assert "anthropic" in body["providers"]
    assert "openrouter" in body["providers"]
    assert body["providers"]["google"]["key_preview"]
    # Full key never returned
    assert "AIzaSyABCDEFGHIJKLMNOP" not in r.text
    # Editable allowlist is exposed so the UI knows what it can edit
    assert "OPENROUTER_API_KEY" in body["editable_keys"]


def test_post_settings_endpoint_writes_and_returns_masked(client, tmp_env):
    r = client.post(
        "/settings",
        json={"updates": {"OPENROUTER_API_KEY": "sk-or-v1-newvaluefortests"}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["providers"]["openrouter"]["configured"] is True
    assert body["providers"]["openrouter"]["key_preview"]
    assert "sk-or-v1-newvaluefortests" not in r.text
    assert "OPENROUTER_API_KEY=sk-or-v1-newvaluefortests" in tmp_env.read_text(
        encoding="utf-8"
    )


def test_post_settings_endpoint_rejects_unknown_key(client):
    r = client.post(
        "/settings",
        json={"updates": {"AWS_SECRET_ACCESS_KEY": "boom"}},
    )
    assert r.status_code == 400
    assert "Refusing to edit" in r.text


def test_post_settings_endpoint_rejects_empty_payload(client):
    r = client.post("/settings", json={"updates": {}})
    assert r.status_code == 400
