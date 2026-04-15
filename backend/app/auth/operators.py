"""Operator store and bootstrap."""

from typing import Optional
from app.auth.credentials import Operator, hash_password

# In-memory operator store for v1
# In production, this would be backed by a real database
_operator_store: dict[str, dict] = {}


def bootstrap_operators() -> None:
    """Initialize bootstrap operator credentials from environment."""
    from app.config import get_settings

    settings = get_settings()

    bootstrap_user = settings.bootstrap_admin_username
    bootstrap_pass = settings.bootstrap_admin_password

    if not _operator_store.get(bootstrap_user):
        _operator_store[bootstrap_user] = {
            "username": bootstrap_user,
            "password_hash": hash_password(bootstrap_pass),
            "is_active": True,
            "scopes": ["read", "write", "admin"],
        }


def get_operator(username: str) -> Optional[Operator]:
    """Get an operator by username."""
    if not _operator_store:
        bootstrap_operators()

    op = _operator_store.get(username)
    if op:
        return Operator(
            username=op["username"],
            is_active=op["is_active"],
            scopes=op.get("scopes", []),
        )
    return None


def get_operator_password_hash(username: str) -> Optional[str]:
    """Get the password hash for an operator (for verification)."""
    if not _operator_store:
        bootstrap_operators()

    op = _operator_store.get(username)
    return op.get("password_hash") if op else None


def operator_exists(username: str) -> bool:
    """Check if an operator exists."""
    if not _operator_store:
        bootstrap_operators()
    return username in _operator_store
