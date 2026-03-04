"""Tests for GLM (Zhipu AI) adapter."""

import os
import pytest

from app.llm.base import Message
from app.llm.glm import GLMProvider


class TestGLMProvider:
    """Test cases for GLMProvider."""

    def test_glm_provider_initialization(self):
        """Test GLMProvider initialization."""
        provider = GLMProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://open.bigmodel.cn/api/paas/v4"
        assert provider.default_model == "glm-4"

    def test_glm_provider_custom_base_url(self):
        """Test GLMProvider with custom base URL."""
        custom_url = "https://custom.api.example.com"
        provider = GLMProvider(api_key="test-key", base_url=custom_url)
        assert provider.api_key == "test-key"
        assert provider.base_url == custom_url
        assert provider.default_model == "glm-4"


@pytest.mark.skipif(
    not os.getenv("GLM_API_KEY"),
    reason="GLM_API_KEY environment variable not set"
)
class TestGLMProviderWithAPI:
    """Test cases for GLMProvider that require API access."""

    @pytest.fixture
    def provider(self):
        """Create a GLMProvider instance for testing."""
        api_key = os.getenv("GLM_API_KEY")
        return GLMProvider(api_key=api_key)

    @pytest.mark.asyncio
    async def test_glm_generate(self, provider):
        """Test basic text generation with GLM."""
        response = await provider.generate(
            prompt="What is the capital of France? Answer in one word.",
            model="glm-4",
            temperature=0.7,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "glm-4"
        assert response.usage is not None
        assert "prompt_tokens" in response.usage

    @pytest.mark.asyncio
    async def test_glm_generate_stream(self, provider):
        """Test streaming text generation with GLM."""
        chunks = []
        async for chunk in provider.generate_stream(
            prompt="Count from 1 to 5.",
            model="glm-4",
            temperature=0.7,
            max_tokens=100
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0

    @pytest.mark.asyncio
    async def test_glm_chat(self, provider):
        """Test multi-turn conversation with GLM."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content="2+2 equals 4."),
            Message(role="user", content="And what is 3+3?")
        ]

        response = await provider.chat(
            messages=messages,
            model="glm-4",
            temperature=0.7,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "glm-4"
        # Should contain the answer to 3+3
        assert "6" in response.text or "six" in response.text.lower()
