"""Tests for document upload and registry APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.auth.operators import bootstrap_operators
from app.main import app
from app.storage.database import initialize_database, reset_local_state


client = TestClient(app)


def setup_module() -> None:
    reset_local_state()
    bootstrap_operators()
    initialize_database()


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": "dev-api-key-change-in-production"}


def test_upload_and_list_document(tmp_path: Path) -> None:
    path = tmp_path / "policy.txt"
    path.write_text("Remote work is allowed with manager approval.", encoding="utf-8")

    with path.open("rb") as handle:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("policy.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["document"]["status"] == "ready"
    assert body["document"]["index_status"] == "indexed"
    assert body["chunks_created"] >= 1

    list_response = client.get("/api/v1/documents", headers=_auth_headers())
    assert list_response.status_code == 200
    documents = list_response.json()["documents"]
    assert len(documents) >= 1
    assert documents[0]["index_status"] == "indexed"


def test_document_lookup_and_duplicate_detection(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.txt"
    path.write_text("Duplicate detection content.", encoding="utf-8")

    with path.open("rb") as handle:
        first = client.post(
            "/api/v1/documents/upload",
            files={"file": ("duplicate.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    assert first.status_code == 200
    document_id = first.json()["document"]["id"]

    with path.open("rb") as handle:
        duplicate = client.post(
            "/api/v1/documents/upload",
            files={"file": ("duplicate.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True

    detail = client.get(f"/api/v1/documents/{document_id}", headers=_auth_headers())
    assert detail.status_code == 200
    assert detail.json()["id"] == document_id
