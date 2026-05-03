from ai_scientist.models import (
    Draft,
    DraftFormat,
    DraftSection,
    Experiment,
    ExperimentResult,
    ExperimentStatus,
    Idea,
    IdeaScore,
    Paper,
)
from ai_scientist.storage import Storage


def _idea() -> Idea:
    return Idea(
        topic="t", title="ti", hypothesis="h", motivation="m",
        proposed_method="pm", expected_outcome="eo",
        score=IdeaScore(novelty=5, feasibility=5, impact=5),
    )


def test_storage_roundtrip(tmp_path):
    s = Storage(db_path=tmp_path / "x.db")
    proj = s.create_project("ml")
    paper = Paper(id="arxiv:1", source="arxiv", title="t")
    s.save_paper(paper, project_id=proj.id)
    idea = _idea()
    s.save_idea(idea, project_id=proj.id)
    exp = Experiment(
        idea_id=idea.id, title="e", description="d", code="print(1)",
        result=ExperimentResult(status=ExperimentStatus.SUCCEEDED, returncode=0, duration_s=0.1),
    )
    s.save_experiment(exp, project_id=proj.id)
    draft = Draft(
        title="t",
        abstract="a",
        sections=[DraftSection(name="Intro", content="hi")],
        format=DraftFormat.MARKDOWN,
        idea_id=idea.id,
        experiment_id=exp.id,
    )
    s.save_draft(draft, project_id=proj.id)

    assert {p.id for p in s.list_papers(proj.id)} == {paper.id}
    assert {i.id for i in s.list_ideas(proj.id)} == {idea.id}
    assert {e.id for e in s.list_experiments(proj.id)} == {exp.id}
    assert {d.id for d in s.list_drafts(proj.id)} == {draft.id}

    fetched = s.get_project(proj.id)
    assert fetched and fetched.topic == "ml"
