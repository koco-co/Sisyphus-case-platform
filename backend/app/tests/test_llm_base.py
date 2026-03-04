"""Tests for LLM base classes and models."""

import pytest
from pydantic import ValidationError

from app.llm.base import LLMProvider, LLMResponse, Message


class TestMessageModel:
    """Test cases for Message model."""

    def test_message_model_with_valid_data(self):
        """Test creating a Message with valid data."""
        message = Message(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_message_model_with_system_role(self):
        """Test creating a Message with system role."""
        message = Message(role="system", content="You are a helpful assistant.")
        assert message.role == "system"
        assert message.content == "You are a helpful assistant."

    def test_message_model_with_assistant_role(self):
        """Test creating a Message with assistant role."""
        message = Message(role="assistant", content="How can I help you?")
        assert message.role == "assistant"
        assert message.content == "How can I help you?"

    def test_message_model_validation_missing_role(self):
        """Test that Message requires role field."""
        with pytest.raises(ValidationError):
            Message(content="Hello")

    def test_message_model_validation_missing_content(self):
        """Test that Message requires content field."""
        with pytest.raises(ValidationError):
            Message(role="user")

    def test_message_model_serialization(self):
        """Test Message model serialization to dict."""
        message = Message(role="user", content="Test message")
        data = message.model_dump()
        assert data == {"role": "user", "content": "Test message"}

    def test_message_model_from_dict(self):
        """Test creating Message from dictionary."""
        data = {"role": "user", "content": "Test message"}
        message = Message(**data)
        assert message.role == "user"
        assert message.content == "Test message"


class TestLLMResponseModel:
    """Test cases for LLMResponse model."""

    def test_llm_response_with_all_fields(self):
        """Test creating LLMResponse with all fields."""
        response = LLMResponse(
            text="Generated text",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        assert response.text == "Generated text"
        assert response.model == "gpt-4"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}

    def test_llm_response_without_usage(self):
        """Test creating LLMResponse without usage field."""
        response = LLMResponse(text="Generated text", model="gpt-4")
        assert response.text == "Generated text"
        assert response.model == "gpt-4"
        assert response.usage is None

    def test_llm_response_validation_missing_text(self):
        """Test that LLMResponse requires text field."""
        with pytest.raises(ValidationError):
            LLMResponse(model="gpt-4")

    def test_llm_response_validation_missing_model(self):
        """Test that LLMResponse requires model field."""
        with pytest.raises(ValidationError):
            LLMResponse(text="Generated text")

    def test_llm_response_serialization(self):
        """Test LLMResponse model serialization to dict."""
        response = LLMResponse(
            text="Generated text",
            model="gpt-4",
            usage={"prompt_tokens": 10}
        )
        data = response.model_dump()
        assert data == {
            "text": "Generated text",
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10}
        }

    def test_llm_response_from_dict(self):
        """Test creating LLMResponse from dictionary."""
        data = {"text": "Generated text", "model": "gpt-4"}
        response = LLMResponse(**data)
        assert response.text == "Generated text"
        assert response.model == "gpt-4"
        assert response.usage is None


class TestLLMProvider:
    """Test cases for LLMProvider abstract base class."""

    def test_llm_provider_is_abstract(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider(api_key="test-key")

    def test_llm_provider_init_with_base_url(self):
        """Test LLMProvider initialization with base_url."""
        # Create a concrete implementation for testing
        class ConcreteProvider(LLMProvider):
            async def generate(self, prompt, model, temperature=0.7, max_tokens=1000):
                return LLMResponse(text="test", model=model)

            async def generate_stream(self, prompt, model, temperature=0.7, max_tokens=1000):
                yield "test"

            async def chat(self, messages, model, temperature=0.7, max_tokens=1000):
                return LLMResponse(text="test", model=model)

        provider = ConcreteProvider(api_key="test-key", base_url="https://api.example.com")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.example.com"

    def test_llm_provider_init_without_base_url(self):
        """Test LLMProvider initialization without base_url."""
        # Create a concrete implementation for testing
        class ConcreteProvider(LLMProvider):
            async def generate(self, prompt, model, temperature=0.7, max_tokens=1000):
                return LLMResponse(text="test", model=model)

            async def generate_stream(self, prompt, model, temperature=0.7, max_tokens=1000):
                yield "test"

            async def chat(self, messages, model, temperature=0.7, max_tokens=1000):
                return LLMResponse(text="test", model=model)

        provider = ConcreteProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url is None
