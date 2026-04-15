"""Ollama LLM provider implementation."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Optional

import httpx

from app.config import get_settings
from app.llm.provider import GenerationChunk, GenerationRequest, GenerationResponse, LLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    """Ollama provider using the native local API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        configured_base_url = base_url or settings.llm_base_url
        if not configured_base_url or configured_base_url == DEEPSEEK_DEFAULT_BASE_URL:
            configured_base_url = OLLAMA_DEFAULT_BASE_URL

        self.base_url = configured_base_url.rstrip("/")
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
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=self._build_payload(request, stream=False),
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
                    usage=self._normalize_usage(data),
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

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[GenerationChunk]:
        """Generate streamed text using Ollama."""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=self._build_payload(request, stream=True),
                ) as response:
                    if response.status_code != 200:
                        logger.error("Ollama streaming API error: %s %s", response.status_code, await response.aread())
                        yield GenerationChunk(
                            finish_reason="error",
                            model=request.model or self.model,
                        )
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        data = json.loads(line)
                        message = data.get("message", {})
                        delta = message.get("content", "")
                        done = bool(data.get("done", False))
                        finish_reason = data.get("done_reason", "stop") if done else None

                        if delta or finish_reason:
                            yield GenerationChunk(
                                content=delta,
                                finish_reason=finish_reason,
                                model=request.model or self.model,
                                usage=self._normalize_usage(data),
                            )
        except httpx.TimeoutException:
            logger.error("Ollama streaming request timeout")
            yield GenerationChunk(finish_reason="error", model=request.model or self.model)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.error("Ollama streaming failed: %s", exc)
            yield GenerationChunk(finish_reason="error", model=request.model or self.model)

    def _build_payload(self, request: GenerationRequest, *, stream: bool) -> dict:
        messages = [{"role": message.role, "content": message.content} for message in request.messages]
        return {
            "model": request.model or self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

    def _normalize_usage(self, data: dict) -> dict:
        return {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
