from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

# Ensure the package is importable when running `pytest` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _isolated_data_dir(monkeypatch, tmp_path):
    """Point all data paths at a temp dir so tests never touch real storage."""
    monkeypatch.setenv("AI_SCIENTIST_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_SCIENTIST_CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("AI_SCIENTIST_DB_URL", f"sqlite:///{tmp_path / 'db.sqlite'}")
    monkeypatch.setenv("AI_SCIENTIST_PDF_CACHE", str(tmp_path / "pdfs"))
    monkeypatch.setenv("AI_SCIENTIST_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    # Reset the cached settings so the new env vars take effect.
    from ai_scientist.config import get_settings

    get_settings.cache_clear()
    from ai_scientist.llm.factory import get_embedder, get_llm

    get_llm.cache_clear()
    get_embedder.cache_clear()
    yield


class FakeLLM:
    """Deterministic LLM stub used by tests."""

    name = "fake"
    default_model = "fake-model"

    def __init__(self, *, json_payload: Any = None, text_payload: str = "ok"):
        self.json_payload = json_payload
        self.text_payload = text_payload
        self.calls: list[dict] = []

    async def complete(self, messages, **kw):
        self.calls.append({"messages": [m.model_dump() for m in messages], **kw})
        from ai_scientist.llm.base import LLMResponse

        content = (
            json.dumps(self.json_payload)
            if kw.get("json_mode")
            else self.text_payload
        )
        return LLMResponse(content=content, model=self.default_model)

    async def complete_text(self, prompt, **kw):
        self.calls.append({"prompt": prompt, **kw})
        return self.text_payload

    async def complete_json(self, prompt, schema, **kw):
        self.calls.append({"prompt": prompt, "schema": schema.__name__, **kw})
        if self.json_payload is None:
            return schema.model_validate({})
        return schema.model_validate(self.json_payload)


@pytest.fixture
def fake_llm():
    return FakeLLM()
