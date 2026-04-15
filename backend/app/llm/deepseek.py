"""DeepSeek LLM provider implementation (OpenAI-compatible)."""

import logging
from typing import Optional

import httpx

from app.llm.provider import LLMProvider, GenerationRequest, GenerationResponse
from app.config import get_settings

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

        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": request.model or self.model,
                        "messages": messages,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                    },
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
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                    },
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

    def _get_headers(self) -> dict:
        """Get request headers for DeepSeek API."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
