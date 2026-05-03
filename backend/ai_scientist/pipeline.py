"""High-level orchestration: search -> ingest -> ideate -> experiment -> draft -> refine."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Sequence

from .experiments import design_experiment, run_experiment
from .ideation import Ideator, score_idea
from .ingestion import chunk_text, extract_pdf_text, summarize_paper
from .llm import LLMProvider, get_llm
from .models import (
    Draft,
    DraftFormat,
    Experiment,
    ExperimentStatus,
    Idea,
    Paper,
)
from .selfimprove import ImprovementReport, refine_draft
from .sources import PaperSource, UnifiedSource
from .storage import Project, Storage
from .vectorstore import ChromaVectorStore, VectorStore
from .writing import draft_paper


@dataclass
class PipelineResult:
    project: Project
    papers: list[Paper]
    ideas: list[Idea]
    chosen_idea: Idea
    experiment: Experiment
    draft: Draft
    improvement: ImprovementReport | None


class AIScientistPipeline:
    def __init__(
        self,
        *,
        llm: LLMProvider | None = None,
        source: PaperSource | None = None,
        vector_store: VectorStore | None = None,
        storage: Storage | None = None,
    ):
        self.llm = llm or get_llm()
        self.source = source or UnifiedSource()
        self.vector_store = vector_store or ChromaVectorStore()
        self.storage = storage or Storage()

    async def search_and_ingest(
        self,
        topic: str,
        *,
        limit: int = 6,
        summarize: bool = True,
        categories: list[str] | None = None,
    ) -> list[Paper]:
        # Pass categories through to UnifiedSource when supported.
        try:
            papers = await self.source.search(topic, limit=limit, categories=categories)
        except TypeError:
            papers = await self.source.search(topic, limit=limit)
        await asyncio.gather(*(self._ingest_paper(p, summarize=summarize) for p in papers))
        return papers

    async def _ingest_paper(self, paper: Paper, *, summarize: bool) -> None:
        try:
            pdf_bytes = await self.source.fetch_pdf_bytes(paper)
        except Exception:
            pdf_bytes = None
        text = ""
        if pdf_bytes:
            try:
                text = extract_pdf_text(pdf_bytes)
            except Exception:
                text = ""
        text = text or paper.abstract
        if text:
            chunks = chunk_text(paper.id, text)
            try:
                await self.vector_store.add(chunks)
            except Exception:
                pass
        if summarize and text:
            try:
                summary = await summarize_paper(paper, text, llm=self.llm)
                paper.summary = summary.summary
                paper.key_findings = summary.findings
                paper.open_questions = summary.open_questions
            except Exception:
                pass
        self.storage.save_paper(paper)

    async def ideate(
        self, topic: str, papers: Sequence[Paper], *, n: int = 5
    ) -> list[Idea]:
        ideator = Ideator(llm=self.llm, vector_store=self.vector_store)
        ideas = await ideator.generate(topic, n=n, seed_papers=list(papers))
        # OpenAI free tiers (~3 RPM) behave poorly under asyncio.gather: many tasks
        # pile up even though the provider serializes POSTs; score sequentially so pacing stays predictable.
        if getattr(self.llm, "name", None) == "openai":
            scored = [await score_idea(i, llm=self.llm) for i in ideas]
        else:
            scored = await asyncio.gather(*(score_idea(i, llm=self.llm) for i in ideas))
        for idea, score in zip(ideas, scored):
            idea.score = score
            self.storage.save_idea(idea)
        ideas.sort(key=lambda i: (i.score.overall if i.score else 0), reverse=True)
        return ideas

    async def experiment(self, idea: Idea) -> Experiment:
        exp = await design_experiment(idea, llm=self.llm)
        exp = await run_experiment(exp, llm=self.llm)
        self.storage.save_experiment(exp)
        return exp

    async def write(
        self,
        idea: Idea,
        experiment: Experiment | None,
        related: list[Paper] | None,
        *,
        fmt: DraftFormat = DraftFormat.MARKDOWN,
    ) -> Draft:
        draft = await draft_paper(idea, experiment, related, fmt=fmt, llm=self.llm)
        self.storage.save_draft(draft)
        return draft

    async def refine(self, draft: Draft, *, max_iters: int = 2) -> ImprovementReport:
        report = await refine_draft(draft, max_iters=max_iters, llm=self.llm)
        self.storage.save_draft(report.final)
        return report

    async def run(
        self,
        topic: str,
        *,
        n_papers: int = 6,
        n_ideas: int = 5,
        refine_iters: int = 2,
        fmt: DraftFormat = DraftFormat.MARKDOWN,
        categories: list[str] | None = None,
    ) -> PipelineResult:
        project = self.storage.create_project(topic)
        papers = await self.search_and_ingest(
            topic, limit=n_papers, categories=categories
        )
        ideas = await self.ideate(topic, papers, n=n_ideas)
        chosen = ideas[0]
        experiment = await self.experiment(chosen)
        draft = await self.write(
            chosen,
            experiment if experiment.result and experiment.result.status != ExperimentStatus.FAILED else experiment,
            papers,
            fmt=fmt,
        )
        report = await self.refine(draft, max_iters=refine_iters) if refine_iters > 0 else None
        return PipelineResult(
            project=project,
            papers=papers,
            ideas=ideas,
            chosen_idea=chosen,
            experiment=experiment,
            draft=report.final if report else draft,
            improvement=report,
        )
