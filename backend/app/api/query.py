"""Query endpoint for grounded answers."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext, get_auth_context
from app.models.query import QueryRequest
from app.retrieval.service import answer_question
from app.retrieval.generator import QueryResponse

router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    _: AuthContext = Depends(get_auth_context),
) -> QueryResponse:
    return await answer_question(payload.question, payload.top_k)

