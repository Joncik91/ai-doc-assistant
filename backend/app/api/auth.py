"""Authentication routes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.credentials import (
    OperatorCredentials,
    Token,
    create_access_token,
    verify_password,
)
from app.api.dependencies import AuthContext, get_auth_context
from app.audit.store import create_audit_event
from app.auth.operators import get_operator_password_hash, operator_exists
from app.observability.metrics import record_auth_login

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _record_failed_login(username: str, reason: str) -> None:
    record_auth_login(outcome="failed", auth_method="jwt")
    create_audit_event(
        actor=username,
        auth_method="jwt",
        action="auth.login_failed",
        resource_type="session",
        outcome="failed",
        details={"reason": reason},
    )


@router.post("/login", response_model=Token, status_code=200)
async def login(credentials: OperatorCredentials) -> Token:
    """
    Operator login endpoint.

    Validates credentials and returns a JWT access token.
    """
    # Check if operator exists
    if not operator_exists(credentials.username):
        logger.warning(f"Login attempt for non-existent operator: {credentials.username}")
        _record_failed_login(credentials.username, "unknown_username")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    password_hash = get_operator_password_hash(credentials.username)
    if not password_hash or not verify_password(credentials.password, password_hash):
        logger.warning(f"Failed login attempt for operator: {credentials.username}")
        _record_failed_login(credentials.username, "invalid_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Issue token
    access_token, expires_at = create_access_token(subject=credentials.username)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    create_audit_event(
        actor=credentials.username,
        auth_method="jwt",
        action="auth.login",
        resource_type="session",
        outcome="success",
        details={"scopes": ["read", "write", "admin"]},
    )
    record_auth_login(outcome="success", auth_method="jwt")
    logger.info(f"Operator logged in: {credentials.username}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/me", status_code=200)
async def get_current_user_info(
    auth_context: AuthContext = Depends(get_auth_context),
):
    """Return the authenticated actor for JWT or API-key based access."""
    return {
        "username": auth_context.username,
        "auth_method": auth_context.auth_method,
        "scopes": auth_context.scopes,
    }
