from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class DraftFormat(str, Enum):
    MARKDOWN = "markdown"
    LATEX = "latex"


class DraftSection(BaseModel):
    name: str
    content: str


class Draft(BaseModel):
    id: str = Field(default_factory=lambda: f"draft_{uuid4().hex[:10]}")
    idea_id: str | None = None
    experiment_id: str | None = None
    title: str
    abstract: str
    sections: list[DraftSection] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    format: DraftFormat = DraftFormat.MARKDOWN
    rendered_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
