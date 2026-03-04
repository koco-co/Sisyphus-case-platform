"""GLM (Zhipu AI) provider implementation."""

import json
from typing import AsyncIterator

import httpx

from app.llm.base import LLMProvider, LLMResponse, Message


class GLMProvider(LLMProvider):
    """GLM (Zhipu AI) provider implementation.

    Attributes:
        api_key: API key for authentication
        base_url: Base URL for the GLM API
        default_model: Default model to use for generations
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        default_model: str = "glm-4",
    ) -> None:
        """Initialize the GLM provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the GLM API endpoint
            default_model: Default model identifier to use
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.default_model = default_model

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
        """
        messages = [{"role": "user", "content": prompt}]

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix

                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if (
                                "choices" in chunk
                                and len(chunk["choices"]) > 0
                                and "delta" in chunk["choices"][0]
                            ):
                                delta = chunk["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue

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
        # Convert Message objects to dicts
        message_dicts = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
        return await self._make_request(message_dicts, model, temperature, max_tokens)

    async def _make_request(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Make a non-streaming request to the GLM API.

        Args:
            messages: List of message dictionaries
            model: The model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated text and metadata
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
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
