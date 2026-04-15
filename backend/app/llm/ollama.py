"""Ollama LLM provider implementation."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.llm.provider import GenerationRequest, GenerationResponse, LLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class OllamaProvider(LLMProvider):
    """Ollama provider using the native local API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url or "http://localhost:11434").rstrip("/")
        self.model = model or settings.llm_model or "llama3.1"
        self.timeout = 60

    async def health_check(self) -> bool:
        """Check Ollama connectivity."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.error("Ollama health check failed: %s", exc)
            return False

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Ollama."""
        messages = [{"role": message.role, "content": message.content} for message in request.messages]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": request.model or self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": request.temperature,
                            "num_predict": request.max_tokens,
                        },
                    },
                )

                if response.status_code != 200:
                    logger.error("Ollama API error: %s %s", response.status_code, response.text)
                    return GenerationResponse(
                        content="",
                        finish_reason="error",
                        model=request.model or self.model,
                    )

                data = response.json()
                message = data.get("message", {})

                return GenerationResponse(
                    content=message.get("content", ""),
                    finish_reason=data.get("done_reason", "stop"),
                    model=request.model or self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                )
        except httpx.TimeoutException:
            logger.error("Ollama request timeout")
            return GenerationResponse(
                content="",
                finish_reason="error",
                model=request.model or self.model,
            )
        except httpx.HTTPError as exc:
            logger.error("Ollama generation failed: %s", exc)
            return GenerationResponse(
                content="",
                finish_reason="error",
                model=request.model or self.model,
            )
