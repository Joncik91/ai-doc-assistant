"""High-level document ingestion workflow."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.ingestion.chunker import chunk_pages
from app.ingestion.extractors import extract_document
from app.models.document import DocumentRecord, DocumentStatus
from app.storage.database import get_storage_root
from app.storage.documents import (
    create_document,
    create_ingestion_event,
    find_document_by_fingerprint,
    replace_document_chunks,
    update_document,
)
from app.retrieval.store import index_document


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._")
    return cleaned or "document"


async def _read_upload(upload: UploadFile) -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )
    return data


def _fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _storage_path(document_id: str, filename: str) -> Path:
    destination = get_storage_root() / document_id
    destination.mkdir(parents=True, exist_ok=True)
    return destination / _safe_filename(filename)


def ingest_upload(
    *,
    filename: str,
    content_type: str,
    content: bytes,
) -> tuple[DocumentRecord, bool, int]:
    """Persist an uploaded file and extract chunks."""

    fingerprint = _fingerprint(content)
    existing = find_document_by_fingerprint(fingerprint)
    if existing:
        create_ingestion_event(
            existing.id,
            event_type="duplicate",
            message="Duplicate upload ignored.",
            details={"filename": filename, "fingerprint": fingerprint},
        )
        return existing, False, 0

    document = create_document(
        filename=_safe_filename(filename),
        original_filename=filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(content),
        fingerprint=fingerprint,
        source_path=None,
        status=DocumentStatus.uploaded,
    )
    assert document is not None

    source_path = _storage_path(document.id, filename)
    source_path.write_bytes(content)
    update_document(document.id, source_path=str(source_path))

    update_document(document.id, status=DocumentStatus.processing)
    create_ingestion_event(
        document.id,
        event_type="uploaded",
        message="Upload stored and ready for extraction.",
        details={"size_bytes": len(content), "fingerprint": fingerprint},
    )

    try:
        extraction = extract_document(source_path)
        if not extraction.text.strip():
            extraction.warnings.append("No extractable text was found in the document.")

        chunks = chunk_pages(
            extraction.pages,
            source_label=document.original_filename,
        )
        chunk_payloads = [
            {
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "section": chunk.section,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "source_label": chunk.source_label,
            }
            for chunk in chunks
        ]
        replace_document_chunks(document.id, chunk_payloads)
        index_document(document.id)

        indexed_document = update_document(
            document.id,
            status=DocumentStatus.ready,
            index_status="indexed",
            page_count=len(extraction.pages),
            chunk_count=len(chunk_payloads),
            warnings=extraction.warnings,
        )
        create_ingestion_event(
            document.id,
            event_type="extracted",
            message="Document extracted and chunked.",
            details={
                "page_count": len(extraction.pages),
                "chunk_count": len(chunk_payloads),
                "warnings": extraction.warnings,
            },
        )
        return indexed_document or document, True, len(chunk_payloads)
    except Exception as exc:  # noqa: BLE001 - persist the failure for the operator
        update_document(
            document.id,
            status=DocumentStatus.failed,
            error_message=str(exc),
        )
        create_ingestion_event(
            document.id,
            event_type="failed",
            message="Document ingestion failed.",
            details={"error": str(exc)},
        )
        raise
