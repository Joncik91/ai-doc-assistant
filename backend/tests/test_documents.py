"""Tests for document upload and registry APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.auth.operators import bootstrap_operators
from app.api import documents as documents_api
from app.main import app
from app.storage.database import initialize_database, reset_local_state
from app.storage.documents import get_document, list_document_chunks


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


def test_upload_rejects_oversized_files(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.txt", b"01234567890", "text/plain")},
        headers=_auth_headers(),
    )

    assert response.status_code == 413
    assert "limit" in response.json()["detail"]


def test_upload_rejects_unsupported_file_types() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("unsupported.csv", b"col1,col2\n1,2\n", "text/csv")},
        headers=_auth_headers(),
    )

    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]

    documents_response = client.get("/api/v1/documents", headers=_auth_headers())
    failed_documents = [
        item
        for item in documents_response.json()["documents"]
        if item["original_filename"] == "unsupported.csv"
    ]
    assert failed_documents
    assert failed_documents[0]["status"] == "failed"


def test_delete_document_removes_registry_chunks_and_file(tmp_path: Path) -> None:
    path = tmp_path / "delete-me.txt"
    path.write_text("Delete me after indexing.", encoding="utf-8")

    with path.open("rb") as handle:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("delete-me.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    document_id = upload_response.json()["document"]["id"]
    stored_document = get_document(document_id)
    assert stored_document is not None
    assert stored_document.source_path is not None
    assert Path(stored_document.source_path).exists()
    assert list_document_chunks(document_id)

    delete_response = client.delete(
        f"/api/v1/documents/{document_id}",
        headers=_auth_headers(),
    )

    assert delete_response.status_code == 200
    assert get_document(document_id) is None
    assert list_document_chunks(document_id) == []
    assert not Path(stored_document.source_path).exists()


def test_delete_nonexistent_document_returns_404() -> None:
    response = client.delete(
        "/api/v1/documents/does-not-exist",
        headers=_auth_headers(),
    )

    assert response.status_code == 404


def test_delete_returns_503_when_vector_store_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "vector-failure.txt"
    path.write_text("Vector store failure should preserve the document.", encoding="utf-8")

    with path.open("rb") as handle:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("vector-failure.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    document_id = upload_response.json()["document"]["id"]

    def fail_delete(_: str) -> None:
        raise RuntimeError("vector store offline")

    monkeypatch.setattr(documents_api, "remove_document_vectors", fail_delete)

    delete_response = client.delete(
        f"/api/v1/documents/{document_id}",
        headers=_auth_headers(),
    )

    assert delete_response.status_code == 503
    assert "Vector store unavailable" in delete_response.json()["detail"]
    assert get_document(document_id) is not None
