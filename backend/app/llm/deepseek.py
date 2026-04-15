"""DeepSeek LLM provider implementation (OpenAI-compatible)."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Optional

import httpx

from app.config import get_settings
from app.llm.provider import (
    GenerationChunk,
    GenerationRequest,
    GenerationResponse,
    LLMProvider,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek provider using OpenAI-compatible API.

    Supports both cloud (api.deepseek.com) and self-hosted deployments.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize DeepSeek provider."""
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url or "https://api.deepseek.com/v1"
        self.model = model or settings.llm_model
        self.timeout = 30

        if not self.api_key:
            logger.warning("DeepSeek API key not configured. Health checks will fail.")

    async def health_check(self) -> bool:
        """
        Check DeepSeek provider connectivity.

        Makes a minimal request to verify the API is reachable.
        """
        if not self.api_key:
            logger.warning("Cannot health check: API key not configured")
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 10,
                        "temperature": 0.1,
                    },
                )
                return response.status_code == 200
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek health check failed: {e}")
            return False

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using DeepSeek.

        Converts the request to OpenAI-compatible format and calls the API.
        """
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=self._build_payload(request, stream=False),
                )

                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.status_code} {response.text}")
                    return GenerationResponse(
                        content="",
                        finish_reason="error",
                        model=request.model or self.model,
                    )

                data = response.json()
                choice = data.get("choices", [{}])[0]
                usage = data.get("usage", {})

                return GenerationResponse(
                    content=choice.get("message", {}).get("content", ""),
                    finish_reason=choice.get("finish_reason", "stop"),
                    model=request.model or self.model,
                    usage=self._normalize_usage(usage),
                )
        except httpx.TimeoutException:
            logger.error("DeepSeek request timeout")
            return GenerationResponse(
                content="",
                finish_reason="error",
                model=request.model or self.model,
            )
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek generation failed: {e}")
            return GenerationResponse(
                content="",
                finish_reason="error",
                model=request.model or self.model,
            )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[GenerationChunk]:
        """Generate streamed text using DeepSeek."""
        if not self.api_key:
            logger.error("DeepSeek streaming requested without an API key")
            yield GenerationChunk(finish_reason="error", model=request.model or self.model)
            return

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=self._build_payload(request, stream=True),
                ) as response:
                    if response.status_code != 200:
                        logger.error("DeepSeek streaming API error: %s %s", response.status_code, await response.aread())
                        yield GenerationChunk(
                            finish_reason="error",
                            model=request.model or self.model,
                        )
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue

                        payload = line.removeprefix("data:").strip()
                        if payload == "[DONE]":
                            break

                        data = json.loads(payload)
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {}).get("content", "")
                        finish_reason = choice.get("finish_reason")

                        if delta or finish_reason:
                            yield GenerationChunk(
                                content=delta,
                                finish_reason=finish_reason,
                                model=request.model or self.model,
                                usage=self._normalize_usage(data.get("usage", {})),
                            )
        except httpx.TimeoutException:
            logger.error("DeepSeek streaming request timeout")
            yield GenerationChunk(finish_reason="error", model=request.model or self.model)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.error("DeepSeek streaming failed: %s", exc)
            yield GenerationChunk(finish_reason="error", model=request.model or self.model)

    def _get_headers(self) -> dict:
        """Get request headers for DeepSeek API."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(self, request: GenerationRequest, *, stream: bool) -> dict:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        return {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

    def _normalize_usage(self, usage: dict) -> dict:
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        }
