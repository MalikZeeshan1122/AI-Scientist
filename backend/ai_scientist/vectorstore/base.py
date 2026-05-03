from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..models import PaperChunk


class SearchHit(BaseModel):
    paper_id: str
    chunk_index: int
    text: str
    section: str | None = None
    score: float


class VectorStore(ABC):
    @abstractmethod
    async def add(self, chunks: list[PaperChunk]) -> None: ...

    @abstractmethod
    async def search(self, query: str, *, k: int = 6) -> list[SearchHit]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def reset(self) -> None: ...
