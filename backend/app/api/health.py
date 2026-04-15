"""Health endpoints for retrieval subsystems."""

from __future__ import annotations

from fastapi import APIRouter

from app.retrieval.store import retrieval_health

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/retrieval")
async def retrieval_status() -> dict:
    return retrieval_health()

