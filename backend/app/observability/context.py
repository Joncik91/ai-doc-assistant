"""Request-scoped observability context."""

from __future__ import annotations

from contextvars import ContextVar, Token

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> Token[str | None]:
    """Store the active request id for log correlation."""
    return request_id_var.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    """Restore the previous request id."""
    request_id_var.reset(token)


def get_request_id() -> str | None:
    """Return the active request id, if any."""
    return request_id_var.get()
