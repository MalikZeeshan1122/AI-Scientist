from __future__ import annotations

from pathlib import Path

from ..config import get_settings
from ..llm import get_embedder
from ..llm.base import EmbeddingProvider
from ..models import PaperChunk
from .base import SearchHit, VectorStore


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB-backed store. Uses the configured embedding provider."""

    def __init__(
        self,
        *,
        persist_dir: Path | str | None = None,
        collection: str = "papers",
        embedder: EmbeddingProvider | None = None,
    ):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        settings = get_settings()
        self._dir = Path(persist_dir or settings.chroma_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self._dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=collection)
        self._embedder = embedder or get_embedder()

    async def add(self, chunks: list[PaperChunk]) -> None:
        if not chunks:
            return
        ids = [f"{c.paper_id}::{c.chunk_index}" for c in chunks]
        docs = [c.text for c in chunks]
        metas = [
            {"paper_id": c.paper_id, "chunk_index": c.chunk_index, "section": c.section or ""}
            for c in chunks
        ]
        embeddings = await self._embedder.embed(docs)
        self._collection.upsert(
            ids=ids, documents=docs, metadatas=metas, embeddings=embeddings
        )

    async def search(self, query: str, *, k: int = 6) -> list[SearchHit]:
        if (await self.count()) == 0:
            return []
        embeddings = await self._embedder.embed([query])
        if not embeddings:
            return []
        res = self._collection.query(
            query_embeddings=embeddings, n_results=k, include=["documents", "metadatas", "distances"]
        )
        out: list[SearchHit] = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            out.append(
                SearchHit(
                    paper_id=meta.get("paper_id", _id.split("::", 1)[0]),
                    chunk_index=int(meta.get("chunk_index", 0) or 0),
                    text=doc,
                    section=meta.get("section") or None,
                    score=1.0 - float(dist),
                )
            )
        return out

    async def count(self) -> int:
        return int(self._collection.count())

    async def reset(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(name=name)
