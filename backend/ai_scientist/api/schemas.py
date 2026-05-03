from __future__ import annotations

from pydantic import BaseModel, Field

from ..models import Idea


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(8, ge=1, le=50)
    categories: list[str] | None = Field(
        default=None,
        description="Optional list of arXiv-style category codes (e.g. ['cs.LG', 'cs.AI']) to restrict the search.",
    )


class IdeateRequest(BaseModel):
    topic: str
    n: int = Field(5, ge=1, le=10)
    project_id: str | None = None


class ExperimentRequest(BaseModel):
    idea: Idea


class DraftRequest(BaseModel):
    idea: Idea
    experiment_id: str | None = None
    fmt: str = "markdown"


class RunPipelineRequest(BaseModel):
    topic: str
    n_papers: int = Field(6, ge=1, le=20)
    n_ideas: int = Field(5, ge=1, le=10)
    refine_iters: int = Field(2, ge=0, le=5)
    fmt: str = "markdown"
    categories: list[str] | None = Field(
        default=None,
        description="Optional list of arXiv-style category codes to restrict paper search.",
    )


class SettingsUpdateRequest(BaseModel):
    """Partial update to the on-disk `.env` from the in-app Settings page.

    Only keys present in :data:`ai_scientist.settings_store.EDITABLE_KEYS`
    are accepted; everything else is rejected by the server. Send an empty
    string to clear (comment out) a key.
    """

    updates: dict[str, str] = Field(
        default_factory=dict,
        description="Map of ENV key -> new value. Empty string clears the key.",
    )
