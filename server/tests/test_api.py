from __future__ import annotations

from fastapi.testclient import TestClient

from kirindl_server.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "kirindl-web-engine"
