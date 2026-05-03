from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from ..models import Paper
from .base import PaperSource


class LocalPdfSource(PaperSource):
    """Treats a folder of PDFs as a paper source.

    Search is naive substring match against filename + first-page text.
    Use the ingestion module for richer text extraction & summarisation.
    """

    name = "local"

    def __init__(self, folder: Path | str):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    async def search(self, query: str, *, limit: int = 10) -> list[Paper]:
        from ..ingestion.pdf_parser import extract_first_page

        q = query.lower().strip()
        results: list[tuple[float, Paper]] = []
        for pdf in sorted(self.folder.glob("**/*.pdf")):
            first = ""
            try:
                first = extract_first_page(pdf)
            except Exception:
                first = ""
            haystack = f"{pdf.name}\n{first}".lower()
            if q and q not in haystack:
                continue
            score = haystack.count(q) if q else 1.0
            paper_id = "local:" + hashlib.sha1(str(pdf.resolve()).encode()).hexdigest()[:12]
            title = first.split("\n", 1)[0].strip()[:200] if first else pdf.stem
            results.append(
                (
                    score,
                    Paper(
                        id=paper_id,
                        source="local",
                        title=title or pdf.stem,
                        abstract=first[:1000],
                        authors=[],
                        published=date.today(),
                        venue=None,
                        url=str(pdf.resolve()),
                        pdf_url=str(pdf.resolve()),
                    ),
                )
            )
        results.sort(key=lambda t: t[0], reverse=True)
        return [p for _, p in results[:limit]]

    async def fetch_pdf_bytes(self, paper: Paper) -> bytes | None:
        if paper.pdf_url and Path(str(paper.pdf_url)).exists():
            return Path(str(paper.pdf_url)).read_bytes()
        return None
