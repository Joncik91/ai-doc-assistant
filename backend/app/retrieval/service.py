"""Query orchestration for retrieved document chunks."""

from __future__ import annotations

from app.retrieval.generator import QueryResponse, generate_answer
from app.retrieval.store import search_chunks


async def answer_question(question: str, top_k: int) -> QueryResponse:
    """Retrieve context and generate a grounded answer."""
    retrieved_chunks = search_chunks(question, top_k)
    context_chunks = [
        {
            "id": chunk.chunk_id,
            "source": chunk.filename,
            "page": chunk.page_number,
            "text": chunk.content,
            "relevance_score": chunk.score,
        }
        for chunk in retrieved_chunks
    ]
    return await generate_answer(question, context_chunks)
