"""
Centralized environment-driven configuration with type safety.
All settings are loaded from environment variables at startup.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    # App metadata
    app_name: str = "AI Document Assistant"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin"
    bootstrap_api_key: str = "dev-api-key-change-in-production"

    # LLM Provider (DeepSeek)
    llm_provider: str = "deepseek"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.5
    llm_max_tokens: int = 2000

    # Vector store (ChromaDB)
    chroma_persist_directory: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    document_storage_directory: str = "./data/documents"

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
