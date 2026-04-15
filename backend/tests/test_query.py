"""Tests for the grounded query API."""

from __future__ import annotations

import asyncio
import json

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
            "files": (
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

    audit_response = client.get("/api/v1/audit/events", headers=_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()["events"]
    assert events[0]["action"] == "query.executed"
    assert events[0]["outcome"] == "success"
    assert "manager approval" in events[0]["details"]["answer"]
    assert events[0]["details"]["citations"][0]["source"] == "remote-policy.txt"


def test_query_streams_incremental_answer(monkeypatch) -> None:
    from app.api import query as query_module

    class FakeStreamingProvider:
        async def generate(self, request):
            raise AssertionError("stream endpoint should not call generate()")

        async def health_check(self) -> bool:
            return True

        async def generate_stream(self, request):
            yield type("Chunk", (), {"content": "Remote work is ", "finish_reason": None})()
            await asyncio.sleep(0)
            yield type(
                "Chunk",
                (),
                {
                    "content": "allowed with manager approval and a weekly check-in to confirm progress.",
                    "finish_reason": "stop",
                },
            )()

    monkeypatch.setattr(query_module, "get_provider", lambda: FakeStreamingProvider())

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "files": (
                "stream-policy.txt",
                b"Remote work is allowed with manager approval and a weekly check-in to confirm progress.",
                "text/plain",
            )
        },
        headers=_auth_headers(),
    )

    assert upload_response.status_code == 200

    with client.stream(
        "POST",
        "/api/v1/query/stream",
        json={"question": "What is the remote work policy?", "top_k": 3},
        headers=_auth_headers(),
    ) as response:
        assert response.status_code == 200
        chunks: list[str] = []
        final_response = None
        for line in response.iter_lines():
            if not line:
                continue
            payload = json.loads(line.decode() if isinstance(line, bytes) else line)
            if payload["type"] == "delta":
                chunks.append(payload["delta"])
            elif payload["type"] == "final":
                final_response = payload["response"]

    assert len(chunks) > 1
    assert final_response is not None
    assert "".join(chunks) == final_response["answer"]

    audit_response = client.get("/api/v1/audit/events", headers=_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()["events"]
    assert events[0]["action"] == "query.executed"
    assert events[0]["outcome"] == "success"


def test_retrieval_health_reports_readiness() -> None:
    response = client.get("/api/v1/health/retrieval")

    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is True
    assert body["status"] == "ready"
