from __future__ import annotations

from pydantic import BaseModel, Field

from ..llm import LLMProvider, get_llm
from ..models import Paper

_SYSTEM = (
    "You are an expert research scientist. Read the provided paper text carefully and "
    "produce a precise, faithful structured summary. Do not hallucinate findings that are "
    "not present in the text."
)


class PaperSummary(BaseModel):
    summary: str = Field(description="3-6 sentence faithful summary of the paper")
    contributions: list[str] = Field(description="Bullet list of the paper's stated contributions")
    methods: list[str] = Field(description="Key methods / techniques used")
    findings: list[str] = Field(description="Empirical findings and headline results")
    limitations: list[str] = Field(description="Limitations stated or strongly implied")
    open_questions: list[str] = Field(
        description="Open questions / future work that this paper invites"
    )
    keywords: list[str] = Field(description="3-8 lowercase keywords")


async def summarize_paper(
    paper: Paper,
    full_text: str,
    *,
    llm: LLMProvider | None = None,
    max_chars: int = 18000,
) -> PaperSummary:
    """Summarise a paper. Truncates text to fit context cheaply (head + tail)."""
    llm = llm or get_llm()
    text = full_text.strip() or paper.abstract
    if len(text) > max_chars:
        head = text[: max_chars // 2]
        tail = text[-max_chars // 2 :]
        text = head + "\n\n[... truncated middle ...]\n\n" + tail
    prompt = (
        f"Title: {paper.title}\n"
        f"Authors: {', '.join(paper.authors[:8]) or 'Unknown'}\n"
        f"Venue: {paper.venue or 'Unknown'}\n"
        f"Abstract: {paper.abstract or '(none)'}\n\n"
        f"Full paper text:\n---\n{text}\n---\n\n"
        "Return a JSON summary as specified."
    )
    return await llm.complete_json(prompt, PaperSummary, system=_SYSTEM)
