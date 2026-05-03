"""Take an idea, design a Python experiment, run it in the sandbox, and report metrics."""

from __future__ import annotations

import asyncio

from ai_scientist.experiments import design_experiment, run_experiment
from ai_scientist.models import Idea


async def main() -> None:
    idea = Idea(
        topic="optimization",
        title="Adam vs. SGD on synthetic convex problems",
        hypothesis=(
            "Adam converges faster than SGD on a 100-dim quadratic with badly conditioned curvature."
        ),
        motivation="Sanity-check optimizer behaviour on a controlled toy problem.",
        proposed_method=(
            "Generate a random PSD matrix A with cond=1000, target b. Minimise 1/2 x^T A x - b^T x. "
            "Run plain SGD and Adam (numpy implementation) for 500 steps. Report final loss for each."
        ),
        expected_outcome="Adam reaches lower loss faster than SGD.",
    )
    exp = await design_experiment(idea)
    print(f"=== Designed experiment: {exp.title} ===\n{exp.description}\n")
    print("--- Code ---")
    print(exp.code)
    print("\n--- Running ---")
    exp = await run_experiment(exp)
    assert exp.result is not None
    print(f"status:  {exp.result.status.value}")
    print(f"time:    {exp.result.duration_s:.2f}s")
    print(f"metrics: {exp.result.metrics}")
    if exp.result.stderr:
        print("\nstderr:\n" + exp.result.stderr[:1500])


if __name__ == "__main__":
    asyncio.run(main())
