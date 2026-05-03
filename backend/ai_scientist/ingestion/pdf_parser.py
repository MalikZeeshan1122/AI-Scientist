from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(source: Path | bytes) -> str:
    """Extract text from a PDF, given a path or raw bytes. Best-effort, no OCR."""
    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
    else:
        reader = PdfReader(BytesIO(source))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(parts).strip()


def extract_first_page(source: Path | bytes) -> str:
    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
    else:
        reader = PdfReader(BytesIO(source))
    if not reader.pages:
        return ""
    try:
        return (reader.pages[0].extract_text() or "").strip()
    except Exception:
        return ""
