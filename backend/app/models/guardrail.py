"""Prompt guardrail models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GuardrailCheckRequest(BaseModel):
    """Prompt evaluation request."""

    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What does the policy say about remote work?",
                "top_k": 4,
            }
        }
    )


class GuardrailCheckResponse(BaseModel):
    """Prompt evaluation response."""

    allowed: bool
    risk_level: str
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_action: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "allowed": True,
                "risk_level": "low",
                "warnings": [
                    "This question is broad; consider naming a specific document."
                ],
                "blockers": [],
                "recommended_action": "proceed",
            }
        }
    )
