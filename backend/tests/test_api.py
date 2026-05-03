from fastapi.testclient import TestClient

from ai_scientist.api.main import create_app


def test_runtime_error_openai_429_returns_503():
    app = create_app()

    @app.get("/__raise_openai_429")
    async def raise_openai_429():
        raise RuntimeError(
            'OpenAI API 429: {"error":{"message":"Rate limit","code":"rate_limit_exceeded"}}'
        )

    client = TestClient(app)
    r = client.get("/__raise_openai_429")
    assert r.status_code == 503
    assert r.headers.get("retry-after") == "60"


def test_health_endpoint():
    client = TestClient(create_app())
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["version"] == "0.1.1"


def test_post_run_openai_rate_limit_returns_503(monkeypatch):
    """Regression: LLM routes must not surface vendor RPM limits as HTTP 500."""

    from ai_scientist.pipeline import AIScientistPipeline

    async def failing_run(self, *args, **kwargs):
        raise RuntimeError(
            'OpenAI API 429: {"error":{"message":"Rate limit","code":"rate_limit_exceeded"}}'
        )

    monkeypatch.setattr(AIScientistPipeline, "run", failing_run)

    client = TestClient(create_app())
    r = client.post(
        "/run",
        json={
            "topic": "test",
            "n_papers": 1,
            "n_ideas": 1,
            "refine_iters": 0,
            "fmt": "markdown",
        },
    )
    assert r.status_code == 503
    assert r.headers.get("retry-after") == "60"


def test_list_projects_empty():
    client = TestClient(create_app())
    r = client.get("/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_unknown_project_404():
    client = TestClient(create_app())
    r = client.get("/projects/does-not-exist")
    assert r.status_code == 404
