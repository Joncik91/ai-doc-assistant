"""Request middleware for observability."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.context import reset_request_id, set_request_id
from app.observability.metrics import record_http_request

logger = logging.getLogger(__name__)


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None:
        return getattr(route, "path", request.url.path)
    return request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach request ids, structured logging, and HTTP metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        request_token = set_request_id(request_id)
        started = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_seconds = perf_counter() - started
            route_label = _route_label(request)
            record_http_request(request.method, route_label, 500, duration_seconds)
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": route_label,
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
            )
            raise
        else:
            duration_seconds = perf_counter() - started
            route_label = _route_label(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_seconds:.3f}"
            record_http_request(request.method, route_label, status_code, duration_seconds)
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": route_label,
                    "status_code": status_code,
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
            )
            return response
        finally:
            reset_request_id(request_token)
