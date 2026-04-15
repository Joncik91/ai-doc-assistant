"""Tests for observability and runtime statistics."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.operators import bootstrap_operators
from app.main import app
from app.storage.database import initialize_database, reset_local_state


client = TestClient(app)


def setup_module() -> None:
    reset_local_state()
    bootstrap_operators()
    initialize_database()


def test_health_endpoint_includes_request_identifiers() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Process-Time"]


def test_runtime_stats_and_metrics_are_exposed() -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    stats_response = client.get(
        "/api/v1/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["documents_total"] == 0
    assert stats["audit_events_total"] == 1
    assert stats["blocked_queries_total"] == 0
    assert stats["failed_logins_total"] == 0
    assert stats["distinct_actors"] == 1
    assert stats["last_activity_at"] is not None

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "ai_doc_assistant_http_requests_total" in metrics_response.text
    assert "ai_doc_assistant_runtime_documents_total" in metrics_response.text
    assert "ai_doc_assistant_auth_logins_total" in metrics_response.text
