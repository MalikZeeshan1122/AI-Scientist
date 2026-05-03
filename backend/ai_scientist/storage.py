"""Lightweight SQLite-backed persistence for projects, papers, ideas, experiments, drafts."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def _now() -> datetime:
    return datetime.now(timezone.utc)
from typing import Any, Iterator
from uuid import uuid4

from pydantic import BaseModel

from .config import get_settings
from .models import Draft, Experiment, Idea, Paper

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    idea_id TEXT,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    idea_id TEXT,
    experiment_id TEXT,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Project(BaseModel):
    id: str
    topic: str
    created_at: datetime


class Storage:
    def __init__(self, db_path: Path | str | None = None):
        settings = get_settings()
        if db_path is None:
            url = settings.db_url
            db_path = url.split("sqlite:///")[-1] if url.startswith("sqlite:") else "ai_scientist.db"
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_project(self, topic: str) -> Project:
        proj = Project(
            id=f"proj_{uuid4().hex[:10]}", topic=topic, created_at=_now()
        )
        with self._conn() as c:
            c.execute(
                "INSERT INTO projects(id, topic, created_at) VALUES (?, ?, ?)",
                (proj.id, proj.topic, proj.created_at.isoformat()),
            )
        return proj

    def list_projects(self) -> list[Project]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [
            Project(
                id=r["id"], topic=r["topic"], created_at=datetime.fromisoformat(r["created_at"])
            )
            for r in rows
        ]

    def get_project(self, project_id: str) -> Project | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            return None
        return Project(
            id=row["id"], topic=row["topic"], created_at=datetime.fromisoformat(row["created_at"])
        )

    def save_paper(self, paper: Paper, project_id: str | None = None) -> None:
        self._upsert("papers", paper.id, paper, project_id=project_id)

    def save_idea(self, idea: Idea, project_id: str | None = None) -> None:
        self._upsert("ideas", idea.id, idea, project_id=project_id)

    def save_experiment(self, exp: Experiment, project_id: str | None = None) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO experiments(id, project_id, idea_id, data, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    exp.id,
                    project_id,
                    exp.idea_id,
                    exp.model_dump_json(),
                    exp.created_at.isoformat(),
                ),
            )

    def save_draft(self, draft: Draft, project_id: str | None = None) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO drafts(id, project_id, idea_id, experiment_id, data, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    draft.id,
                    project_id,
                    draft.idea_id,
                    draft.experiment_id,
                    draft.model_dump_json(),
                    draft.created_at.isoformat(),
                ),
            )

    def _upsert(self, table: str, id_: str, obj: BaseModel, project_id: str | None) -> None:
        ts = getattr(obj, "created_at", None)
        ts_str = ts.isoformat() if ts else _now().isoformat()
        with self._conn() as c:
            c.execute(
                f"INSERT OR REPLACE INTO {table}(id, project_id, data, created_at) "
                "VALUES (?, ?, ?, ?)",
                (id_, project_id, obj.model_dump_json(), ts_str),
            )

    def list_papers(self, project_id: str | None = None) -> list[Paper]:
        return self._list("papers", Paper, project_id)

    def list_ideas(self, project_id: str | None = None) -> list[Idea]:
        return self._list("ideas", Idea, project_id)

    def list_experiments(self, project_id: str | None = None) -> list[Experiment]:
        return self._list("experiments", Experiment, project_id)

    def list_drafts(self, project_id: str | None = None) -> list[Draft]:
        return self._list("drafts", Draft, project_id)

    def _list(self, table: str, model: type[BaseModel], project_id: str | None) -> list[Any]:
        with self._conn() as c:
            if project_id:
                rows = c.execute(
                    f"SELECT data FROM {table} WHERE project_id=? ORDER BY created_at DESC",
                    (project_id,),
                ).fetchall()
            else:
                rows = c.execute(
                    f"SELECT data FROM {table} ORDER BY created_at DESC"
                ).fetchall()
        return [model.model_validate(json.loads(r["data"])) for r in rows]
