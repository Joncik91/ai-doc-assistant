"""Shared API dependencies for authentication and authorization."""

from hmac import compare_digest
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth.credentials import Operator, verify_token
from app.auth.operators import get_operator
from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext(BaseModel):
    """Authenticated actor details for the current request."""

    username: str
    auth_method: str
    scopes: list[str] = Field(default_factory=list)


async def get_auth_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> AuthContext:
    """Resolve the current actor from either JWT or API key authentication."""
    if credentials:
        token_data = verify_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        operator = get_operator(token_data.sub)
        if not operator or not operator.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Operator not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthContext(
            username=operator.username,
            auth_method="jwt",
            scopes=operator.scopes,
        )

    if x_api_key:
        settings = get_settings()
        if compare_digest(x_api_key, settings.bootstrap_api_key):
            return AuthContext(
                username="api-key-client",
                auth_method="api_key",
                scopes=["read", "write"],
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_operator(
    auth_context: AuthContext = Depends(get_auth_context),
) -> Operator:
    """Return the current authenticated actor as an operator-shaped object."""
    return Operator(
        username=auth_context.username,
        is_active=True,
        scopes=auth_context.scopes,
    )


async def get_current_admin_operator(
    auth_context: AuthContext = Depends(get_auth_context),
) -> Operator:
    """Ensure the current authenticated actor has admin scope."""
    if "admin" not in auth_context.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return Operator(
        username=auth_context.username,
        is_active=True,
        scopes=auth_context.scopes,
    )
