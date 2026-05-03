from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Paper


class PaperSource(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, *, limit: int = 10) -> list[Paper]: ...

    async def fetch_pdf_bytes(self, paper: Paper) -> bytes | None:
        """Optional. Default implementation downloads paper.pdf_url with httpx."""
        if not paper.pdf_url:
            return None
        import httpx

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            r = await client.get(str(paper.pdf_url))
            if r.status_code != 200:
                return None
            return r.content
