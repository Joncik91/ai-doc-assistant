"""LLM provider abstract contract."""

from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """A message in the chat."""

    role: str  # "system", "user", "assistant"
    content: str


class GenerationRequest(BaseModel):
    """Request for text generation."""

    messages: list[Message]
    model: str | None = None
    temperature: float = 0.5
    max_tokens: int = 2000

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "deepseek-chat",
                "temperature": 0.5,
                "max_tokens": 2000,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is this document about?"},
                ],
            }
        }
    )


class GenerationResponse(BaseModel):
    """Response from text generation."""

    content: str
    finish_reason: str  # "stop", "length", "error"
    model: str
    usage: dict = Field(default_factory=dict)  # {"prompt_tokens": 10, "completion_tokens": 20}

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "This document discusses...",
                "finish_reason": "stop",
                "model": "deepseek-chat",
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            }
        }
    )


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text based on the request."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider connectivity and health."""
        pass
