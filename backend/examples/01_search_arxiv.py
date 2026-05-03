"""Search across all configured paper sources for a topic."""

from __future__ import annotations

import asyncio
import sys

from ai_scientist.sources import UnifiedSource


async def main(query: str = "diffusion models for protein design", limit: int = 6) -> None:
    src = UnifiedSource()
    papers = await src.search(query, limit=limit)
    for p in papers:
        print(f"- [{p.source}] {p.title}")
        print(f"    id={p.id}  cites={p.citation_count}  pdf={p.pdf_url}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "diffusion models for protein design"
    asyncio.run(main(q))
