from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from ..llm import LLMProvider, get_llm
from ..models import Experiment, ExperimentResult, ExperimentStatus, Idea
from .sandbox import SandboxResult, run_python_in_sandbox

_DESIGN_SYSTEM = (
    "You are a meticulous research engineer. Translate research ideas into a single "
    "self-contained Python experiment script that can run on a typical laptop in under "
    "two minutes. The script MUST: (1) print structured results as JSON to stdout in a "
    "block delimited by `===METRICS_START===` and `===METRICS_END===`; (2) use only the "
    "Python stdlib unless absolutely necessary; (3) avoid network access; (4) be "
    "deterministic where possible (set seeds)."
)

_METRICS_RE = re.compile(
    r"===METRICS_START===\s*(\{.*?\})\s*===METRICS_END===", re.DOTALL
)


class _Design(BaseModel):
    title: str
    description: str = Field(description="What is being measured and why")
    code: str = Field(description="Self-contained Python script. Single file.")
    requirements: list[str] = Field(default_factory=list)


class ExperimentRunner:
    def __init__(self, *, llm: LLMProvider | None = None):
        self.llm = llm or get_llm()

    async def design(self, idea: Idea) -> Experiment:
        prompt = (
            "Design a runnable experiment for the following idea. Output ONLY JSON "
            "matching the schema (no fences). Keep `code` to a single file < 250 lines. "
            "Always wrap final results between `===METRICS_START===` and "
            "`===METRICS_END===` as a JSON object.\n\n"
            f"Title: {idea.title}\n"
            f"Hypothesis: {idea.hypothesis}\n"
            f"Method: {idea.proposed_method}\n"
            f"Expected outcome: {idea.expected_outcome}\n"
        )
        design = await self.llm.complete_json(prompt, _Design, system=_DESIGN_SYSTEM)
        return Experiment(
            idea_id=idea.id,
            title=design.title,
            description=design.description,
            code=design.code,
            requirements=design.requirements,
        )

    async def run(self, experiment: Experiment, *, workdir: Path | None = None) -> Experiment:
        sb: SandboxResult = await run_python_in_sandbox(
            experiment.code,
            requirements=experiment.requirements,
            workdir=workdir,
        )
        status = (
            ExperimentStatus.TIMED_OUT
            if sb.timed_out
            else ExperimentStatus.SUCCEEDED
            if sb.returncode == 0
            else ExperimentStatus.FAILED
        )
        metrics = _parse_metrics(sb.stdout)
        experiment.result = ExperimentResult(
            status=status,
            stdout=sb.stdout,
            stderr=sb.stderr,
            returncode=sb.returncode,
            duration_s=sb.duration_s,
            artifacts=[str(p) for p in sb.artifacts],
            metrics=metrics,
        )
        return experiment


async def design_experiment(idea: Idea, *, llm: LLMProvider | None = None) -> Experiment:
    return await ExperimentRunner(llm=llm).design(idea)


async def run_experiment(
    experiment: Experiment, *, workdir: Path | None = None, llm: LLMProvider | None = None
) -> Experiment:
    return await ExperimentRunner(llm=llm).run(experiment, workdir=workdir)


def _parse_metrics(stdout: str) -> dict[str, float]:
    m = _METRICS_RE.search(stdout)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    out: dict[str, float] = {}
    for k, v in (data.items() if isinstance(data, dict) else []):
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out
