"""Test LLM provider contract."""

import pytest
from app.llm.provider import LLMProvider, GenerationRequest, GenerationResponse, Message
from app.llm.deepseek import DeepSeekProvider
from app.llm.factory import get_provider
from app.llm.ollama import OllamaProvider


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


def test_get_provider_supports_ollama(monkeypatch):
    """Test provider factory switches to Ollama."""
    from app.llm import factory as factory_module

    monkeypatch.setattr(factory_module, "_provider", None)
    monkeypatch.setattr(factory_module.settings, "llm_provider", "ollama")

    provider = factory_module.get_provider()

    assert isinstance(provider, OllamaProvider)


@pytest.mark.asyncio
async def test_ollama_provider_generate(monkeypatch):
    """Test Ollama request and response handling."""

    captured = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "message": {"content": "Hello from Ollama"},
                "done_reason": "stop",
                "prompt_eval_count": 12,
                "eval_count": 7,
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

        async def get(self, url):
            captured["health_url"] = url
            return FakeResponse()

    monkeypatch.setattr("app.llm.ollama.httpx.AsyncClient", FakeClient)

    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1")
    response = await provider.generate(
        GenerationRequest(
            messages=[Message(role="user", content="Hi")],
            temperature=0.2,
            max_tokens=42,
        )
    )

    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["json"]["stream"] is False
    assert captured["json"]["options"]["num_predict"] == 42
    assert response.content == "Hello from Ollama"
    assert response.finish_reason == "stop"
    assert response.usage["prompt_tokens"] == 12

    assert await provider.health_check() is True
    assert captured["health_url"] == "http://localhost:11434/api/tags"


@pytest.mark.asyncio
async def test_deepseek_health_check_no_api_key():
    """Test health check fails gracefully without API key."""
    provider = DeepSeekProvider(api_key=None)
    is_healthy = await provider.health_check()
    assert is_healthy is False
