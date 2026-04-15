"""LLM provider factory and registry."""

import logging
from typing import Optional
from app.llm.provider import LLMProvider
from app.llm.deepseek import DeepSeekProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global provider instance
_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Get the configured LLM provider (singleton)."""
    global _provider

    if _provider is None:
        provider_name = settings.llm_provider.lower()

        if provider_name == "deepseek":
            _provider = DeepSeekProvider()
            logger.info(f"Initialized DeepSeek provider: {settings.llm_model}")
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    return _provider


async def health_check() -> dict:
    """Check LLM provider health and readiness."""
    provider = get_provider()
    is_healthy = await provider.health_check()

    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "healthy": is_healthy,
        "status": "ready" if is_healthy else "unreachable",
    }
