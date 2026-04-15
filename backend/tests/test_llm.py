"""Test LLM provider contract."""

import pytest
from app.llm.provider import LLMProvider, GenerationRequest, GenerationResponse, Message
from app.llm.deepseek import DeepSeekProvider
from app.llm.factory import get_provider


def test_provider_interface():
    """Test that DeepSeekProvider implements LLMProvider."""
    provider = DeepSeekProvider(api_key="test-key")
    assert isinstance(provider, LLMProvider)


@pytest.mark.asyncio
async def test_generation_request_creation():
    """Test creating a generation request."""
    request = GenerationRequest(
        messages=[
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello"),
        ],
        model="test-model",
        temperature=0.5,
        max_tokens=100,
    )

    assert request.model == "test-model"
    assert len(request.messages) == 2
    assert request.temperature == 0.5


def test_generation_response_structure():
    """Test generation response structure."""
    response = GenerationResponse(
        content="Test response",
        finish_reason="stop",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
    )

    assert response.content == "Test response"
    assert response.finish_reason == "stop"
    assert response.usage["prompt_tokens"] == 10


def test_get_provider():
    """Test provider factory."""
    provider = get_provider()
    assert isinstance(provider, LLMProvider)
    # Verify singleton
    provider2 = get_provider()
    assert provider is provider2


@pytest.mark.asyncio
async def test_deepseek_health_check_no_api_key():
    """Test health check fails gracefully without API key."""
    provider = DeepSeekProvider(api_key=None)
    is_healthy = await provider.health_check()
    assert is_healthy is False
