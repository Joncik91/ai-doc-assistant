"""Tests for the grounded query API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.operators import bootstrap_operators
from app.llm.provider import GenerationResponse
from app.main import app
from app.storage.database import initialize_database, reset_local_state


client = TestClient(app)


def setup_module() -> None:
    reset_local_state()
    bootstrap_operators()
    initialize_database()


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": "dev-api-key-change-in-production"}


def test_query_returns_grounded_answer(monkeypatch) -> None:
    from app.retrieval import generator as generator_module

    class FakeProvider:
        async def generate(self, request):
            return GenerationResponse(
                content="Remote work is allowed with manager approval.",
                finish_reason="stop",
                model="mock",
                usage={},
            )

        async def health_check(self) -> bool:
            return True

    monkeypatch.setattr(generator_module, "get_provider", lambda: FakeProvider())

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "remote-policy.txt",
                b"Remote work is allowed with manager approval.",
                "text/plain",
            )
        },
        headers=_auth_headers(),
    )

    assert upload_response.status_code == 200

    response = client.post(
        "/api/v1/query",
        json={"question": "What is the remote work policy?", "top_k": 3},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert "manager approval" in body["answer"]
    assert body["citations"]
    assert body["citations"][0]["source"] == "remote-policy.txt"


def test_retrieval_health_reports_readiness() -> None:
    response = client.get("/api/v1/health/retrieval")

    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is True
    assert body["status"] == "ready"
