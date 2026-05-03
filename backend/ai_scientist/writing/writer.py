from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..config import get_settings
from ..llm import LLMProvider, get_llm
from ..models import Draft, DraftFormat, DraftSection, Experiment, Idea, Paper
from .latex_writer import render_latex
from .markdown_writer import render_markdown

_SYSTEM = (
    "You are an academic writer drafting a short workshop-style paper. Be precise, avoid "
    "overclaiming, and ground every quantitative statement in the provided experiment "
    "results. Keep prose tight and technical. Use the conventional sections."
)


class _DraftJSON(BaseModel):
    title: str
    abstract: str = Field(description="150-250 word abstract")
    sections: list[DraftSection] = Field(
        description=(
            "Sections in order: Introduction, Background, Method, Experiments, "
            "Results, Discussion, Limitations, Future Work, Conclusion"
        )
    )
    references: list[str] = Field(
        description="Plain-text reference strings (one per related paper)"
    )


async def draft_paper(
    idea: Idea,
    experiment: Experiment | None,
    related: list[Paper] | None = None,
    *,
    fmt: DraftFormat = DraftFormat.MARKDOWN,
    llm: LLMProvider | None = None,
    output_dir: Path | None = None,
) -> Draft:
    llm = llm or get_llm()
    settings = get_settings()
    output_dir = output_dir or settings.workspace / "drafts"
    output_dir.mkdir(parents=True, exist_ok=True)

    related_block = "(no related work supplied)"
    if related:
        related_block = "\n".join(
            f"[{p.id}] {p.title} — {', '.join(p.authors[:3])}" for p in related[:15]
        )

    exp_block = "(no experiment was run)"
    if experiment and experiment.result:
        r = experiment.result
        exp_block = (
            f"Title: {experiment.title}\n"
            f"Description: {experiment.description}\n"
            f"Status: {r.status.value}\n"
            f"Duration: {r.duration_s:.1f}s\n"
            f"Metrics: {r.metrics}\n"
            f"Stdout (head):\n{r.stdout[:3000]}\n"
        )

    prompt = (
        f"Draft a paper for the following idea and experiment.\n\n"
        f"=== Idea ===\n"
        f"Title: {idea.title}\nHypothesis: {idea.hypothesis}\n"
        f"Motivation: {idea.motivation}\nMethod: {idea.proposed_method}\n"
        f"Expected outcome: {idea.expected_outcome}\n\n"
        f"=== Experiment ===\n{exp_block}\n\n"
        f"=== Related work ===\n{related_block}\n"
    )
    parsed = await llm.complete_json(prompt, _DraftJSON, system=_SYSTEM, max_tokens=6000)

    draft = Draft(
        idea_id=idea.id,
        experiment_id=experiment.id if experiment else None,
        title=parsed.title,
        abstract=parsed.abstract,
        sections=parsed.sections,
        references=parsed.references,
        format=fmt,
    )
    if fmt is DraftFormat.MARKDOWN:
        path = output_dir / f"{draft.id}.md"
        path.write_text(render_markdown(draft), encoding="utf-8")
    else:
        path = output_dir / f"{draft.id}.tex"
        path.write_text(render_latex(draft), encoding="utf-8")
    draft.rendered_path = str(path)
    return draft
