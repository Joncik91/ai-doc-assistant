"""Document registry and ingestion routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import AuthContext, get_auth_context
from app.config import get_settings
from app.audit.store import create_audit_event
from app.ingestion.service import ingest_upload
from app.models.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentRecord,
    DocumentUploadResponse,
)
from app.retrieval.store import remove_document as remove_document_vectors
from app.storage.documents import delete_document, get_document, list_documents

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
logger = logging.getLogger(__name__)
READ_CHUNK_SIZE_BYTES = 1024 * 1024


async def _read_upload(file: UploadFile) -> bytes:
    settings = get_settings()
    max_size_bytes = settings.max_upload_size_bytes

    if file.size is not None and file.size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds the {max_size_bytes}-byte limit.",
        )

    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(READ_CHUNK_SIZE_BYTES)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds the {max_size_bytes}-byte limit.",
            )
        chunks.append(chunk)

    data = b"".join(chunks)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    return data


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    auth_context: AuthContext = Depends(get_auth_context),
) -> DocumentUploadResponse:
    content = await _read_upload(file)
    document, created, chunk_count = ingest_upload(
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    create_audit_event(
        actor=auth_context.username,
        auth_method=auth_context.auth_method,
        action="document.uploaded" if created else "document.duplicate",
        resource_type="document",
        resource_id=document.id,
        outcome="success" if created else "duplicate",
        details={
            "filename": document.original_filename,
            "size_bytes": document.size_bytes,
            "chunks_created": chunk_count,
        },
    )
    return DocumentUploadResponse(
        document=document,
        created=created,
        duplicate=not created,
        chunks_created=chunk_count,
        message="Document ingested." if created else "Duplicate document ignored.",
    )


@router.get("", response_model=DocumentListResponse)
async def get_documents(_: AuthContext = Depends(get_auth_context)) -> DocumentListResponse:
    return DocumentListResponse(documents=list_documents())


@router.get("/{document_id}", response_model=DocumentRecord)
async def get_document_detail(
    document_id: str,
    _: AuthContext = Depends(get_auth_context),
) -> DocumentRecord:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def remove_document(
    document_id: str,
    auth_context: AuthContext = Depends(get_auth_context),
) -> DocumentDeleteResponse:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        remove_document_vectors(document_id)
    except Exception as exc:  # noqa: BLE001 - surface vector-store outages at the API boundary
        logger.error("Failed to remove vectors for %s: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store unavailable. Document was not deleted.",
        ) from exc

    deleted = delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    create_audit_event(
        actor=auth_context.username,
        auth_method=auth_context.auth_method,
        action="document.deleted",
        resource_type="document",
        resource_id=document_id,
        outcome="success",
        details={},
    )
    return DocumentDeleteResponse(document_id=document_id, deleted=True)
