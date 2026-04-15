"""High-level document ingestion workflow."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from fastapi import HTTPException, status

from app.guardrails.pii import scan_text_for_pii
from app.ingestion.chunker import chunk_pages
from app.ingestion.extractors import extract_document
from app.models.document import DocumentStatus, DocumentUploadResponse
from app.retrieval.store import index_document
from app.storage.database import get_storage_root
from app.storage.documents import (
    create_document,
    create_ingestion_event,
    find_document_by_fingerprint,
    replace_document_chunks,
    update_document,
)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._")
    return cleaned or "document"


def _fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _storage_path(document_id: str, filename: str) -> Path:
    destination = get_storage_root() / document_id
    destination.mkdir(parents=True, exist_ok=True)
    return destination / _safe_filename(filename)


def _deduplicate_warnings(*groups: list[str]) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for warning in group:
            normalized = warning.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                warnings.append(normalized)
    return warnings


def ingest_upload(
    *,
    filename: str,
    content_type: str,
    content: bytes,
    strict_errors: bool = False,
) -> DocumentUploadResponse:
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
        return DocumentUploadResponse(
            filename=filename,
            document=existing,
            created=False,
            duplicate=True,
            warning=False,
            chunks_created=0,
            message="Duplicate document ignored.",
        )

    document = create_document(
        filename=_safe_filename(filename),
        original_filename=filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(content),
        fingerprint=fingerprint,
        source_path=None,
        status=DocumentStatus.queued,
    )
    assert document is not None

    try:
        source_path = _storage_path(document.id, filename)
        source_path.write_bytes(content)
        update_document(document.id, source_path=str(source_path), status=DocumentStatus.processing)
        create_ingestion_event(
            document.id,
            event_type="uploaded",
            message="Upload stored and ready for extraction.",
            details={"size_bytes": len(content), "fingerprint": fingerprint},
        )

        extraction = extract_document(source_path)
        warnings = list(extraction.warnings)
        if not extraction.text.strip():
            warnings.append("No extractable text was found in the document.")

        pii_findings = scan_text_for_pii(extraction.text)
        warnings = _deduplicate_warnings(warnings, [finding.warning for finding in pii_findings])

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

        final_status = DocumentStatus.warning if warnings else DocumentStatus.completed
        indexed_document = update_document(
            document.id,
            status=final_status,
            index_status="indexed",
            page_count=len(extraction.pages),
            chunk_count=len(chunk_payloads),
            warnings=warnings,
        )
        create_ingestion_event(
            document.id,
            event_type="warning" if warnings else "completed",
            message="Document ingested with warnings." if warnings else "Document ingested.",
            details={
                "page_count": len(extraction.pages),
                "chunk_count": len(chunk_payloads),
                "warnings": warnings,
                "pii_findings": [asdict(finding) for finding in pii_findings],
            },
        )
        return DocumentUploadResponse(
            filename=filename,
            document=indexed_document or document,
            created=True,
            duplicate=False,
            warning=bool(warnings),
            chunks_created=len(chunk_payloads),
            message="Document ingested with warnings." if warnings else "Document ingested.",
        )
    except ValueError as exc:
        failed_document = update_document(
            document.id,
            status=DocumentStatus.failed,
            error_message=str(exc),
        )
        create_ingestion_event(
            document.id,
            event_type="failed",
            message="Document ingestion failed validation.",
            details={"error": str(exc)},
        )
        if strict_errors:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc
        return DocumentUploadResponse(
            filename=filename,
            document=failed_document or document,
            created=False,
            duplicate=False,
            warning=False,
            chunks_created=0,
            message=str(exc),
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 - surface the failure to the operator
        failed_document = update_document(
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
        if strict_errors:
            raise
        return DocumentUploadResponse(
            filename=filename,
            document=failed_document or document,
            created=False,
            duplicate=False,
            warning=False,
            chunks_created=0,
            message=str(exc),
            error=str(exc),
        )
