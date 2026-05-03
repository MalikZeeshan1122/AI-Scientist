"""Generate research ideas for a topic, scored by an LLM peer reviewer."""

from __future__ import annotations

import asyncio
import sys

from ai_scientist.ideation import Ideator
from ai_scientist.sources import UnifiedSource


async def main(topic: str, n: int = 4) -> None:
    src = UnifiedSource()
    seed = await src.search(topic, limit=4)
    ideator = Ideator()
    ideas = await ideator.generate(topic, n=n, seed_papers=seed)
    for idea in ideas:
        score = await ideator.score(idea)
        idea.score = score
        print(f"\n=== {idea.title}  (overall {score.overall}) ===")
        print(f"hypothesis: {idea.hypothesis}")
        print(f"method:     {idea.proposed_method}")
        print(f"expected:   {idea.expected_outcome}")
        print(f"score:      novelty={score.novelty} feasibility={score.feasibility} impact={score.impact}")


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "energy-efficient transformer inference"
    asyncio.run(main(topic))
