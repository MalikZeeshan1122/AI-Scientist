from __future__ import annotations

from pydantic import BaseModel, Field

from ..llm import LLMProvider, get_llm
from ..models import Idea, IdeaScore, Paper
from ..vectorstore import SearchHit, VectorStore

_IDEATION_SYSTEM = (
    "You are a senior research scientist proposing rigorous, NOVEL research directions. "
    "Avoid trivial extensions. Each idea must be: testable in <1 week of compute on a "
    "single GPU/CPU machine, well-motivated, and clearly distinct from existing work. "
    "Ground every idea in the provided paper context."
)


class _IdeaList(BaseModel):
    ideas: list[Idea] = Field(min_length=1)


class _ScoreResp(BaseModel):
    score: IdeaScore


class Ideator:
    """Generates ideas grounded in indexed papers."""

    def __init__(
        self,
        *,
        llm: LLMProvider | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.llm = llm or get_llm()
        self.vs = vector_store

    async def _retrieve_context(self, topic: str, k: int = 6) -> list[SearchHit]:
        if self.vs is None:
            return []
        return await self.vs.search(topic, k=k)

    async def generate(
        self,
        topic: str,
        *,
        n: int = 5,
        seed_papers: list[Paper] | None = None,
        extra_context: str | None = None,
    ) -> list[Idea]:
        hits = await self._retrieve_context(topic)
        ctx_blocks: list[str] = []
        if seed_papers:
            for p in seed_papers[:8]:
                ctx_blocks.append(
                    f"[{p.id}] {p.title}\nAuthors: {', '.join(p.authors[:5])}\n"
                    f"Abstract: {p.abstract[:800]}"
                )
        for h in hits:
            ctx_blocks.append(f"[{h.paper_id} #{h.chunk_index} | {h.section}] {h.text[:800]}")
        if extra_context:
            ctx_blocks.append(f"[user-context] {extra_context}")
        ctx = "\n\n---\n\n".join(ctx_blocks) if ctx_blocks else "(no prior context provided)"

        prompt = (
            f"Topic: {topic}\n\n"
            f"Background context (papers, chunks, user notes):\n{ctx}\n\n"
            f"Propose exactly {n} distinct research ideas. Each must include: title, "
            "hypothesis, motivation, proposed_method (concrete steps), expected_outcome, "
            "related_paper_ids (cite from the IDs above), and 3-6 keywords. Do NOT include "
            "any 'score' field. Set 'topic' to the user's topic."
        )
        resp = await self.llm.complete_json(prompt, _IdeaList, system=_IDEATION_SYSTEM)
        for idea in resp.ideas:
            idea.topic = topic
        return resp.ideas

    async def score(self, idea: Idea) -> IdeaScore:
        prompt = (
            "Critically score the following research idea on novelty, feasibility, and impact "
            "(each 0-10). Be conservative; reserve 9-10 for outstanding scores. Provide a "
            "1-3 sentence rationale.\n\n"
            f"Title: {idea.title}\n"
            f"Hypothesis: {idea.hypothesis}\n"
            f"Method: {idea.proposed_method}\n"
            f"Expected outcome: {idea.expected_outcome}\n"
        )
        resp = await self.llm.complete_json(
            prompt, _ScoreResp, system="You are a strict, fair peer reviewer."
        )
        return resp.score


async def generate_ideas(
    topic: str,
    *,
    n: int = 5,
    vector_store: VectorStore | None = None,
    seed_papers: list[Paper] | None = None,
    llm: LLMProvider | None = None,
) -> list[Idea]:
    return await Ideator(llm=llm, vector_store=vector_store).generate(
        topic, n=n, seed_papers=seed_papers
    )


async def score_idea(idea: Idea, *, llm: LLMProvider | None = None) -> IdeaScore:
    return await Ideator(llm=llm).score(idea)
