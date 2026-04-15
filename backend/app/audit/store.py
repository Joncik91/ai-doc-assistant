"""SQLite-backed audit event storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.models.audit import AuditEventRecord
from app.storage.database import connect, dumps, initialize_database, new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_event(row: Any) -> AuditEventRecord:
    return AuditEventRecord(
        id=row["id"],
        actor=row["actor"],
        auth_method=row["auth_method"],
        action=row["action"],
        resource_type=row["resource_type"],
        resource_id=row["resource_id"],
        outcome=row["outcome"],
        details=_decode_details(row["details_json"]),
        created_at=row["created_at"],
    )


def _decode_details(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def create_audit_event(
    *,
    actor: str,
    auth_method: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    outcome: str,
    details: dict[str, Any] | None = None,
) -> AuditEventRecord:
    initialize_database()
    event_id = new_id("audit")
    timestamp = _now()
    payload_details = details or {}
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (
                id, actor, auth_method, action, resource_type, resource_id,
                outcome, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                actor,
                auth_method,
                action,
                resource_type,
                resource_id,
                outcome,
                dumps(payload_details),
                timestamp,
            ),
        )
    return AuditEventRecord(
        id=event_id,
        actor=actor,
        auth_method=auth_method,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        details=payload_details,
        created_at=timestamp,
    )


def list_audit_events(limit: int = 50) -> list[AuditEventRecord]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM audit_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    events: list[AuditEventRecord] = []
    for row in rows:
        events.append(_row_to_event(row))
    return events
