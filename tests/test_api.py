"""API contracts and security checks without external AI calls."""

import pytest
from fastapi.testclient import TestClient

from codeatlas.api.app import create_app
from codeatlas.api.service import RepositoryService
from codeatlas.config import settings


@pytest.fixture
def service(tmp_path):
    instance = RepositoryService(tmp_path / "catalog.json")
    source = tmp_path / "example.py"
    source.write_text("import os\n\ndef greet():\n    return 'hello'\n")
    instance.records["test"] = {
        "id": "test",
        "name": "fixture",
        "source": "https://github.com/example/fixture",
        "path": str(tmp_path),
        "statistics": {},
    }
    yield instance
    instance.executor.shutdown(wait=True)


@pytest.fixture
def client(service, monkeypatch):
    monkeypatch.setattr(settings, "api_token", "")
    monkeypatch.setattr(settings, "api_requests_per_minute", 100)
    return TestClient(create_app(service))


def test_health_and_private_catalog(client):
    assert client.get("/health").json()["status"] == "ok"
    assert "path" not in client.get("/api/repositories").json()[0]
    assert client.get("/api/repositories/test/tree").json()["files"] == ["example.py"]


@pytest.mark.parametrize("path", ["../.env", ".env", "C:/Windows/win.ini", "/etc/passwd"])
def test_source_rejects_unknown_paths(client, path):
    assert client.get("/api/repositories/test/source", params={"path": path}).status_code == 400


def test_source_lines_and_imports(client):
    result = client.get("/api/repositories/test/source", params={"path": "example.py"}).json()
    assert result["start_line"] == 1
    assert result["imports"] == ["os"]
    assert "def greet" in result["content"]


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://evil.com/a/b",
        "https://github.com/a/..",
        "https://github.com/a/b?x=y",
        "https://user:secret@github.com/a/b",
    ],
)
def test_import_validation(client, url):
    assert client.post("/api/repositories", json={"url": url}).status_code == 422


def test_auth_and_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "api_token", "test-token")
    assert client.get("/api/repositories").status_code == 401
    monkeypatch.setattr(settings, "api_requests_per_minute", 1)
    headers = {"Authorization": "Bearer test-token"}
    assert client.get("/api/repositories", headers=headers).status_code == 200
    assert client.get("/api/repositories", headers=headers).status_code == 429


def test_question_validation_and_busy(client, service):
    assert (
        client.post("/api/repositories/test/questions", json={"question": " "}).status_code == 422
    )
    with service.compute:
        assert (
            client.post(
                "/api/repositories/test/questions", json={"question": "Explain"}
            ).status_code
            == 409
        )


def test_job_success_and_failure(service, monkeypatch):
    from codeatlas.api import service as module

    repository = service.repository("test")
    monkeypatch.setattr(service, "preflight", lambda url: None)
    monkeypatch.setattr(module, "clone_repository", lambda url: repository)
    monkeypatch.setattr(module, "index_repository", lambda *a, **k: (None, {"chunks": 3}))
    service.jobs["one"] = {}
    service.run("one", repository.source)
    assert service.jobs["one"]["status"] == "completed"
    assert service.catalog.exists()

    def fail(*args, **kwargs):
        raise RuntimeError("secret-value")

    monkeypatch.setattr(module, "index_repository", fail)
    service.jobs["two"] = {}
    service.run("two", repository.source)
    assert service.jobs["two"]["status"] == "failed"
    assert "secret-value" not in service.jobs["two"]["error"]


def test_missing_resources(client):
    assert client.get("/api/jobs/missing").status_code == 404
    assert client.get("/api/repositories/missing/tree").status_code == 404


def test_oversized_body_rejected(client):
    result = client.post(
        "/api/repositories",
        content=b"x" * 32769,
        headers={"Content-Type": "application/json"},
    )
    assert result.status_code == 413


def test_production_requires_strong_token(service, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_token", "")
    with pytest.raises(RuntimeError, match="Production requires"):
        with TestClient(create_app(service)):
            pass


def test_repository_preflight_enforces_size(service, monkeypatch):
    from codeatlas.api import service as module

    class Metadata:
        def raise_for_status(self):
            pass

        def json(self):
            return {"size": settings.max_repository_size_kb + 1, "private": False}

    monkeypatch.setattr(module.httpx, "get", lambda *a, **k: Metadata())
    with pytest.raises(ValueError, match="size limit"):
        service.preflight("https://github.com/example/fixture")
