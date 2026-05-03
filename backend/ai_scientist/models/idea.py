from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class IdeaScore(BaseModel):
    novelty: float = Field(ge=0, le=10)
    feasibility: float = Field(ge=0, le=10)
    impact: float = Field(ge=0, le=10)
    rationale: str = ""

    @property
    def overall(self) -> float:
        return round((self.novelty + self.feasibility + self.impact) / 3, 2)


class Idea(BaseModel):
    id: str = Field(default_factory=lambda: f"idea_{uuid4().hex[:10]}")
    topic: str
    title: str
    hypothesis: str
    motivation: str
    proposed_method: str
    expected_outcome: str
    related_paper_ids: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    score: IdeaScore | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
