from fastapi.testclient import TestClient

from employee_agent_service.app import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint_exposes_identifiers_without_prompt_text() -> None:
    with TestClient(app) as client:
        response = client.get("/api/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]["version"] == "0.1.0"
    assert payload["components"]["prompt"] == "prompt-1.0.0"
    assert "你负责识别用户意图" not in response.text
