"""Audit event models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRecord(BaseModel):
    """Persisted operator event."""

    id: str
    actor: str
    auth_method: str
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "audit_01HX...",
                "actor": "admin",
                "auth_method": "jwt",
                "action": "query.executed",
                "resource_type": "query",
                "resource_id": "query_01HX...",
                "outcome": "success",
                "details": {"top_k": 4},
                "created_at": "2026-04-15T16:54:49Z",
            }
        }
    )


class AuditEventListResponse(BaseModel):
    """List of audit events."""

    events: list[AuditEventRecord]
