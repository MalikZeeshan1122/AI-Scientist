"""arXiv API source.

Implements the conventions from the arXiv API User's Manual:
https://info.arxiv.org/help/api/user-manual.html

Specifically we:
* call the canonical https endpoint with a descriptive User-Agent;
* throttle to >= 3 s between calls (process-wide), as recommended;
* detect Atom error feeds (single entry whose id starts with .../api/errors);
* extract the arxiv: extension elements (doi, journal_ref, primary_category);
* robustly strip the trailing ``v\\d+`` version suffix from ids.
"""

from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from urllib.parse import urlencode

import feedparser
import httpx

from .. import __version__
from ..models import Paper
from .base import PaperSource

ARXIV_API = "https://export.arxiv.org/api/query"
USER_AGENT = f"AI-Scientist/{__version__} (+https://github.com/; arXiv API client)"
_ERROR_ID_PREFIX = "http://arxiv.org/api/errors"
_VERSION_SUFFIX = re.compile(r"v\d+$")


class _MinIntervalLimiter:
    """Process-wide async limiter that ensures >= ``interval_s`` between calls."""

    def __init__(self, interval_s: float) -> None:
        self.interval_s = interval_s
        self._lock = asyncio.Lock()
        self._next_at: float = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            sleep_for = self._next_at - now
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
                now = time.monotonic()
            self._next_at = now + self.interval_s


# arXiv asks callers to space requests >= 3 s apart. Shared across instances.
_ARXIV_RATE_LIMITER = _MinIntervalLimiter(interval_s=3.0)


def _strip_version(arxiv_id: str) -> str:
    """Strip a trailing ``v\\d+`` suffix without breaking ids like ``cond-mat/0207270v1``."""
    return _VERSION_SUFFIX.sub("", arxiv_id)


def _build_query(query: str, categories: list[str]) -> str:
    """Build an arXiv search_query string with optional category restrictions.

    Category syntax is ``cat:cs.LG``; multiple cats are OR-ed and AND-ed with
    the free-text portion: ``all:gnn AND (cat:cs.LG OR cat:stat.ML)``.
    """
    base = f"all:{query.strip()}" if query and query.strip() else "all:*"
    cats = [c.strip() for c in categories if c and c.strip()]
    if not cats:
        return base
    cat_clause = " OR ".join(f"cat:{c}" for c in cats)
    return f"({base}) AND ({cat_clause})"


def _parse_published(value: str | None) -> "datetime.date | None":
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class ArxivSource(PaperSource):
    name = "arxiv"

    def __init__(
        self,
        *,
        rate_limit: bool = True,
        categories: list[str] | None = None,
    ) -> None:
        self._rate_limit = rate_limit
        self._categories = categories or []

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        categories: list[str] | None = None,
    ) -> list[Paper]:
        # arXiv caps slices at 2000 per call.
        max_results = max(1, min(limit, 2000))
        cats = categories if categories is not None else self._categories
        search_query = _build_query(query, cats)
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API}?{urlencode(params)}"
        if self._rate_limit:
            await _ARXIV_RATE_LIMITER.wait()
        async with httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": USER_AGENT}
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            xml = r.text
        return _parse_feed(xml)


def _parse_feed(xml: str) -> list[Paper]:
    feed = feedparser.parse(xml)
    entries = list(getattr(feed, "entries", []))

    # arXiv reports errors as a one-entry feed where the entry id starts with
    # http://arxiv.org/api/errors#... -- treat that as "no results".
    if (
        len(entries) == 1
        and getattr(entries[0], "id", "").startswith(_ERROR_ID_PREFIX)
    ):
        return []

    out: list[Paper] = []
    for entry in entries:
        arxiv_id_raw = entry.id.rsplit("/", 1)[-1]
        arxiv_id = _strip_version(arxiv_id_raw)
        pdf_url = next(
            (
                link.href
                for link in getattr(entry, "links", [])
                if getattr(link, "type", "") == "application/pdf"
            ),
            f"https://arxiv.org/pdf/{arxiv_id_raw}.pdf",
        )
        # arxiv: extension elements (feedparser exposes them under flattened keys).
        doi = getattr(entry, "arxiv_doi", None) or None
        journal_ref = getattr(entry, "arxiv_journal_ref", None) or None
        comment = getattr(entry, "arxiv_comment", None) or None
        venue = (journal_ref.strip() if journal_ref else None) or "arXiv"

        # Categories: feedparser exposes <category term="..."/> as `tags`,
        # and the arxiv:primary_category extension under `arxiv_primary_category`.
        category_terms: list[str] = []
        for tag in getattr(entry, "tags", []) or []:
            term = getattr(tag, "term", None)
            if term:
                category_terms.append(term)
        # Deduplicate while preserving order
        seen: set[str] = set()
        categories = [c for c in category_terms if not (c in seen or seen.add(c))]

        primary_category: str | None = None
        prim = getattr(entry, "arxiv_primary_category", None)
        if isinstance(prim, dict):
            primary_category = prim.get("term") or None
        elif isinstance(prim, str):
            primary_category = prim or None
        if primary_category and primary_category not in categories:
            categories.insert(0, primary_category)
        if not primary_category and categories:
            primary_category = categories[0]

        out.append(
            Paper(
                id=f"arxiv:{arxiv_id}",
                source="arxiv",
                title=entry.title.replace("\n", " ").strip(),
                abstract=entry.summary.replace("\n", " ").strip(),
                authors=[a.name for a in getattr(entry, "authors", [])],
                published=_parse_published(getattr(entry, "published", None)),
                venue=venue,
                url=entry.link,
                pdf_url=pdf_url,
                doi=doi,
                arxiv_id=arxiv_id,
                primary_category=primary_category,
                categories=categories,
                comment=comment.strip() if comment else None,
                journal_ref=journal_ref.strip() if journal_ref else None,
            )
        )
    return out
