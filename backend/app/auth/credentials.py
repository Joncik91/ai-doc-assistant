"""JWT and credential management."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


class TokenData(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (username)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    scopes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "operator@admin",
                "iat": "2024-04-15T18:00:00Z",
                "exp": "2024-04-15T19:00:00Z",
                "scopes": ["read", "write"],
            }
        }
    )


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """
    Create a JWT access token.

    Returns: (token_string, expiration_datetime)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": subject,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt, expire


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token.

    Returns: TokenData if valid, None if invalid.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject: str = payload.get("sub")
        if subject is None:
            return None
        return TokenData(
            sub=subject,
            iat=datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc),
            exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
            scopes=payload.get("scopes", []),
        )
    except JWTError:
        return None


class OperatorCredentials(BaseModel):
    """Operator login credentials."""

    username: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "secure-password",
            }
        }
    )


class Operator(BaseModel):
    """Authenticated operator."""

    username: str
    is_active: bool = True
    scopes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "is_active": True,
                "scopes": ["read", "write"],
            }
        }
    )
