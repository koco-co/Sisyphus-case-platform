"""Tests for Alibaba (DashScope) adapter."""

import os
import pytest

from app.llm.alibaba import AlibabaProvider
from app.llm.base import Message


class TestAlibabaProvider:
    """Test cases for AlibabaProvider."""

    def test_alibaba_provider_initialization(self):
        """Test AlibabaProvider initialization."""
        provider = AlibabaProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://dashscope.aliyuncs.com/api/v1"
        assert provider.default_model == "qwen-max"

    def test_alibaba_provider_custom_base_url(self):
        """Test AlibabaProvider with custom base URL."""
        custom_url = "https://custom.api.example.com"
        provider = AlibabaProvider(api_key="test-key", base_url=custom_url)
        assert provider.api_key == "test-key"
        assert provider.base_url == custom_url
        assert provider.default_model == "qwen-max"


@pytest.mark.skipif(
    not os.getenv("ALIBABA_API_KEY"),
    reason="ALIBABA_API_KEY environment variable not set"
)
class TestAlibabaProviderWithAPI:
    """Test cases for AlibabaProvider that require API access."""

    @pytest.fixture
    def provider(self):
        """Create an AlibabaProvider instance for testing."""
        api_key = os.getenv("ALIBABA_API_KEY")
        return AlibabaProvider(api_key=api_key)

    @pytest.mark.asyncio
    async def test_alibaba_generate(self, provider):
        """Test basic text generation with Alibaba."""
        response = await provider.generate(
            prompt="What is 2+2? Answer with just the number.",
            model="qwen-max",
            temperature=0.1,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "qwen-max"
        # Should contain the answer "4" somewhere
        assert "4" in response.text

    @pytest.mark.asyncio
    async def test_alibaba_chat(self, provider):
        """Test multi-turn conversation with Alibaba."""
        messages = [
            Message(role="user", content="My name is Alice."),
            Message(role="assistant", content="Hello Alice! Nice to meet you."),
            Message(role="user", content="What's my name?"),
        ]

        response = await provider.chat(
            messages=messages,
            model="qwen-max",
            temperature=0.1,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "qwen-max"
        # Should remember the name
        assert "Alice" in response.text

    @pytest.mark.asyncio
    async def test_alibaba_custom_model(self, provider):
        """Test using custom model."""
        response = await provider.generate(
            prompt="What is 1+1?",
            model="qwen-plus",
            temperature=0.1,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "qwen-plus"
