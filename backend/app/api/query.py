"""Query endpoint for grounded answers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AuthContext, get_auth_context
from app.audit.store import create_audit_event
from app.guardrails.filter import evaluate_question
from app.guardrails.rate_limit import enforce_rate_limit
from app.models.query import QueryRequest
from app.observability.metrics import record_query_decision
from app.retrieval.service import answer_question
from app.retrieval.generator import QueryResponse

router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> QueryResponse:
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
    create_audit_event(
        actor=auth_context.username,
        auth_method=auth_context.auth_method,
        action="query.executed",
        resource_type="query",
        outcome="success",
        details={
            "question": payload.question,
            "top_k": payload.top_k,
            "confidence": response.confidence,
            "sources": [citation.source for citation in response.citations],
        },
    )
    record_query_decision(outcome="success")
    return response
