from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Paper(BaseModel):
    """A normalised representation of a scientific paper, regardless of source."""

    id: str = Field(description="Stable id, e.g. 'arxiv:2401.12345' or 'doi:10.1.../...'")
    source: Literal["arxiv", "semantic_scholar", "openalex", "local", "tavily"]
    title: str
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    published: date | None = None
    venue: str | None = None
    url: HttpUrl | str | None = None
    pdf_url: HttpUrl | str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    citation_count: int | None = None
    primary_category: str | None = Field(
        default=None,
        description="Primary subject category, e.g. 'cs.CV' (arXiv) or normalized field of study.",
    )
    categories: list[str] = Field(
        default_factory=list,
        description="All subject categories the paper belongs to.",
    )
    comment: str | None = Field(
        default=None,
        description="Author's comment, e.g. '12 pages, 5 figures' (arXiv) or accepted-at note.",
    )
    journal_ref: str | None = Field(
        default=None,
        description="Journal reference if the paper has been formally published.",
    )
    summary: str | None = Field(default=None, description="LLM-generated summary")
    key_findings: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def short_id(self) -> str:
        return self.id.split(":", 1)[-1]


class PaperChunk(BaseModel):
    """A chunk of a paper's full text, used for semantic search."""

    paper_id: str
    chunk_index: int
    text: str
    section: str | None = None
