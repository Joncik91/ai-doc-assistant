"""Simple fixed-window in-memory rate limiting."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Deque

from fastapi import HTTPException, status

from app.config import get_settings

_WINDOWS: dict[tuple[str, str], Deque[datetime]] = defaultdict(deque)
_LOCK = Lock()


def reset_rate_limits() -> None:
    """Clear tracked request windows (test helper)."""
    with _LOCK:
        _WINDOWS.clear()


def enforce_rate_limit(actor: str, route: str) -> None:
    """Raise 429 if the actor has exceeded the configured window."""
    settings = get_settings()
    window = timedelta(minutes=settings.rate_limit_period_minutes)
    now = datetime.now(timezone.utc)
    key = (actor, route)

    with _LOCK:
        bucket = _WINDOWS[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= settings.rate_limit_requests:
            retry_after = max(1, int((window - (now - bucket[0])).total_seconds()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            )

        bucket.append(now)
