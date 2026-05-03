from fastapi.testclient import TestClient

from ai_scientist.api.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_projects_empty():
    client = TestClient(create_app())
    r = client.get("/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_unknown_project_404():
    client = TestClient(create_app())
    r = client.get("/projects/does-not-exist")
    assert r.status_code == 404
