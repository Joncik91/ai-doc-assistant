"""Query endpoint for grounded answers."""

from __future__ import annotations

import json
import math

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import AuthContext, get_auth_context
from app.audit.store import create_audit_event
from app.guardrails.filter import evaluate_question
from app.guardrails.rate_limit import enforce_rate_limit
from app.models.query import QueryRequest
from app.observability.metrics import record_query_decision
from app.retrieval.service import answer_question
from app.retrieval.generator import QueryResponse

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


async def _run_query(payload: QueryRequest, auth_context: AuthContext) -> QueryResponse:
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

    response = await answer_question(payload.question, payload.top_k)
    _audit_query_success(payload, auth_context, response)
    record_query_decision(outcome="success")
    return response


async def _stream_query_response(response: QueryResponse):
    answer = response.answer or ""
    chunk_size = max(1, math.ceil(len(answer) / 8)) if answer else 0

    if not answer:
        yield json.dumps({"type": "delta", "delta": ""}, ensure_ascii=False).encode("utf-8") + b"\n"
    else:
        for start in range(0, len(answer), chunk_size):
            chunk = answer[start : start + chunk_size]
            yield json.dumps({"type": "delta", "delta": chunk}, ensure_ascii=False).encode("utf-8") + b"\n"

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
    response = await _run_query(payload, auth_context)
    return StreamingResponse(
        _stream_query_response(response),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
