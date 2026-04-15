"""Audit event routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AuthContext, get_auth_context
from app.audit.store import list_audit_events
from app.models.audit import AuditEventListResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventListResponse)
async def get_events(
    limit: int = Query(default=50, ge=1, le=100),
    _: AuthContext = Depends(get_auth_context),
) -> AuditEventListResponse:
    return AuditEventListResponse(events=list_audit_events(limit=limit))
