from ai_scientist.models import Idea, IdeaScore, Paper


def test_paper_short_id():
    p = Paper(id="arxiv:2401.12345", source="arxiv", title="t")
    assert p.short_id == "2401.12345"


def test_idea_score_overall():
    s = IdeaScore(novelty=8, feasibility=6, impact=7)
    assert s.overall == round((8 + 6 + 7) / 3, 2)


def test_idea_defaults_id():
    i = Idea(
        topic="x",
        title="t",
        hypothesis="h",
        motivation="m",
        proposed_method="pm",
        expected_outcome="eo",
    )
    assert i.id.startswith("idea_")
