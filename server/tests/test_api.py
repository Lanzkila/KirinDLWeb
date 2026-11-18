from __future__ import annotations

from fastapi.testclient import TestClient

from kirindl_server.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "kirindl-web-engine"
    assert response.json()["api_version"] == "v1"


def test_create_task_rejects_localhost_before_queueing():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "http://localhost/private", "engine": "auto"},
        )
    assert response.status_code == 400
    assert "Local and internal" in response.json()["detail"]


def test_create_task_rejects_embedded_credentials():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "https://user:secret@example.com/media", "engine": "yt-dlp"},
        )
    assert response.status_code == 400
    assert "credentials" in response.json()["detail"]


def test_create_task_rejects_unknown_engine():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "https://example.com/media", "engine": "unknown"},
        )
    assert response.status_code == 422


def test_create_task_rejects_unexpected_fields():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "https://example.com/media", "engine": "auto", "output_path": "/tmp/file"},
        )
    assert response.status_code == 422


def test_missing_task_returns_not_found():
    with TestClient(app) as client:
        response = client.get("/api/v1/tasks/not-a-real-task")
    assert response.status_code == 404


def test_cancel_missing_task_returns_not_found():
    with TestClient(app) as client:
        response = client.delete("/api/v1/tasks/not-a-real-task")
    assert response.status_code == 404


def test_download_missing_task_returns_conflict():
    with TestClient(app) as client:
        response = client.get("/api/v1/tasks/not-a-real-task/download")
    assert response.status_code == 409


def test_task_creation_requires_turnstile_when_enabled(monkeypatch):
    from kirindl_server import main

    monkeypatch.setattr(main, "TURNSTILE_REQUIRED", True)
    monkeypatch.setattr(main, "TURNSTILE_SECRET", "")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "https://example.com/media", "engine": "auto"},
        )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_task_creation_rejects_missing_token_when_turnstile_is_configured(monkeypatch):
    from kirindl_server import main

    monkeypatch.setattr(main, "TURNSTILE_REQUIRED", True)
    monkeypatch.setattr(main, "TURNSTILE_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"url": "https://example.com/media", "engine": "auto"},
        )
    assert response.status_code == 400
    assert "security check" in response.json()["detail"]


def test_challenge_token_has_a_strict_maximum_length():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={
                "url": "https://example.com/media",
                "engine": "auto",
                "challenge_token": "x" * 2049,
            },
        )
    assert response.status_code == 422
