"""Query generation service using the LLM provider."""

from dataclasses import dataclass
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


@dataclass(slots=True)
class PreparedQueryGeneration:
    """Prepared generation request plus citation metadata."""

    request: GenerationRequest
    citations: list[Citation]
    has_context: bool


def prepare_query_generation(
    query: str,
    context_chunks: list[dict],
    system_prompt: Optional[str] = None,
) -> PreparedQueryGeneration:
    """Build the provider request and response metadata for a query."""
    context_text = "\n\n".join(
        f"[Source: {chunk.get('source', 'unknown')}]\n{chunk.get('text', '')}"
        for chunk in context_chunks
    )

    if not system_prompt:
        system_prompt = """You are a helpful document analysis assistant.
Answer questions based only on the provided document context.
If the context doesn't contain relevant information, say so clearly.
Be concise and accurate."""

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=f"Context:\n{context_text}\n\nQuestion: {query}"),
    ]

    request = GenerationRequest(
        messages=messages,
        model=None,
        temperature=0.5,
        max_tokens=2000,
    )

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

    return PreparedQueryGeneration(
        request=request,
        citations=citations,
        has_context=bool(context_chunks),
    )


def build_query_response(
    *,
    answer: str,
    finish_reason: str,
    citations: list[Citation],
    has_context: bool,
) -> QueryResponse:
    """Build the final query response from generated text and retrieval metadata."""
    disclaimer = None
    confidence = 0.8

    if not has_context:
        disclaimer = "This answer was generated without document context and may not be accurate."
        confidence = 0.3
    elif finish_reason == "length":
        disclaimer = "Answer was truncated due to length limit."
        confidence = 0.6

    return QueryResponse(
        answer=answer,
        citations=citations,
        confidence=confidence,
        finish_reason=finish_reason,
        disclaimer=disclaimer,
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
    prepared = prepare_query_generation(query, context_chunks, system_prompt)
    response: GenerationResponse = await provider.generate(prepared.request)
    return build_query_response(
        answer=response.content,
        finish_reason=response.finish_reason,
        citations=prepared.citations,
        has_context=prepared.has_context,
    )
