"""Query orchestration for retrieved document chunks."""

from __future__ import annotations

from app.retrieval.generator import (
    PreparedQueryGeneration,
    QueryResponse,
    generate_answer,
    prepare_query_generation,
)
from app.retrieval.store import search_chunks


def retrieve_context_chunks(question: str, top_k: int) -> list[dict]:
    """Retrieve context chunks in the structure expected by the generator."""
    retrieved_chunks = search_chunks(question, top_k)
    return [
        {
            "id": chunk.chunk_id,
            "source": chunk.filename,
            "page": chunk.page_number,
            "text": chunk.content,
            "relevance_score": chunk.score,
        }
        for chunk in retrieved_chunks
    ]


def prepare_question_answer(question: str, top_k: int) -> PreparedQueryGeneration:
    """Prepare the provider request and citations for a question."""
    return prepare_query_generation(question, retrieve_context_chunks(question, top_k))


async def answer_question(question: str, top_k: int) -> QueryResponse:
    """Retrieve context and generate a grounded answer."""
    return await generate_answer(question, retrieve_context_chunks(question, top_k))
