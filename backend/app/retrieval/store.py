"""Chroma-backed chunk storage and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb

from app.config import get_settings
from app.retrieval.embeddings import DEFAULT_EMBEDDING_DIMENSIONS, HashEmbeddingFunction
from app.storage.documents import get_document, list_document_chunks, update_document

COLLECTION_NAME = "document_chunks"


@dataclass(slots=True)
class RetrievedChunk:
    """Chunk returned from semantic search."""

    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    section: str | None
    content: str
    score: float


def _persist_directory() -> Path:
    settings = get_settings()
    path = Path(settings.chroma_persist_directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_client() -> chromadb.PersistentClient:
    """Create or reuse the local Chroma client."""
    return chromadb.PersistentClient(path=str(_persist_directory()))


@lru_cache
def get_collection():
    """Get the document chunk collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_texts(texts: list[str]) -> list[list[float]]:
    embedder = HashEmbeddingFunction(DEFAULT_EMBEDDING_DIMENSIONS)
    return embedder(texts)


def index_document(document_id: str) -> int:
    """Index persisted chunks for a document into Chroma."""
    document = get_document(document_id)
    if not document:
        raise ValueError(f"Document not found: {document_id}")

    chunks = list_document_chunks(document_id)
    if not chunks:
        return 0

    collection = get_collection()
    collection.delete(where={"document_id": document_id})

    ids = [chunk["id"] for chunk in chunks]
    embeddings = _embed_texts([chunk["content"] for chunk in chunks])
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "filename": document.original_filename,
            "page_number": chunk["page_number"],
            "section": chunk["section"] or "",
            "source_label": chunk["source_label"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    indexed_at = datetime.now(timezone.utc).isoformat()
    update_document(
        document_id,
        index_status="indexed",
        indexed_at=indexed_at,
    )
    return len(ids)


def remove_document(document_id: str) -> None:
    """Remove a document from the vector store."""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})


def search_chunks(question: str, top_k: int) -> list[RetrievedChunk]:
    """Return the most relevant chunks for a question."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = _embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved: list[RetrievedChunk] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    for index, chunk_id in enumerate(ids):
        metadata: dict[str, Any] = metadatas[index] if index < len(metadatas) else {}
        score = 1.0 - float(distances[index]) if index < len(distances) else 0.0
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                document_id=metadata.get("document_id", ""),
                filename=metadata.get("filename", "document"),
                page_number=metadata.get("page_number"),
                section=metadata.get("section") or None,
                content=documents[index] if index < len(documents) else "",
                score=max(0.0, min(1.0, score)),
            )
        )
    return retrieved


def retrieval_health() -> dict[str, Any]:
    """Expose vector-store readiness for health checks."""
    try:
        collection = get_collection()
        return {
            "healthy": True,
            "status": "ready",
            "collection": COLLECTION_NAME,
            "persist_directory": str(_persist_directory()),
            "indexed_chunks": collection.count(),
            "indexed_documents": _count_indexed_documents(),
            "embedding_dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        }
    except Exception as exc:  # noqa: BLE001 - health should report the failure details
        return {
            "healthy": False,
            "status": "unavailable",
            "collection": COLLECTION_NAME,
            "persist_directory": str(_persist_directory()),
            "error": str(exc),
        }


def _count_indexed_documents() -> int:
    from app.storage.database import connect

    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM documents WHERE index_status = 'indexed'"
        ).fetchone()
    return int(row["count"]) if row else 0
