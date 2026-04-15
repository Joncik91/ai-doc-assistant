"""Runtime statistics collection for the dashboard."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.stats import RuntimeStatsResponse
from app.observability.metrics import update_runtime_gauges
from app.storage.database import connect, initialize_database

APP_STARTED_AT = datetime.now(timezone.utc)


def collect_runtime_stats() -> RuntimeStatsResponse:
    """Gather local runtime, corpus, and safety statistics."""
    initialize_database()
    now = datetime.now(timezone.utc)

    with connect() as connection:
        document_row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status IN ('completed', 'warning', 'ready') THEN 1 ELSE 0 END), 0) AS ready,
                COALESCE(SUM(CASE WHEN index_status = 'indexed' THEN 1 ELSE 0 END), 0) AS indexed,
                COALESCE(SUM(CASE WHEN duplicate_of IS NOT NULL THEN 1 ELSE 0 END), 0) AS duplicates
            FROM documents
            """
        ).fetchone()
        chunk_row = connection.execute("SELECT COUNT(*) AS total FROM document_chunks").fetchone()
        ingestion_row = connection.execute("SELECT COUNT(*) AS total FROM ingestion_events").fetchone()
        audit_row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(DISTINCT actor) AS distinct_actors,
                MAX(created_at) AS last_activity_at
            FROM audit_events
            """
        ).fetchone()
        query_row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM audit_events
            WHERE action = 'query.executed'
            """
        ).fetchone()
        blocked_row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM audit_events
            WHERE action = 'query.blocked'
            """
        ).fetchone()
        failed_login_row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM audit_events
            WHERE action = 'auth.login_failed'
            """
        ).fetchone()

    stats = RuntimeStatsResponse(
        generated_at=now,
        started_at=APP_STARTED_AT,
        uptime_seconds=int((now - APP_STARTED_AT).total_seconds()),
        documents_total=int(document_row["total"]) if document_row else 0,
        documents_ready=int(document_row["ready"]) if document_row else 0,
        indexed_documents=int(document_row["indexed"]) if document_row else 0,
        chunks_total=int(chunk_row["total"]) if chunk_row else 0,
        duplicate_documents=int(document_row["duplicates"]) if document_row else 0,
        ingestion_events_total=int(ingestion_row["total"]) if ingestion_row else 0,
        audit_events_total=int(audit_row["total"]) if audit_row else 0,
        query_total=int(query_row["total"]) if query_row else 0,
        blocked_queries_total=int(blocked_row["total"]) if blocked_row else 0,
        failed_logins_total=int(failed_login_row["total"]) if failed_login_row else 0,
        distinct_actors=int(audit_row["distinct_actors"]) if audit_row else 0,
        last_activity_at=audit_row["last_activity_at"] if audit_row else None,
    )
    update_runtime_gauges(
        uptime_seconds=stats.uptime_seconds,
        documents_total=stats.documents_total,
        documents_ready=stats.documents_ready,
        indexed_documents=stats.indexed_documents,
        chunks_total=stats.chunks_total,
        audit_events_total=stats.audit_events_total,
        blocked_queries_total=stats.blocked_queries_total,
        failed_logins_total=stats.failed_logins_total,
    )
    return stats
