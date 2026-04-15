"""Document and ingestion models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    """Lifecycle state for an uploaded document."""

    queued = "queued"
    processing = "processing"
    completed = "completed"
    warning = "warning"
    failed = "failed"


class DocumentRecord(BaseModel):
    """Persisted document metadata."""

    id: str
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    fingerprint: str
    status: DocumentStatus
    index_status: str = "pending"
    source_path: str | None = None
    duplicate_of: str | None = None
    page_count: int = 0
    chunk_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc_01HX...",
                "filename": "employee-handbook.pdf",
                "original_filename": "employee-handbook.pdf",
                "content_type": "application/pdf",
                "size_bytes": 124002,
                "fingerprint": "7f7a1b0c...",
                "status": "completed",
                "index_status": "pending",
                "source_path": "./data/documents/doc_01HX.../employee-handbook.pdf",
                "duplicate_of": None,
                "page_count": 18,
                "chunk_count": 24,
                "warnings": [],
                "error_message": None,
                "created_at": "2026-04-15T16:54:49Z",
                "updated_at": "2026-04-15T16:54:49Z",
                "indexed_at": None,
            }
        }
    )


class DocumentListResponse(BaseModel):
    """List of stored documents."""

    documents: list[DocumentRecord]


class DocumentUploadResponse(BaseModel):
    """Response returned after an upload attempt."""

    filename: str
    document: DocumentRecord | None = None
    created: bool
    duplicate: bool
    warning: bool
    chunks_created: int
    message: str | None = None
    error: str | None = None


class DocumentBatchUploadResponse(BaseModel):
    """Response returned after a multi-file upload attempt."""

    results: list[DocumentUploadResponse]
    processed_count: int
    created_count: int
    warning_count: int
    duplicate_count: int
    failed_count: int
    message: str | None = None


class DocumentDeleteResponse(BaseModel):
    """Response returned after deleting a document."""

    document_id: str
    deleted: bool = True
