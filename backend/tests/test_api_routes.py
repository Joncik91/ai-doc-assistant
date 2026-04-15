"""Integration tests for Sprint 1 API routes."""

from fastapi.testclient import TestClient

from app.main import app
from app.auth.operators import bootstrap_operators
from app.config import get_settings


client = TestClient(app)


def setup_module() -> None:
    """Ensure bootstrap auth data exists for route tests."""
    bootstrap_operators()


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_config_endpoint() -> None:
    response = client.get("/api/v1/config")

    assert response.status_code == 200
    body = response.json()
    assert body["app_name"] == "AI Document Assistant"
    assert body["llm_provider"] == "deepseek"


def test_login_with_valid_credentials() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_me_rejects_unauthenticated_requests() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_accepts_jwt_authentication() -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )

    token = login_response.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["auth_method"] == "jwt"


def test_me_accepts_api_key_authentication() -> None:
    settings = get_settings()
    response = client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": settings.bootstrap_api_key},
    )

    assert response.status_code == 200
    assert response.json()["auth_method"] == "api_key"
