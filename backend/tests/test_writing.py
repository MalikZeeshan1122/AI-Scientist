from ai_scientist.models import Draft, DraftFormat, DraftSection
from ai_scientist.writing import render_latex, render_markdown


def _draft(fmt: DraftFormat) -> Draft:
    return Draft(
        title="My Title",
        abstract="abs $x$ & y",
        sections=[
            DraftSection(name="Intro", content="hello world"),
            DraftSection(name="Results", content="metric=42"),
        ],
        references=["Smith et al. 2024"],
        format=fmt,
    )


def test_render_markdown_contains_sections():
    md = render_markdown(_draft(DraftFormat.MARKDOWN))
    assert "# My Title" in md
    assert "## Abstract" in md
    assert "## Intro" in md
    assert "## Results" in md
    assert "Smith et al. 2024" in md


def test_render_latex_escapes():
    tex = render_latex(_draft(DraftFormat.LATEX))
    assert "\\title{My Title}" in tex
    assert "\\$x\\$" in tex  # escaped dollar
    assert "\\&" in tex
    assert "\\section{Intro}" in tex
    assert "\\end{document}" in tex
