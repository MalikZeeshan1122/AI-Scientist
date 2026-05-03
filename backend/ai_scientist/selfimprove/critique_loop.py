"""Self-improvement loop: the agent critiques its own draft, scores it,
proposes targeted edits, and re-drafts until quality stops improving.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..llm import LLMProvider, get_llm
from ..models import Draft
from ..writing.latex_writer import render_latex
from ..writing.markdown_writer import render_markdown

_REVIEWER_SYSTEM = (
    "You are a strict but constructive peer reviewer (NeurIPS / ICML calibre). Identify "
    "concrete weaknesses, missing controls, unsupported claims, and unclear writing. "
    "Be specific; cite section names. Score honestly."
)


class CritiqueScore(BaseModel):
    soundness: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    novelty: float = Field(ge=0, le=10)
    significance: float = Field(ge=0, le=10)

    @property
    def overall(self) -> float:
        return round(
            (self.soundness + self.clarity + self.novelty + self.significance) / 4, 2
        )


class CritiqueReport(BaseModel):
    score: CritiqueScore
    strengths: list[str]
    weaknesses: list[str]
    actionable_edits: list[str] = Field(
        description="Concrete, section-targeted edits the author should make"
    )


class _RewrittenDraft(BaseModel):
    title: str
    abstract: str
    sections: list[dict]
    references: list[str]


class ImprovementReport(BaseModel):
    iterations: int
    history: list[CritiqueScore] = Field(default_factory=list)
    final: Draft
    final_critique: CritiqueReport


class CritiqueLoop:
    def __init__(self, *, llm: LLMProvider | None = None):
        self.llm = llm or get_llm()

    async def critique(self, draft: Draft) -> CritiqueReport:
        rendered = render_markdown(draft)
        prompt = (
            "Review this draft carefully. Return JSON only.\n\n"
            f"---\n{rendered[:18000]}\n---"
        )
        return await self.llm.complete_json(prompt, CritiqueReport, system=_REVIEWER_SYSTEM)

    async def revise(self, draft: Draft, critique: CritiqueReport) -> Draft:
        rendered = render_markdown(draft)
        edits = "\n".join(f"- {e}" for e in critique.actionable_edits)
        prompt = (
            "Rewrite the draft to address EVERY actionable edit below. Preserve the section "
            "ordering. Be precise; do not introduce unsupported claims.\n\n"
            f"=== Required edits ===\n{edits}\n\n"
            f"=== Current draft (Markdown) ===\n{rendered[:16000]}"
        )
        revised = await self.llm.complete_json(
            prompt, _RewrittenDraft, system="You are an academic writer revising your draft."
        )
        from ..models import DraftSection

        new = draft.model_copy(deep=True)
        new.title = revised.title
        new.abstract = revised.abstract
        new.sections = [DraftSection(**s) for s in revised.sections]
        new.references = revised.references
        return new

    async def loop(
        self,
        draft: Draft,
        *,
        max_iters: int = 3,
        min_improvement: float = 0.2,
        output_dir: Path | None = None,
    ) -> ImprovementReport:
        history: list[CritiqueScore] = []
        current = draft
        last_overall = -1.0
        critique: CritiqueReport | None = None
        iters = 0
        for i in range(max_iters):
            iters = i + 1
            critique = await self.critique(current)
            history.append(critique.score)
            improvement = critique.score.overall - last_overall
            last_overall = critique.score.overall
            if i > 0 and improvement < min_improvement:
                break
            if i == max_iters - 1:
                break
            current = await self.revise(current, critique)

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            ext = "md" if current.format.value == "markdown" else "tex"
            path = output_dir / f"{current.id}_revised.{ext}"
            renderer = render_markdown if ext == "md" else render_latex
            path.write_text(renderer(current), encoding="utf-8")
            current.rendered_path = str(path)

        assert critique is not None
        return ImprovementReport(
            iterations=iters, history=history, final=current, final_critique=critique
        )


async def refine_draft(
    draft: Draft,
    *,
    max_iters: int = 3,
    llm: LLMProvider | None = None,
    output_dir: Path | None = None,
) -> ImprovementReport:
    return await CritiqueLoop(llm=llm).loop(draft, max_iters=max_iters, output_dir=output_dir)
