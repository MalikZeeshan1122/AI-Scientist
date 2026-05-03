import pytest

from ai_scientist.ideation import Ideator
from ai_scientist.models import IdeaScore


@pytest.mark.asyncio
async def test_ideator_generates(fake_llm):
    fake_llm.json_payload = {
        "ideas": [
            {
                "topic": "ml",
                "title": "Idea A",
                "hypothesis": "h",
                "motivation": "m",
                "proposed_method": "pm",
                "expected_outcome": "eo",
                "related_paper_ids": ["arxiv:1"],
                "keywords": ["k1", "k2"],
            }
        ]
    }
    ideator = Ideator(llm=fake_llm)
    ideas = await ideator.generate("ml", n=1)
    assert len(ideas) == 1
    assert ideas[0].title == "Idea A"
    assert ideas[0].topic == "ml"


@pytest.mark.asyncio
async def test_ideator_scores(fake_llm):
    fake_llm.json_payload = {
        "score": {"novelty": 8, "feasibility": 7, "impact": 9, "rationale": "ok"}
    }
    from ai_scientist.models import Idea

    idea = Idea(
        topic="x", title="t", hypothesis="h", motivation="m",
        proposed_method="pm", expected_outcome="eo",
    )
    score = await Ideator(llm=fake_llm).score(idea)
    assert isinstance(score, IdeaScore)
    assert score.overall == round((8 + 7 + 9) / 3, 2)
