"""Query generation service using the LLM provider."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider import Message, GenerationRequest, GenerationResponse
from app.llm.factory import get_provider

class Citation(BaseModel):
    """Citation reference in an answer."""

    source: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    relevance_score: float = 0.0
    excerpt: Optional[str] = None


class QueryResponse(BaseModel):
    """Response to a query with citations."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.5  # 0-1, how confident the answer is
    finish_reason: str  # "stop", "length", "error"
    disclaimer: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "This document discusses...",
                "citations": [
                    {
                        "source": "document.pdf",
                        "page": 1,
                        "chunk_id": "chunk-001",
                        "relevance_score": 0.95,
                    }
                ],
                "confidence": 0.85,
                "finish_reason": "stop",
                "disclaimer": "This answer is based on retrieved documents and may not be 100% accurate.",
            }
        }
    )


async def generate_answer(
    query: str,
    context_chunks: list[dict],
    system_prompt: Optional[str] = None,
) -> QueryResponse:
    """
    Generate an answer to a query using retrieved context.

    Args:
        query: The user's question
        context_chunks: Retrieved chunks with source metadata
        system_prompt: Optional custom system prompt

    Returns: QueryResponse with answer and citations
    """
    provider = get_provider()

    # Build context string from chunks
    context_text = "\n\n".join(
        [f"[Source: {chunk.get('source', 'unknown')}]\n{chunk.get('text', '')}" for chunk in context_chunks]
    )

    # Build system prompt
    if not system_prompt:
        system_prompt = """You are a helpful document analysis assistant.
Answer questions based only on the provided document context.
If the context doesn't contain relevant information, say so clearly.
Be concise and accurate."""

    # Build messages
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=f"Context:\n{context_text}\n\nQuestion: {query}"),
    ]

    # Generate
    request = GenerationRequest(
        messages=messages,
        model=None,
        temperature=0.5,
        max_tokens=2000,
    )

    response: GenerationResponse = await provider.generate(request)

    # Build citations from context
    citations = [
        Citation(
            source=chunk.get("source", "unknown"),
            page=chunk.get("page"),
            chunk_id=chunk.get("id"),
            relevance_score=chunk.get("relevance_score", 0.0),
            excerpt=chunk.get("text", "")[:400] if chunk.get("text") else None,
        )
        for chunk in context_chunks
    ]

    # Add disclaimer if confidence is low or no context
    disclaimer = None
    confidence = 0.8
    if not context_chunks:
        disclaimer = "This answer was generated without document context and may not be accurate."
        confidence = 0.3
    elif response.finish_reason == "length":
        disclaimer = "Answer was truncated due to length limit."
        confidence = 0.6

    return QueryResponse(
        answer=response.content,
        citations=citations,
        confidence=confidence,
        finish_reason=response.finish_reason,
        disclaimer=disclaimer,
    )
