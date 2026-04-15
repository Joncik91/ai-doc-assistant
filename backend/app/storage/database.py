"""SQLite persistence helpers for documents and ingestion metadata."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from app.config import get_settings

SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database_path() -> Path:
    settings = get_settings()
    url = settings.database_url
    if not url.startswith("sqlite://"):
        raise ValueError(f"Unsupported database URL: {url}")
    if url == "sqlite:///:memory:":
        return Path(":memory:")
    if url.startswith("sqlite:////"):
        return Path(url.removeprefix("sqlite:///"))
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///"))
    raise ValueError(f"Unsupported database URL: {url}")


def get_database_path() -> Path:
    """Return the configured SQLite database path."""
    return _database_path()


def get_storage_root() -> Path:
    """Return the directory used for persisted source files."""
    settings = get_settings()
    path = Path(settings.document_storage_directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    """Open a configured SQLite connection."""
    database_path = get_database_path()
    if database_path.name != ":memory:":
        database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        ":memory:" if database_path.name == ":memory:" else database_path,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create document registry tables if they do not already exist."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                index_status TEXT NOT NULL DEFAULT 'pending',
                source_path TEXT,
                duplicate_of TEXT,
                page_count INTEGER NOT NULL DEFAULT 0,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                warnings_json TEXT NOT NULL DEFAULT '[]',
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                indexed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER,
                section TEXT,
                start_char INTEGER NOT NULL DEFAULT 0,
                end_char INTEGER NOT NULL DEFAULT 0,
                source_label TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ingestion_events (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                auth_method TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                outcome TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
            CREATE INDEX IF NOT EXISTS idx_documents_index_status ON documents(index_status);
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
            CREATE INDEX IF NOT EXISTS idx_events_document_id ON ingestion_events(document_id);
            CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor, created_at DESC);
            """
        )


def reset_local_state() -> None:
    """Remove local development state for a clean test run."""
    settings = get_settings()
    database_path = get_database_path()
    if database_path.exists() and database_path.name != ":memory:":
        database_path.unlink()

    for directory in (
        Path(settings.document_storage_directory),
    ):
        if directory.exists():
            import shutil

            shutil.rmtree(directory)

    try:
        from app.retrieval.store import COLLECTION_NAME, get_client, get_collection

        client = get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        get_client.cache_clear()
        get_collection.cache_clear()
    except Exception:
        pass

    try:
        from app.guardrails.rate_limit import reset_rate_limits

        reset_rate_limits()
    except Exception:
        pass


def new_id(prefix: str) -> str:
    """Generate a stable opaque identifier for persisted records."""
    return f"{prefix}_{uuid4().hex}"


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def loads(value: str | None, default: Iterable[str] | None = None) -> list[str]:
    if not value:
        return list(default or [])
    parsed = json.loads(value)
    return list(parsed) if isinstance(parsed, list) else list(default or [])
