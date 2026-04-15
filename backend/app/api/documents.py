"""Document registry and ingestion routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import AuthContext, get_auth_context
from app.config import get_settings
from app.audit.store import create_audit_event
from app.ingestion.service import ingest_upload
from app.models.document import (
    DocumentBatchUploadResponse,
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentRecord,
    DocumentUploadResponse,
)
from app.observability.metrics import record_document_operation
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


def _result_outcome(result: DocumentUploadResponse) -> str:
    if result.error:
        return "failed"
    if result.duplicate:
        return "duplicate"
    if result.warning:
        return "warning"
    return "success"


def _audit_action(result: DocumentUploadResponse) -> str:
    if result.error:
        return "document.upload_failed"
    if result.duplicate:
        return "document.duplicate"
    if result.warning:
        return "document.warning"
    return "document.uploaded"


async def _process_upload(
    file: UploadFile,
    auth_context: AuthContext,
    *,
    fail_fast: bool,
) -> DocumentUploadResponse:
    filename = file.filename or "document"
    try:
        content = await _read_upload(file)
    except HTTPException as exc:
        message = str(exc.detail)
        create_audit_event(
            actor=auth_context.username,
            auth_method=auth_context.auth_method,
            action="document.upload_failed",
            resource_type="document",
            resource_id=None,
            outcome="failed",
            details={
                "filename": filename,
                "error": message,
                "stage": "validation",
            },
        )
        record_document_operation(operation="upload", outcome="failed")
        if fail_fast:
            raise
        return DocumentUploadResponse(
            filename=filename,
            document=None,
            created=False,
            duplicate=False,
            warning=False,
            chunks_created=0,
            message=message,
            error=message,
        )

    try:
        result = ingest_upload(
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            content=content,
            strict_errors=fail_fast,
        )
    except HTTPException as exc:
        message = str(exc.detail)
        create_audit_event(
            actor=auth_context.username,
            auth_method=auth_context.auth_method,
            action="document.upload_failed",
            resource_type="document",
            resource_id=None,
            outcome="failed",
            details={
                "filename": filename,
                "error": message,
                "stage": "ingestion",
            },
        )
        record_document_operation(operation="upload", outcome="failed")
        raise
    details = {
        "filename": result.filename,
        "size_bytes": len(content),
        "chunks_created": result.chunks_created,
    }
    if result.document is not None:
        details["document_status"] = result.document.status.value
        details["warnings"] = result.document.warnings
        details["index_status"] = result.document.index_status
    if result.error:
        details["error"] = result.error

    create_audit_event(
        actor=auth_context.username,
        auth_method=auth_context.auth_method,
        action=_audit_action(result),
        resource_type="document",
        resource_id=result.document.id if result.document else None,
        outcome=_result_outcome(result),
        details=details,
    )
    record_document_operation(
        operation="upload",
        outcome=_result_outcome(result),
    )
    return result


def _summarize_uploads(results: list[DocumentUploadResponse]) -> DocumentBatchUploadResponse:
    created_count = sum(1 for result in results if result.created)
    warning_count = sum(1 for result in results if result.warning)
    duplicate_count = sum(1 for result in results if result.duplicate)
    failed_count = sum(1 for result in results if result.error)
    processed_count = len(results)
    message = (
        f"Processed {processed_count} file(s): {created_count} created, "
        f"{warning_count} with warnings, {duplicate_count} duplicates, {failed_count} failed."
    )
    return DocumentBatchUploadResponse(
        results=results,
        processed_count=processed_count,
        created_count=created_count,
        warning_count=warning_count,
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        message=message,
    )


@router.post("/upload", response_model=DocumentBatchUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    auth_context: AuthContext = Depends(get_auth_context),
) -> DocumentBatchUploadResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file must be provided.",
        )

    fail_fast = len(files) == 1
    results: list[DocumentUploadResponse] = []
    for file in files:
        results.append(await _process_upload(file, auth_context, fail_fast=fail_fast))
    return _summarize_uploads(results)


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
    record_document_operation(operation="delete", outcome="success")
    return DocumentDeleteResponse(document_id=document_id, deleted=True)
