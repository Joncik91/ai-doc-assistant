"""Test authentication flow."""

from app.auth.credentials import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
)
from app.auth.operators import bootstrap_operators, get_operator, operator_exists


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test-password-123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_creation_and_verification():
    """Test JWT token creation and verification."""
    subject = "test-operator"
    token, expires_at = create_access_token(subject)
    
    assert token
    assert expires_at
    
    token_data = verify_token(token)
    assert token_data
    assert token_data.sub == subject


def test_invalid_token_verification():
    """Test verification of invalid token."""
    invalid_token = "invalid.token.here"
    assert verify_token(invalid_token) is None


def test_operator_bootstrap():
    """Test operator bootstrapping."""
    bootstrap_operators()
    
    # Default admin should exist
    assert operator_exists("admin")
    operator = get_operator("admin")
    assert operator
    assert operator.username == "admin"
    assert operator.is_active
    assert "admin" in operator.scopes


def test_operator_password_verification():
    """Test operator password verification."""
    from app.auth.operators import get_operator_password_hash
    from app.auth.credentials import verify_password
    
    bootstrap_operators()
    
    password_hash = get_operator_password_hash("admin")
    assert password_hash
    
    # Verify with default password (from settings)
    from app.config import get_settings
    settings = get_settings()
    assert verify_password(settings.bootstrap_admin_password, password_hash)
