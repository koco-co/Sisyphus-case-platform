"""Tests for LLM factory."""

import pytest

from app.llm.factory import create_llm_provider


def test_create_glm_provider() -> None:
    """Test creating GLM provider."""
    provider = create_llm_provider("glm", api_key="test-key")
    assert provider.__class__.__name__ == "GLMProvider"
    assert provider.api_key == "test-key"


def test_create_minimax_provider() -> None:
    """Test creating MiniMax provider."""
    provider = create_llm_provider("minimax", api_key="test-key")
    assert provider.__class__.__name__ == "MiniMaxProvider"
    assert provider.api_key == "test-key"


def test_create_minimax_provider_with_group_id() -> None:
    """Test creating MiniMax provider with group_id parameter."""
    provider = create_llm_provider(
        "minimax", api_key="test-key", group_id="test-group"
    )
    assert provider.__class__.__name__ == "MiniMaxProvider"
    assert provider.api_key == "test-key"
    assert provider.group_id == "test-group"


def test_create_alibaba_provider() -> None:
    """Test creating Alibaba provider."""
    provider = create_llm_provider("alibaba", api_key="test-key")
    assert provider.__class__.__name__ == "AlibabaProvider"
    assert provider.api_key == "test-key"


def test_invalid_provider() -> None:
    """Test creating provider with invalid name."""
    with pytest.raises(ValueError, match="不支持的 LLM 提供商"):
        create_llm_provider("invalid", api_key="test-key")


def test_case_insensitive_provider_name() -> None:
    """Test that provider names are case-insensitive."""
    provider_glm = create_llm_provider("GLM", api_key="test-key")
    assert provider_glm.__class__.__name__ == "GLMProvider"

    provider_minimax = create_llm_provider("MiniMax", api_key="test-key")
    assert provider_minimax.__class__.__name__ == "MiniMaxProvider"

    provider_alibaba = create_llm_provider("ALIBABA", api_key="test-key")
    assert provider_alibaba.__class__.__name__ == "AlibabaProvider"
