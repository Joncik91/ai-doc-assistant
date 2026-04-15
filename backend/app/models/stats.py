"""Runtime statistics returned by the operator dashboard."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RuntimeStatsResponse(BaseModel):
    """Aggregated runtime and corpus statistics."""

    generated_at: datetime
    started_at: datetime
    uptime_seconds: int
    documents_total: int
    documents_ready: int
    indexed_documents: int
    chunks_total: int
    duplicate_documents: int
    ingestion_events_total: int
    audit_events_total: int
    query_total: int
    blocked_queries_total: int
    failed_logins_total: int
    distinct_actors: int
    last_activity_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generated_at": "2026-04-15T19:00:00Z",
                "started_at": "2026-04-15T18:45:00Z",
                "uptime_seconds": 900,
                "documents_total": 4,
                "documents_ready": 4,
                "indexed_documents": 4,
                "chunks_total": 18,
                "duplicate_documents": 1,
                "ingestion_events_total": 12,
                "audit_events_total": 8,
                "query_total": 3,
                "blocked_queries_total": 1,
                "failed_logins_total": 0,
                "distinct_actors": 1,
                "last_activity_at": "2026-04-15T18:59:20Z",
            }
        }
    )
