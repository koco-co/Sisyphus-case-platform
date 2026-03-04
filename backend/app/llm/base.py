"""LLM base classes and unified interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """Message model for LLM chat completions.

    Attributes:
        role: The role of the message sender (system, user, or assistant)
        content: The content of the message
    """

    role: str
    content: str


class LLMResponse(BaseModel):
    """Response model for LLM generations.

    Attributes:
        text: The generated text content
        model: The model identifier used for generation
        usage: Optional token usage information
    """

    text: str
    model: str
    usage: Optional[dict] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    This class defines the unified interface that all LLM providers must implement.
    It supports both simple prompt generation and chat-based interactions.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None) -> None:
        """Initialize the LLM provider.

        Args:
            api_key: API key for authentication
            base_url: Optional base URL for the API endpoint
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate text from a simple prompt.

        Args:
            prompt: The input prompt text
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated text and metadata
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Generate text from a prompt with streaming.

        Args:
            prompt: The input prompt text
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Yields:
            str: Chunks of generated text as they arrive
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a chat completion from a list of messages.

        Args:
            messages: List of Message objects representing the conversation
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the assistant's response and metadata
        """
        pass
