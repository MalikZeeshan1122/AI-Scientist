from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ExperimentResult(BaseModel):
    status: ExperimentStatus
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    duration_s: float = 0.0
    artifacts: list[str] = Field(default_factory=list, description="Files written by the run")
    metrics: dict[str, float] = Field(default_factory=dict)


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: f"exp_{uuid4().hex[:10]}")
    idea_id: str | None = None
    title: str
    description: str
    code: str = Field(description="Python source for the experiment")
    requirements: list[str] = Field(default_factory=list)
    result: ExperimentResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
