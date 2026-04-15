"""Prompt guardrail routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext, get_auth_context
from app.guardrails.filter import evaluate_question
from app.models.guardrail import GuardrailCheckRequest, GuardrailCheckResponse

router = APIRouter(prefix="/api/v1/guardrails", tags=["guardrails"])


@router.post("/check", response_model=GuardrailCheckResponse)
async def check_prompt(
    payload: GuardrailCheckRequest,
    _: AuthContext = Depends(get_auth_context),
) -> GuardrailCheckResponse:
    return evaluate_question(payload.question, payload.top_k)
