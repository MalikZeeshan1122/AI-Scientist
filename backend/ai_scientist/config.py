"""Centralised settings, loaded from environment variables / .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_SCIENTIST_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM providers (read directly so people can use vendor-standard names) ---
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    semantic_scholar_api_key: str | None = Field(
        default=None, alias="SEMANTIC_SCHOLAR_API_KEY"
    )
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    default_provider: Literal[
        "anthropic", "google", "groq", "openai", "openrouter"
    ] = "anthropic"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    google_model: str = "gemini-2.0-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    openai_model: str = "gpt-4o-mini"
    # Space out chat-completions when using keys with very low RPM (common free /
    # new-org caps like ~3 RPM → ~20s theoretical minimum for a sliding window).
    # Default ~35s adds slack for clock jitter + concurrent consumers of the same key.
    openai_min_interval_s: float = Field(default=35.0, ge=0.0)
    # Extra seconds added on top of ``openai_min_interval_s`` after OpenAI returns 429,
    # so rolling RPM windows drain before we POST again. Ignored when ``openai_min_interval_s`` is 0.
    openai_rate_limit_extra_sleep_s: float = Field(default=8.0, ge=0.0)
    # OpenRouter brokers many backends; default to a free-tier-friendly model.
    openrouter_model: str = "openai/gpt-4o-mini"
    # Optional referer/title that OpenRouter uses for analytics + free-tier eligibility.
    openrouter_site_url: str = "http://localhost:3000"
    openrouter_app_name: str = "AI Scientist"

    embed_provider: Literal["google"] = "google"
    google_embed_model: str = "gemini-embedding-001"

    # --- Storage ---
    data_dir: Path = Path("./data")
    chroma_dir: Path = Path("./data/chroma")
    db_url: str = "sqlite:///./data/ai_scientist.db"
    pdf_cache: Path = Path("./data/pdfs")
    workspace: Path = Path("./data/workspaces")

    # --- Sandbox ---
    sandbox_timeout_s: int = 120
    sandbox_max_output_bytes: int = 200_000

    # --- API ---
    cors_origins: str = "http://localhost:3000"

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.chroma_dir, self.pdf_cache, self.workspace):
            Path(p).mkdir(parents=True, exist_ok=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
