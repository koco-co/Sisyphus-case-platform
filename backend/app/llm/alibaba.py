"""Alibaba (DashScope) provider implementation."""

import httpx
from typing import AsyncIterator, Optional

from app.llm.base import LLMProvider, LLMResponse, Message


class AlibabaProvider(LLMProvider):
    """Alibaba (DashScope) provider implementation.

    Attributes:
        api_key: API key for authentication
        base_url: Base URL for the DashScope API
        default_model: Default model to use for generations
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/api/v1",
        default_model: str = "qwen-max",
    ) -> None:
        """Initialize the Alibaba provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the DashScope API endpoint
            default_model: Default model identifier to use
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.default_model = default_model

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate text from a simple prompt.

        Args:
            prompt: The input prompt text
            model: The model identifier to use (uses default if not specified)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated text and metadata
        """
        if model is None:
            model = self.default_model

        messages = [{"role": "user", "content": prompt}]
        return await self._make_request(messages, model, temperature, max_tokens)

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Generate text from a prompt with streaming.

        Args:
            prompt: The input prompt text
            model: The model identifier to use (uses default if not specified)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Yields:
            str: Chunks of generated text as they arrive

        Raises:
            NotImplementedError: Streaming is not yet implemented
        """
        raise NotImplementedError("Streaming is not yet implemented for Alibaba provider")

    async def chat(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a chat completion from a list of messages.

        Args:
            messages: List of Message objects representing the conversation
            model: The model identifier to use (uses default if not specified)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the assistant's response and metadata
        """
        if model is None:
            model = self.default_model

        # Convert Message objects to dicts using model_dump()
        message_dicts = [msg.model_dump() for msg in messages]
        return await self._make_request(message_dicts, model, temperature, max_tokens)

    async def _make_request(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Make a non-streaming request to the DashScope API.

        Args:
            messages: List of message dictionaries
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated text and metadata
        """
        # Alibaba DashScope uses a special request format with input.messages
        # and parameters separated
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "input": {
                        "messages": messages
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            # Alibaba DashScope uses output.text for the response content
            return LLMResponse(
                text=data["output"]["text"],
                model=data.get("model", model),
                usage=data.get("usage"),
            )
