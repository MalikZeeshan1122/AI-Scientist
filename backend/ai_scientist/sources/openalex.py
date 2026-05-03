from __future__ import annotations

from datetime import date

import httpx

from ..models import Paper
from .base import PaperSource

OPENALEX = "https://api.openalex.org/works"


class OpenAlexSource(PaperSource):
    name = "openalex"

    async def search(self, query: str, *, limit: int = 10) -> list[Paper]:
        params = {
            "search": query,
            "per-page": limit,
            "sort": "relevance_score:desc",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(OPENALEX, params=params)
            r.raise_for_status()
            data = r.json()
        out: list[Paper] = []
        for item in data.get("results", []):
            oa_id = item["id"].rsplit("/", 1)[-1]
            doi = (item.get("doi") or "").replace("https://doi.org/", "") or None
            primary_location = item.get("primary_location") or {}
            pdf_url = primary_location.get("pdf_url") or (
                item.get("open_access") or {}
            ).get("oa_url")
            authors = [
                (a.get("author") or {}).get("display_name", "")
                for a in item.get("authorships", [])
            ]
            year = item.get("publication_year")
            pub_date_str = item.get("publication_date")
            published: date | None = None
            try:
                if pub_date_str:
                    y, m, d = pub_date_str.split("-")
                    published = date(int(y), int(m), int(d))
                elif year:
                    published = date(year, 1, 1)
            except Exception:
                pass
            abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))
            venue = (
                ((primary_location.get("source") or {}).get("display_name"))
                if primary_location
                else None
            )
            categories = _collect_categories(item)
            primary_topic = (item.get("primary_topic") or {}).get("display_name")
            out.append(
                Paper(
                    id=f"openalex:{oa_id}",
                    source="openalex",
                    title=item.get("title") or "",
                    abstract=abstract,
                    authors=[a for a in authors if a],
                    published=published,
                    venue=venue,
                    url=item.get("id"),
                    pdf_url=pdf_url,
                    doi=doi,
                    citation_count=item.get("cited_by_count"),
                    categories=categories,
                    primary_category=primary_topic or (categories[0] if categories else None),
                )
            )
        return out


def _collect_categories(item: dict) -> list[str]:
    """Build a deduplicated category list from OpenAlex topics + concepts."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(name: str | None) -> None:
        if not name:
            return
        n = name.strip()
        if n and n not in seen:
            seen.add(n)
            out.append(n)

    primary_topic = item.get("primary_topic") or {}
    _add(primary_topic.get("display_name"))

    for topic in item.get("topics") or []:
        _add(topic.get("display_name"))

    # Highest-level OpenAlex concepts are noisier; cap to top-3 by score.
    concepts = sorted(
        item.get("concepts") or [],
        key=lambda c: c.get("score", 0.0),
        reverse=True,
    )
    for c in concepts[:3]:
        _add(c.get("display_name"))

    return out


def _reconstruct_abstract(inv_index: dict | None) -> str:
    if not inv_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)
