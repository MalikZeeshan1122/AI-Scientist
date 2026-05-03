"""Download an arXiv paper and produce a structured summary."""

from __future__ import annotations

import asyncio
import sys

from ai_scientist.ingestion import extract_pdf_text, summarize_paper
from ai_scientist.sources import ArxivSource


async def main(query: str) -> None:
    src = ArxivSource()
    papers = await src.search(query, limit=1)
    if not papers:
        print("No paper found for query.")
        return
    paper = papers[0]
    print(f"Paper: {paper.title}")
    pdf = await src.fetch_pdf_bytes(paper)
    text = extract_pdf_text(pdf) if pdf else paper.abstract
    summary = await summarize_paper(paper, text)
    print("\nSummary:\n" + summary.summary)
    print("\nFindings:")
    for f in summary.findings:
        print(f"  - {f}")
    print("\nOpen questions:")
    for q in summary.open_questions:
        print(f"  - {q}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "graph neural networks tutorial"))
