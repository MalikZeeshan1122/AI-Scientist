"""Tavily web-search source.

Tavily is an LLM-oriented web search API. It's not a paper database, so results
won't have authors/DOIs/citations — but for surveying live web context (blog
posts, docs, code, news) it complements the academic sources nicely.

We talk to Tavily over HTTPS with `httpx.AsyncClient` rather than the official
`tavily-python` SDK because that SDK is synchronous and would block our
FastAPI event loop during searches.

Docs: https://docs.tavily.com
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Literal

import httpx

from ..config import get_settings
from ..models import Paper
from .base import PaperSource

TAVILY_ENDPOINT = "https://api.tavily.com/search"

SearchDepth = Literal["basic", "advanced"]
IncludeAnswer = Literal[False, True, "basic", "advanced"]


class TavilySource(PaperSource):
    name = "tavily"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        search_depth: SearchDepth = "advanced",
        include_answer: IncludeAnswer = False,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ):
        self.api_key = api_key or get_settings().tavily_api_key
        self.search_depth = search_depth
        self.include_answer = include_answer
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        # Populated after the most recent search, when include_answer != False
        self.last_answer: str | None = None

    async def search(self, query: str, *, limit: int = 10) -> list[Paper]:
        if not self.api_key:
            return []

        payload: dict = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max(1, min(limit, 20)),
            "search_depth": self.search_depth,
            "include_answer": self.include_answer,
            "include_raw_content": False,
        }
        if self.include_domains:
            payload["include_domains"] = self.include_domains
        if self.exclude_domains:
            payload["exclude_domains"] = self.exclude_domains

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(TAVILY_ENDPOINT, json=payload)
            r.raise_for_status()
            data = r.json()

        self.last_answer = data.get("answer") or None

        out: list[Paper] = []
        for item in data.get("results", []):
            url = item.get("url") or ""
            if not url:
                continue
            digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
            out.append(
                Paper(
                    id=f"tavily:{digest}",
                    source="tavily",
                    title=(item.get("title") or url)[:500],
                    abstract=item.get("content") or "",
                    url=url,
                    published=_parse_date(item.get("published_date")),
                )
            )
        return out


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value[: len(fmt) + 4], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
