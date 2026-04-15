"""Repository helpers for document registry records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.document import DocumentRecord, DocumentStatus
from app.storage.database import connect, dumps, loads, new_id

LEGACY_STATUS_MAP = {
    "uploaded": DocumentStatus.queued.value,
    "ready": DocumentStatus.completed.value,
    "duplicate": DocumentStatus.warning.value,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_document(row: Any) -> DocumentRecord:
    status_value = LEGACY_STATUS_MAP.get(row["status"], row["status"])
    return DocumentRecord(
        id=row["id"],
        filename=row["filename"],
        original_filename=row["original_filename"],
        content_type=row["content_type"],
        size_bytes=row["size_bytes"],
        fingerprint=row["fingerprint"],
        status=DocumentStatus(status_value),
        index_status=row["index_status"],
        source_path=row["source_path"],
        duplicate_of=row["duplicate_of"],
        page_count=row["page_count"],
        chunk_count=row["chunk_count"],
        warnings=loads(row["warnings_json"]),
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        indexed_at=row["indexed_at"],
    )


def list_documents() -> list[DocumentRecord]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_document(row) for row in rows]


def get_document(document_id: str) -> DocumentRecord | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    return _row_to_document(row) if row else None


def find_document_by_fingerprint(fingerprint: str) -> DocumentRecord | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
    return _row_to_document(row) if row else None


def create_document(
    *,
    filename: str,
    original_filename: str,
    content_type: str,
    size_bytes: int,
    fingerprint: str,
    source_path: str | None,
    status: DocumentStatus = DocumentStatus.queued,
) -> DocumentRecord:
    document_id = new_id("doc")
    timestamp = _now()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, filename, original_filename, content_type, size_bytes,
                fingerprint, status, index_status, source_path, warnings_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                filename,
                original_filename,
                content_type,
                size_bytes,
                fingerprint,
                status.value,
                "pending",
                source_path,
                dumps([]),
                timestamp,
                timestamp,
            ),
        )
    return get_document(document_id)  # type: ignore[return-value]


def update_document(
    document_id: str,
    *,
    status: DocumentStatus | None = None,
    index_status: str | None = None,
    source_path: str | None = None,
    duplicate_of: str | None = None,
    page_count: int | None = None,
    chunk_count: int | None = None,
    warnings: list[str] | None = None,
    error_message: str | None = None,
    indexed_at: str | None = None,
) -> DocumentRecord | None:
    assignments: list[str] = ["updated_at = ?"]
    values: list[Any] = [_now()]

    if status is not None:
        assignments.append("status = ?")
        values.append(status.value)
    if index_status is not None:
        assignments.append("index_status = ?")
        values.append(index_status)
    if source_path is not None:
        assignments.append("source_path = ?")
        values.append(source_path)
    if duplicate_of is not None:
        assignments.append("duplicate_of = ?")
        values.append(duplicate_of)
    if page_count is not None:
        assignments.append("page_count = ?")
        values.append(page_count)
    if chunk_count is not None:
        assignments.append("chunk_count = ?")
        values.append(chunk_count)
    if warnings is not None:
        assignments.append("warnings_json = ?")
        values.append(dumps(warnings))
    if error_message is not None:
        assignments.append("error_message = ?")
        values.append(error_message)
    if indexed_at is not None:
        assignments.append("indexed_at = ?")
        values.append(indexed_at)

    values.append(document_id)

    with connect() as connection:
        connection.execute(
            f"UPDATE documents SET {', '.join(assignments)} WHERE id = ?",
            values,
        )
    return get_document(document_id)


def delete_document(document_id: str) -> bool:
    document = get_document(document_id)
    if document and document.source_path:
        path = Path(document.source_path)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                for child in path.iterdir():
                    if child.is_file():
                        child.unlink()
                path.rmdir()

    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,),
        )
    return cursor.rowcount > 0


def replace_document_chunks(document_id: str, chunks: list[dict[str, Any]]) -> list[str]:
    chunk_ids: list[str] = []
    with connect() as connection:
        connection.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (document_id,),
        )
        for chunk in chunks:
            chunk_id = new_id("chunk")
            chunk_ids.append(chunk_id)
            connection.execute(
                """
                INSERT INTO document_chunks (
                    id, document_id, chunk_index, content, page_number, section,
                    start_char, end_char, source_label, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    document_id,
                    chunk["chunk_index"],
                    chunk["content"],
                    chunk.get("page_number"),
                    chunk.get("section"),
                    chunk.get("start_char", 0),
                    chunk.get("end_char", 0),
                    chunk["source_label"],
                    _now(),
                ),
            )
    return chunk_ids


def list_document_chunks(document_id: str) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
            """,
            (document_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_ingestion_event(
    document_id: str,
    *,
    event_type: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> str:
    event_id = new_id("event")
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO ingestion_events (
                id, document_id, event_type, message, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                document_id,
                event_type,
                message,
                dumps(details or {}),
                _now(),
            ),
        )
    return event_id
