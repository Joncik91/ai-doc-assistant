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
            files={"files": ("policy.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["processed_count"] == 1
    assert body["created_count"] == 1
    assert body["results"][0]["created"] is True
    assert body["results"][0]["document"]["status"] == "completed"
    assert body["results"][0]["document"]["index_status"] == "indexed"
    assert body["results"][0]["chunks_created"] >= 1

    list_response = client.get("/api/v1/documents", headers=_auth_headers())
    assert list_response.status_code == 200
    documents = list_response.json()["documents"]
    assert len(documents) >= 1
    assert documents[0]["index_status"] == "indexed"


def test_document_lookup_and_duplicate_detection(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.txt"
    path.write_text("Duplicate detection content.", encoding="utf-8")

    with path.open("rb") as first_handle, path.open("rb") as duplicate_handle:
        response = client.post(
            "/api/v1/documents/upload",
            files=[
                ("files", ("duplicate-a.txt", first_handle, "text/plain")),
                ("files", ("duplicate-b.txt", duplicate_handle, "text/plain")),
            ],
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["processed_count"] == 2
    assert body["created_count"] == 1
    assert body["duplicate_count"] == 1
    document_id = body["results"][0]["document"]["id"]

    detail = client.get(f"/api/v1/documents/{document_id}", headers=_auth_headers())
    assert detail.status_code == 200
    assert detail.json()["id"] == document_id


def test_upload_rejects_oversized_files(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    response = client.post(
        "/api/v1/documents/upload",
        files={"files": ("large.txt", b"01234567890", "text/plain")},
        headers=_auth_headers(),
    )

    assert response.status_code == 413
    assert "limit" in response.json()["detail"]


def test_upload_rejects_unsupported_file_types() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"files": ("unsupported.csv", b"col1,col2\n1,2\n", "text/csv")},
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


def test_multi_file_upload_reports_partial_failures(tmp_path: Path) -> None:
    valid_path = tmp_path / "policy.txt"
    valid_path.write_text("Unique mixed batch content for partial failure coverage.", encoding="utf-8")

    with valid_path.open("rb") as valid_handle:
        response = client.post(
            "/api/v1/documents/upload",
            files=[
                ("files", ("policy.txt", valid_handle, "text/plain")),
                ("files", ("unsupported.csv", b"unique_col1,unique_col2\n3,4\n", "text/csv")),
            ],
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["processed_count"] == 2
    assert body["created_count"] == 1
    assert body["failed_count"] == 1
    assert any(result["created"] for result in body["results"])
    assert any(result["error"] for result in body["results"])


def test_upload_marks_pii_findings_as_warnings(tmp_path: Path) -> None:
    path = tmp_path / "pii.txt"
    path.write_text("Contact jane.doe@example.com for the latest policy.", encoding="utf-8")

    with path.open("rb") as handle:
        response = client.post(
            "/api/v1/documents/upload",
            files={"files": ("pii.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["warning_count"] == 1
    assert body["results"][0]["warning"] is True
    assert body["results"][0]["document"]["status"] == "warning"
    assert any(
        "email" in warning.lower()
        for warning in body["results"][0]["document"]["warnings"]
    )


def test_delete_document_removes_registry_chunks_and_file(tmp_path: Path) -> None:
    path = tmp_path / "delete-me.txt"
    path.write_text("Delete me after indexing.", encoding="utf-8")

    with path.open("rb") as handle:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"files": ("delete-me.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    document_id = upload_response.json()["results"][0]["document"]["id"]
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
            files={"files": ("vector-failure.txt", handle, "text/plain")},
            headers=_auth_headers(),
        )

    document_id = upload_response.json()["results"][0]["document"]["id"]

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
