from __future__ import annotations

from typing import Any

import logging
import os
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("ai_scientist.api")

from ..config import get_settings
from ..ideation import generate_ideas
from ..models import DraftFormat
from ..pipeline import AIScientistPipeline
from ..settings_store import (
    EDITABLE_KEYS,
    is_editable_key,
    mask_secret,
    read_env_file,
    write_env_updates,
)
from ..sources import UnifiedSource
from ..storage import Storage
from .http_errors import runtime_error_status_and_headers
from .schemas import (
    DraftRequest,
    ExperimentRequest,
    IdeateRequest,
    RunPipelineRequest,
    SearchRequest,
    SettingsUpdateRequest,
)


def _runtime_error_http_response(exc: RuntimeError) -> JSONResponse:
    """Translate provider ``RuntimeError`` messages into JSON + correct HTTP status."""
    msg = str(exc)
    status_code, headers = runtime_error_status_and_headers(msg)
    return JSONResponse(
        status_code=status_code,
        content={"detail": msg, "type": "RuntimeError"},
        headers=headers,
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Scientist API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        # Missing keys / vendor rate limits → 503 so clients treat it as retryable,
        # unlike unexpected bugs (500).
        logger.warning("RuntimeError on %s %s: %s", request.method, request.url.path, exc)
        return _runtime_error_http_response(exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled %s on %s %s: %s\n%s",
            type(exc).__name__,
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )

    storage = Storage()

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "version": "0.1.1"}

    @app.get("/settings")
    async def get_settings_view() -> dict[str, Any]:
        """Return current settings: which API keys are configured (masked) and
        which provider/model is active. Never returns full secret values."""
        env = read_env_file()
        # Pull from process env first (covers values set without restart).
        def _val(key: str) -> str | None:
            return os.environ.get(key) or env.get(key) or None

        s = get_settings()
        # Anything in the .env that ends in _API_KEY but isn't one of the
        # well-known providers is surfaced as a "custom" entry so the UI can
        # show + edit it.
        well_known = {
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "GROQ_API_KEY",
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "TAVILY_API_KEY",
            "SEMANTIC_SCHOLAR_API_KEY",
        }
        custom: list[dict[str, Any]] = []
        for key, value in env.items():
            if key in well_known or not key.endswith("_API_KEY"):
                continue
            if not is_editable_key(key):
                continue
            custom.append(
                {
                    "name": key,
                    "configured": bool(value),
                    "key_preview": mask_secret(value),
                }
            )
        custom.sort(key=lambda c: c["name"])

        return {
            "providers": {
                "anthropic": {
                    "configured": bool(s.anthropic_api_key),
                    "key_preview": mask_secret(_val("ANTHROPIC_API_KEY")),
                    "model": s.anthropic_model,
                },
                "google": {
                    "configured": bool(s.google_api_key),
                    "key_preview": mask_secret(_val("GOOGLE_API_KEY")),
                    "model": s.google_model,
                },
                "groq": {
                    "configured": bool(s.groq_api_key),
                    "key_preview": mask_secret(_val("GROQ_API_KEY")),
                    "model": s.groq_model,
                },
                "openai": {
                    "configured": bool(s.openai_api_key),
                    "key_preview": mask_secret(_val("OPENAI_API_KEY")),
                    "model": s.openai_model,
                    "min_interval_s": s.openai_min_interval_s,
                    "rate_limit_extra_sleep_s": s.openai_rate_limit_extra_sleep_s,
                },
                "openrouter": {
                    "configured": bool(s.openrouter_api_key),
                    "key_preview": mask_secret(_val("OPENROUTER_API_KEY")),
                    "model": s.openrouter_model,
                },
            },
            "search": {
                "tavily": {
                    "configured": bool(s.tavily_api_key),
                    "key_preview": mask_secret(_val("TAVILY_API_KEY")),
                },
                "semantic_scholar": {
                    "configured": bool(s.semantic_scholar_api_key),
                    "key_preview": mask_secret(_val("SEMANTIC_SCHOLAR_API_KEY")),
                },
            },
            "custom_keys": custom,
            "default_provider": s.default_provider,
            "editable_keys": list(EDITABLE_KEYS),
            "custom_key_pattern": "^[A-Z][A-Z0-9_]{1,64}_API_KEY$",
        }

    @app.post("/settings")
    async def update_settings(req: SettingsUpdateRequest) -> dict[str, Any]:
        if not req.updates:
            raise HTTPException(status_code=400, detail="No updates supplied.")
        try:
            write_env_updates(req.updates)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        # Re-read the masked view so the UI immediately reflects the new state.
        return await get_settings_view()

    @app.get("/projects")
    async def list_projects():
        return [p.model_dump() for p in storage.list_projects()]

    @app.get("/projects/{project_id}")
    async def get_project(project_id: str):
        proj = storage.get_project(project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="project not found")
        return {
            "project": proj.model_dump(),
            "papers": [p.model_dump() for p in storage.list_papers(project_id)],
            "ideas": [i.model_dump() for i in storage.list_ideas(project_id)],
            "experiments": [e.model_dump() for e in storage.list_experiments(project_id)],
            "drafts": [d.model_dump() for d in storage.list_drafts(project_id)],
        }

    @app.get("/papers")
    async def list_papers():
        return [p.model_dump() for p in storage.list_papers()]

    @app.get("/ideas")
    async def list_ideas():
        return [i.model_dump() for i in storage.list_ideas()]

    @app.get("/experiments")
    async def list_experiments():
        return [e.model_dump() for e in storage.list_experiments()]

    @app.get("/drafts")
    async def list_drafts():
        return [d.model_dump() for d in storage.list_drafts()]

    @app.post("/search")
    async def search(req: SearchRequest):
        src = UnifiedSource()
        papers = await src.search(
            req.query, limit=req.limit, categories=req.categories
        )
        return [p.model_dump() for p in papers]

    @app.post("/ideate")
    async def ideate(req: IdeateRequest):
        try:
            ideas = await generate_ideas(req.topic, n=req.n)
        except RuntimeError as exc:
            return _runtime_error_http_response(exc)
        for idea in ideas:
            storage.save_idea(idea, project_id=req.project_id)
        return [i.model_dump() for i in ideas]

    @app.post("/experiment")
    async def experiment(req: ExperimentRequest):
        pipe = AIScientistPipeline()
        try:
            exp = await pipe.experiment(req.idea)
        except RuntimeError as exc:
            return _runtime_error_http_response(exc)
        return exp.model_dump()

    @app.post("/draft")
    async def draft(req: DraftRequest):
        pipe = AIScientistPipeline()
        exp = None
        if req.experiment_id:
            for e in storage.list_experiments():
                if e.id == req.experiment_id:
                    exp = e
                    break
        try:
            d = await pipe.write(req.idea, exp, related=None, fmt=DraftFormat(req.fmt))
        except RuntimeError as exc:
            return _runtime_error_http_response(exc)
        return d.model_dump()

    @app.post("/run")
    async def run(req: RunPipelineRequest):
        pipe = AIScientistPipeline()
        try:
            result = await pipe.run(
                req.topic,
                n_papers=req.n_papers,
                n_ideas=req.n_ideas,
                refine_iters=req.refine_iters,
                fmt=DraftFormat(req.fmt),
                categories=req.categories,
            )
        except RuntimeError as exc:
            return _runtime_error_http_response(exc)
        return {
            "project": result.project.model_dump(),
            "papers": [p.model_dump() for p in result.papers],
            "ideas": [i.model_dump() for i in result.ideas],
            "chosen_idea": result.chosen_idea.model_dump(),
            "experiment": result.experiment.model_dump(),
            "draft": result.draft.model_dump(),
            "improvement": result.improvement.model_dump() if result.improvement else None,
        }

    return app


app = create_app()
