"""End-to-end run: search papers -> ideate -> experiment -> draft -> refine."""

from __future__ import annotations

import asyncio
import sys

from ai_scientist.models import DraftFormat
from ai_scientist.pipeline import AIScientistPipeline


async def main(topic: str) -> None:
    pipe = AIScientistPipeline()
    result = await pipe.run(
        topic, n_papers=5, n_ideas=4, refine_iters=2, fmt=DraftFormat.MARKDOWN
    )
    print(f"\n=== Project {result.project.id} on '{topic}' ===")
    print(f"papers indexed: {len(result.papers)}")
    print(f"ideas generated: {len(result.ideas)}")
    print(f"chosen idea:    {result.chosen_idea.title}")
    if result.experiment.result:
        print(f"experiment:     {result.experiment.result.status.value}")
        print(f"  metrics:      {result.experiment.result.metrics}")
    print(f"draft path:     {result.draft.rendered_path}")
    if result.improvement:
        print(f"improvement:    {[s.overall for s in result.improvement.history]}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "sparse mixture-of-experts inference"))
