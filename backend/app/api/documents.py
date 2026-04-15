"""Document registry and ingestion routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import AuthContext, get_auth_context
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


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    return data


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    _: AuthContext = Depends(get_auth_context),
) -> DocumentUploadResponse:
    content = await _read_upload(file)
    document, created, chunk_count = ingest_upload(
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
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
    _: AuthContext = Depends(get_auth_context),
) -> DocumentDeleteResponse:
    remove_document_vectors(document_id)
    deleted = delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentDeleteResponse(document_id=document_id, deleted=True)
