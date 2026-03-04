"""MiniMax provider implementation."""

from typing import AsyncIterator, Optional

import httpx

from app.llm.base import LLMProvider, LLMResponse, Message


class MiniMaxProvider(LLMProvider):
    """MiniMax provider implementation.

    Attributes:
        api_key: API key for authentication
        base_url: Base URL for the MiniMax API
        default_model: Default model to use for generations
        group_id: Optional group ID for MiniMax API
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.minimax.chat/v1",
        default_model: str = "abab6.5s-chat",
        group_id: Optional[str] = None,
    ) -> None:
        """Initialize the MiniMax provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the MiniMax API endpoint
            default_model: Default model identifier to use
            group_id: Optional group ID for MiniMax API (added to headers)
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.default_model = default_model
        self.group_id = group_id

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
        messages = [{"role": "user", "content": prompt}]
        return await self._make_request(messages, model, temperature, max_tokens)

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

        Raises:
            NotImplementedError: Streaming is not yet implemented for MiniMax
        """
        raise NotImplementedError("Streaming is not yet implemented for MiniMax")

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
        # Convert Message objects to dicts using msg.dict()
        message_dicts = [msg.dict() for msg in messages]
        return await self._make_request(message_dicts, model, temperature, max_tokens)

    async def _make_request(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Make a non-streaming request to the MiniMax API.

        Args:
            messages: List of message dictionaries
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated text and metadata
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Add GroupId header if group_id is provided
        if self.group_id:
            headers["GroupId"] = self.group_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=data.get("model", model),
                usage=data.get("usage"),
            )
