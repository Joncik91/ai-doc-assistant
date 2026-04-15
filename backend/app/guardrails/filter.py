"""Prompt safety heuristics for the operator UI."""

from __future__ import annotations

from app.models.guardrail import GuardrailCheckResponse

BLOCK_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "reveal your prompt",
    "api key",
    "password",
    "secret",
    "token",
    "bypass",
    "jailbreak",
)

WARN_PATTERNS = (
    "all documents",
    "every document",
    "download data",
    "export data",
    "summarize everything",
)


def evaluate_question(question: str, top_k: int = 4) -> GuardrailCheckResponse:
    """Evaluate a question before it reaches retrieval and generation."""
    normalized = " ".join(question.lower().split())
    blockers: list[str] = []
    warnings: list[str] = []

    if any(pattern in normalized for pattern in BLOCK_PATTERNS):
        blockers.append("This request appears to ask for secrets, prompts, or bypass instructions.")
    if any(pattern in normalized for pattern in WARN_PATTERNS):
        warnings.append(
            "This request is broad; narrow it to a specific document or topic for better retrieval."
        )

    if len(normalized) < 12:
        warnings.append("The prompt is very short; add more context for better results.")
    if top_k > 6:
        warnings.append("High top_k values may reduce precision.")

    allowed = not blockers
    if blockers:
        risk_level = "high"
        recommended_action = "block"
    elif warnings:
        risk_level = "medium"
        recommended_action = "warn"
    else:
        risk_level = "low"
        recommended_action = "proceed"

    return GuardrailCheckResponse(
        allowed=allowed,
        risk_level=risk_level,
        warnings=warnings,
        blockers=blockers,
        recommended_action=recommended_action,
    )
