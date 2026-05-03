from __future__ import annotations

import asyncio
from pathlib import Path

from ..config import get_settings
from ..models import Paper
from .arxiv import ArxivSource
from .base import PaperSource
from .local_pdf import LocalPdfSource
from .openalex import OpenAlexSource
from .semantic_scholar import SemanticScholarSource
from .tavily import TavilySource


class UnifiedSource(PaperSource):
    """Fan-out search across all configured sources, then de-duplicate."""

    name = "unified"

    def __init__(
        self,
        *,
        include_arxiv: bool = True,
        include_semantic_scholar: bool = True,
        include_openalex: bool = True,
        include_local: bool = True,
        include_tavily: bool | None = None,
        local_folder: Path | str | None = None,
    ):
        settings = get_settings()
        self._sources: list[PaperSource] = []
        if include_arxiv:
            self._sources.append(ArxivSource())
        if include_semantic_scholar:
            self._sources.append(SemanticScholarSource())
        if include_openalex:
            self._sources.append(OpenAlexSource())
        if include_local:
            self._sources.append(LocalPdfSource(local_folder or settings.pdf_cache))
        # Tavily is auto-enabled when an API key is configured (override with the flag)
        if include_tavily is True or (include_tavily is None and settings.tavily_api_key):
            self._sources.append(TavilySource())

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        categories: list[str] | None = None,
    ) -> list[Paper]:
        per_source = max(1, limit)
        results = await asyncio.gather(
            *[_safe_search(s, query, per_source, categories) for s in self._sources],
            return_exceptions=False,
        )
        merged: dict[str, Paper] = {}
        for batch in results:
            for paper in batch:
                key = _dedupe_key(paper)
                if key not in merged:
                    merged[key] = paper
                else:
                    # Prefer the entry with citation count / pdf
                    existing = merged[key]
                    if paper.pdf_url and not existing.pdf_url:
                        merged[key] = paper
        candidates = list(merged.values())
        # For non-arXiv sources we apply a post-hoc category filter (best-effort
        # match against any of the paper's categories or its primary one).
        if categories:
            wanted = {c.strip().lower() for c in categories if c and c.strip()}
            if wanted:
                candidates = [
                    p
                    for p in candidates
                    if _matches_categories(p, wanted)
                ]
        ranked = sorted(
            candidates,
            key=lambda p: (p.citation_count or 0),
            reverse=True,
        )
        return ranked[:limit]

    async def fetch_pdf_bytes(self, paper: Paper) -> bytes | None:
        for src in self._sources:
            if src.name == paper.source:
                return await src.fetch_pdf_bytes(paper)
        return await super().fetch_pdf_bytes(paper)


async def _safe_search(
    src: PaperSource,
    query: str,
    limit: int,
    categories: list[str] | None = None,
) -> list[Paper]:
    try:
        # Only ArxivSource (and UnifiedSource itself) takes a categories kwarg.
        if isinstance(src, ArxivSource):
            return await src.search(query, limit=limit, categories=categories)
        return await src.search(query, limit=limit)
    except Exception:
        return []


def _matches_categories(p: Paper, wanted: set[str]) -> bool:
    """Return True when the paper has at least one matching category.

    Matching is case-insensitive and treats arXiv prefix matches loosely so
    'cs' matches 'cs.LG' (useful when a user picks a coarse category).
    """
    haystack: list[str] = []
    if p.primary_category:
        haystack.append(p.primary_category.lower())
    haystack.extend(c.lower() for c in p.categories or [])
    if not haystack:
        # If the source didn't return categories at all, keep the paper rather
        # than silently dropping it (best-effort filter).
        return p.source != "arxiv"
    for c in haystack:
        for w in wanted:
            if c == w or c.startswith(w + "."):
                return True
    return False


def _dedupe_key(p: Paper) -> str:
    if p.doi:
        return f"doi:{p.doi.lower()}"
    if p.arxiv_id:
        return f"arxiv:{p.arxiv_id.lower()}"
    # Tavily results have no DOI/arxiv id but each URL is distinct → key on URL
    if p.source == "tavily" and p.url:
        return f"url:{str(p.url).lower()}"
    return f"title:{p.title.strip().lower()[:120]}"
