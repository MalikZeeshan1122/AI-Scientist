"""Draft a workshop-style paper from an idea + experiment, then refine via critique loop."""

from __future__ import annotations

import asyncio

from ai_scientist.experiments import design_experiment, run_experiment
from ai_scientist.models import DraftFormat, Idea
from ai_scientist.selfimprove import refine_draft
from ai_scientist.writing import draft_paper


async def main() -> None:
    idea = Idea(
        topic="curriculum learning",
        title="Easy-to-hard curriculum for tiny char-level LM on Wikipedia subset",
        hypothesis="Sorting training docs by length produces lower validation perplexity.",
        motivation="Curriculum learning sometimes helps; sometimes hurts. Small controlled test.",
        proposed_method="Train a 1-layer GRU on 5k random Wikipedia paragraphs vs the same sorted by length.",
        expected_outcome="Sorted curriculum yields ~3% lower validation perplexity.",
    )
    exp = await design_experiment(idea)
    exp = await run_experiment(exp)

    draft = await draft_paper(idea, exp, related=None, fmt=DraftFormat.MARKDOWN)
    print(f"draft saved to: {draft.rendered_path}")

    report = await refine_draft(draft, max_iters=2)
    print(f"\nself-improvement scores: {[s.overall for s in report.history]}")
    print(f"final saved to: {report.final.rendered_path}")


if __name__ == "__main__":
    asyncio.run(main())
