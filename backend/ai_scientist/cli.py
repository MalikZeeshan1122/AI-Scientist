"""Typer-based CLI exposing every stage of the pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path

from contextlib import contextmanager

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .ideation import generate_ideas
from .ingestion import extract_pdf_text, summarize_paper
from .models import DraftFormat, Idea
from .pipeline import AIScientistPipeline
from .sources import UnifiedSource

app = typer.Typer(help="AI Scientist: an autonomous research assistant.", no_args_is_help=True)
console = Console()


def _arun(coro):
    return asyncio.run(coro)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(8, "--limit", "-n"),
):
    """Search across arXiv, Semantic Scholar, OpenAlex and local PDFs."""

    async def _run():
        src = UnifiedSource()
        with _spinner(f"Searching '{query}'..."):
            return await src.search(query, limit=limit)

    papers = _arun(_run())
    table = Table(title=f"Top {len(papers)} papers")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Year", justify="right")
    table.add_column("Cites", justify="right")
    for p in papers:
        table.add_row(
            p.id,
            p.title[:90],
            str(p.published.year) if p.published else "-",
            str(p.citation_count or "-"),
        )
    console.print(table)


@app.command()
def summarize(
    pdf: Path = typer.Argument(..., exists=True, readable=True),
):
    """Summarise a local PDF using the configured LLM."""
    from .models import Paper
    from datetime import date

    text = extract_pdf_text(pdf)
    paper = Paper(
        id=f"local:{pdf.stem}",
        source="local",
        title=pdf.stem,
        abstract=text[:2000],
        published=date.today(),
    )
    summary = _arun(summarize_paper(paper, text))
    console.print(Panel(summary.summary, title="Summary"))
    console.print("[bold]Findings:[/]")
    for f in summary.findings:
        console.print(f"  • {f}")


@app.command()
def ideate(
    topic: str = typer.Argument(...),
    n: int = typer.Option(5, "--n"),
):
    """Generate research ideas grounded in the indexed corpus."""

    async def _run():
        return await generate_ideas(topic, n=n)

    ideas = _arun(_run())
    for i, idea in enumerate(ideas, 1):
        console.print(Panel(_idea_panel(idea), title=f"Idea {i}: {idea.title}"))


@app.command()
def experiment(
    idea_json: Path = typer.Argument(..., exists=True, help="Path to a JSON-serialised Idea"),
):
    """Design + run an experiment for an idea (loaded from JSON)."""
    idea = Idea.model_validate_json(Path(idea_json).read_text(encoding="utf-8"))
    pipe = AIScientistPipeline()
    with _spinner("Designing and running experiment..."):
        exp = _arun(pipe.experiment(idea))
    console.print(Panel(exp.code, title=f"Code: {exp.title}"))
    if exp.result:
        console.print(f"[bold]Status:[/] {exp.result.status.value}")
        console.print(f"[bold]Duration:[/] {exp.result.duration_s:.1f}s")
        if exp.result.metrics:
            console.print("[bold]Metrics:[/]")
            for k, v in exp.result.metrics.items():
                console.print(f"  {k} = {v}")
        if exp.result.stderr:
            console.print(Panel(exp.result.stderr[:2000], title="stderr", style="red"))


@app.command()
def run(
    topic: str = typer.Argument(...),
    n_papers: int = typer.Option(6, "--papers"),
    n_ideas: int = typer.Option(5, "--ideas"),
    refine: int = typer.Option(2, "--refine", help="Refine iterations (0 to skip)"),
    fmt: str = typer.Option("markdown", "--format", help="markdown or latex"),
):
    """End-to-end: search -> ideate -> experiment -> draft -> refine."""
    pipe = AIScientistPipeline()
    fmt_enum = DraftFormat(fmt.lower())
    with _spinner(f"Running full pipeline on '{topic}'..."):
        result = _arun(
            pipe.run(
                topic,
                n_papers=n_papers,
                n_ideas=n_ideas,
                refine_iters=refine,
                fmt=fmt_enum,
            )
        )
    console.rule(f"[bold green]Project {result.project.id}")
    console.print(f"[bold]Topic:[/] {result.project.topic}")
    console.print(f"[bold]Papers indexed:[/] {len(result.papers)}")
    console.print(f"[bold]Ideas:[/] {len(result.ideas)}")
    console.print(Panel(_idea_panel(result.chosen_idea), title=f"Chosen idea: {result.chosen_idea.title}"))
    if result.experiment.result:
        console.print(f"[bold]Experiment:[/] {result.experiment.result.status.value} "
                      f"({result.experiment.result.duration_s:.1f}s)")
        if result.experiment.result.metrics:
            console.print(f"  metrics: {result.experiment.result.metrics}")
    console.print(f"[bold green]Draft saved to:[/] {result.draft.rendered_path}")
    if result.improvement:
        scores = " → ".join(f"{s.overall:.2f}" for s in result.improvement.history)
        console.print(f"[bold]Self-improvement scores:[/] {scores}")


@app.command()
def projects():
    """List previously-run projects."""
    from .storage import Storage

    rows = Storage().list_projects()
    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Topic")
    table.add_column("Created")
    for p in rows:
        table.add_row(p.id, p.topic, p.created_at.isoformat(timespec="minutes"))
    console.print(table)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the FastAPI backend."""
    import uvicorn

    uvicorn.run("ai_scientist.api.main:app", host=host, port=port, reload=reload)


def _idea_panel(idea: Idea) -> str:
    score = (
        f"score: novelty={idea.score.novelty}, feasibility={idea.score.feasibility}, "
        f"impact={idea.score.impact} (overall {idea.score.overall})"
        if idea.score
        else "(unscored)"
    )
    return (
        f"[bold]Hypothesis:[/] {idea.hypothesis}\n\n"
        f"[bold]Method:[/] {idea.proposed_method}\n\n"
        f"[bold]Expected:[/] {idea.expected_outcome}\n\n"
        f"[dim]{score}[/]"
    )


@contextmanager
def _spinner(msg: str):
    progress = Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
    )
    progress.start()
    progress.add_task(msg, total=None)
    try:
        yield
    finally:
        progress.stop()


if __name__ == "__main__":
    app()
