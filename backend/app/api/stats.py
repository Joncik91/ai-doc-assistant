"""Runtime statistics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext, get_auth_context
from app.models.stats import RuntimeStatsResponse
from app.observability.stats import collect_runtime_stats

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("", response_model=RuntimeStatsResponse)
async def get_runtime_stats(_: AuthContext = Depends(get_auth_context)) -> RuntimeStatsResponse:
    """Return the current local runtime snapshot."""
    return collect_runtime_stats()
