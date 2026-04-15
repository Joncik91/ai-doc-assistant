"""Query endpoint for grounded answers."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import AuthContext, get_auth_context
from app.audit.store import create_audit_event
from app.guardrails.filter import evaluate_question
from app.guardrails.rate_limit import enforce_rate_limit
from app.llm.factory import get_provider
from app.models.query import QueryRequest
from app.observability.metrics import record_query_decision
from app.retrieval.generator import PreparedQueryGeneration, QueryResponse, build_query_response
from app.retrieval.service import answer_question, prepare_question_answer

router = APIRouter(prefix="/api/v1/query", tags=["query"])


def _audit_query_success(payload: QueryRequest, auth_context: AuthContext, response: QueryResponse) -> None:
    create_audit_event(
        actor=auth_context.username,
        auth_method=auth_context.auth_method,
        action="query.executed",
        resource_type="query",
        outcome="success",
        details={
            "question": payload.question,
            "top_k": payload.top_k,
            "answer": response.answer,
            "confidence": response.confidence,
            "finish_reason": response.finish_reason,
            "disclaimer": response.disclaimer,
            "citations": [citation.model_dump() for citation in response.citations],
            "sources": [citation.source for citation in response.citations],
        },
    )


def _evaluate_query_request(payload: QueryRequest, auth_context: AuthContext) -> None:
    enforce_rate_limit(auth_context.username, "query")
    assessment = evaluate_question(payload.question, payload.top_k)
    if not assessment.allowed:
        create_audit_event(
            actor=auth_context.username,
            auth_method=auth_context.auth_method,
            action="query.blocked",
            resource_type="query",
            outcome="blocked",
            details={
                "question": payload.question,
                "top_k": payload.top_k,
                "risk_level": assessment.risk_level,
                "blockers": assessment.blockers,
            },
        )
        record_query_decision(outcome="blocked")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=assessment.model_dump(),
        )


async def _run_query(payload: QueryRequest, auth_context: AuthContext) -> QueryResponse:
    _evaluate_query_request(payload, auth_context)

    response = await answer_question(payload.question, payload.top_k)
    _audit_query_success(payload, auth_context, response)
    record_query_decision(outcome="success")
    return response


async def _stream_query_response(
    payload: QueryRequest,
    auth_context: AuthContext,
    prepared: PreparedQueryGeneration,
):
    provider = get_provider()

    answer_parts: list[str] = []
    finish_reason = "stop"

    async for chunk in provider.generate_stream(prepared.request):
        if chunk.content:
            answer_parts.append(chunk.content)
            yield json.dumps({"type": "delta", "delta": chunk.content}, ensure_ascii=False).encode("utf-8") + b"\n"

        if chunk.finish_reason:
            finish_reason = chunk.finish_reason

    response = build_query_response(
        answer="".join(answer_parts),
        finish_reason=finish_reason,
        citations=prepared.citations,
        has_context=prepared.has_context,
    )
    _audit_query_success(payload, auth_context, response)
    record_query_decision(outcome="success")
    yield json.dumps({"type": "final", "response": response.model_dump()}, ensure_ascii=False).encode("utf-8") + b"\n"


@router.post("", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> QueryResponse:
    return await _run_query(payload, auth_context)


@router.post("/stream")
async def stream_query_documents(
    payload: QueryRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> StreamingResponse:
    _evaluate_query_request(payload, auth_context)
    prepared = prepare_question_answer(payload.question, payload.top_k)
    return StreamingResponse(
        _stream_query_response(payload, auth_context, prepared),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
