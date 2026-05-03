from __future__ import annotations

import re

from ..models import PaperChunk

_SECTION_RE = re.compile(
    r"^(\s*\d+(\.\d+)*\s+)?(abstract|introduction|background|related work|methods?|"
    r"approach|experiments?|results?|discussion|conclusion|references)\b",
    re.IGNORECASE | re.MULTILINE,
)


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Best-effort split into (section_name, body) tuples; falls back to one block."""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return [("body", text)]
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        name = m.group(3).strip().lower()
        out.append((name, text[start:end].strip()))
    return out


def chunk_text(
    paper_id: str,
    text: str,
    *,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> list[PaperChunk]:
    """Split text into overlapping word-windowed chunks, tagged by section."""
    if not text.strip():
        return []
    chunks: list[PaperChunk] = []
    idx = 0
    for section, body in _split_sections(text):
        words = body.split()
        if not words:
            continue
        step = max(1, chunk_size - overlap)
        for start in range(0, len(words), step):
            window = words[start : start + chunk_size]
            if not window:
                break
            chunks.append(
                PaperChunk(
                    paper_id=paper_id,
                    chunk_index=idx,
                    text=" ".join(window),
                    section=section,
                )
            )
            idx += 1
            if start + chunk_size >= len(words):
                break
    return chunks
