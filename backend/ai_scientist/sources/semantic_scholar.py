from __future__ import annotations

from datetime import date

import httpx

from ..config import get_settings
from ..models import Paper
from .base import PaperSource

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = (
    "paperId,title,abstract,authors,year,venue,externalIds,openAccessPdf,"
    "citationCount,url,fieldsOfStudy,s2FieldsOfStudy"
)


class SemanticScholarSource(PaperSource):
    name = "semantic_scholar"

    async def search(self, query: str, *, limit: int = 10) -> list[Paper]:
        settings = get_settings()
        headers: dict[str, str] = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        params = {"query": query, "limit": limit, "fields": FIELDS}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            r = await client.get(S2_SEARCH, params=params)
            if r.status_code == 429:
                return []  # rate limited; degrade gracefully
            r.raise_for_status()
            data = r.json()
        out: list[Paper] = []
        for item in data.get("data", []):
            ext = item.get("externalIds") or {}
            doi = ext.get("DOI")
            arxiv_id = ext.get("ArXiv")
            pdf = (item.get("openAccessPdf") or {}).get("url")
            year = item.get("year")
            published = date(year, 1, 1) if year else None
            categories = _collect_categories(item)
            out.append(
                Paper(
                    id=f"s2:{item['paperId']}",
                    source="semantic_scholar",
                    title=item.get("title") or "",
                    abstract=item.get("abstract") or "",
                    authors=[a.get("name", "") for a in item.get("authors", [])],
                    published=published,
                    venue=item.get("venue"),
                    url=item.get("url"),
                    pdf_url=pdf,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    citation_count=item.get("citationCount"),
                    categories=categories,
                    primary_category=categories[0] if categories else None,
                )
            )
        return out


def _collect_categories(item: dict) -> list[str]:
    """Merge ``fieldsOfStudy`` and ``s2FieldsOfStudy`` into a deduplicated list."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(value: str | None) -> None:
        if not value:
            return
        v = value.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)

    for v in item.get("fieldsOfStudy") or []:
        _add(v)
    for v in item.get("s2FieldsOfStudy") or []:
        if isinstance(v, dict):
            _add(v.get("category"))
        elif isinstance(v, str):
            _add(v)
    return out
