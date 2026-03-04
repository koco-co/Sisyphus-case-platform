"""Tests for MiniMax adapter."""

import os
import pytest

from app.llm.base import Message
from app.llm.minimax import MiniMaxProvider


class TestMiniMaxProvider:
    """Test cases for MiniMaxProvider."""

    def test_minimax_provider_initialization(self):
        """Test MiniMaxProvider initialization."""
        provider = MiniMaxProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.minimax.chat/v1"
        assert provider.default_model == "abab6.5s-chat"

    def test_minimax_provider_custom_base_url(self):
        """Test MiniMaxProvider with custom base URL."""
        custom_url = "https://custom.api.example.com"
        provider = MiniMaxProvider(api_key="test-key", base_url=custom_url)
        assert provider.api_key == "test-key"
        assert provider.base_url == custom_url
        assert provider.default_model == "abab6.5s-chat"

    def test_minimax_provider_with_group_id(self):
        """Test MiniMaxProvider with group_id."""
        provider = MiniMaxProvider(api_key="test-key", group_id="test-group-123")
        assert provider.api_key == "test-key"
        assert provider.group_id == "test-group-123"
        assert provider.base_url == "https://api.minimax.chat/v1"


@pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY environment variable not set"
)
class TestMiniMaxProviderWithAPI:
    """Test cases for MiniMaxProvider that require API access."""

    @pytest.fixture
    def provider(self):
        """Create a MiniMaxProvider instance for testing."""
        api_key = os.getenv("MINIMAX_API_KEY")
        group_id = os.getenv("MINIMAX_GROUP_ID")
        return MiniMaxProvider(api_key=api_key, group_id=group_id)

    @pytest.mark.asyncio
    async def test_minimax_generate(self, provider):
        """Test basic text generation with MiniMax."""
        response = await provider.generate(
            prompt="What is the capital of France? Answer in one word.",
            model="abab6.5s-chat",
            temperature=0.7,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "abab6.5s-chat"
        assert response.usage is not None
        assert "prompt_tokens" in response.usage

    @pytest.mark.asyncio
    async def test_minimax_chat(self, provider):
        """Test multi-turn conversation with MiniMax."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content="2+2 equals 4."),
            Message(role="user", content="And what is 3+3?")
        ]

        response = await provider.chat(
            messages=messages,
            model="abab6.5s-chat",
            temperature=0.7,
            max_tokens=100
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert response.model == "abab6.5s-chat"
        # Should contain the answer to 3+3
        assert "6" in response.text or "six" in response.text.lower()
