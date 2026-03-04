"""LLM provider factory for creating provider instances."""

from app.llm.alibaba import AlibabaProvider
from app.llm.base import LLMProvider
from app.llm.glm import GLMProvider
from app.llm.minimax import MiniMaxProvider

# Mapping of provider names to their implementation classes
PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "glm": GLMProvider,
    "minimax": MiniMaxProvider,
    "alibaba": AlibabaProvider,
}


def create_llm_provider(
    provider_name: str,
    api_key: str,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider instance.

    This factory function creates provider instances based on the provider name.
    It supports passing additional keyword arguments that are specific to certain
    providers (e.g., group_id for MiniMax).

    Args:
        provider_name: The name of the provider (glm, minimax, alibaba)
        api_key: API key for authentication
        **kwargs: Additional provider-specific parameters:
            - group_id: Optional group ID for MiniMax API
            - base_url: Optional custom base URL
            - default_model: Optional default model identifier

    Returns:
        An instance of the specified LLM provider

    Raises:
        ValueError: If the provider name is not supported

    Examples:
        Create a GLM provider:
        >>> provider = create_llm_provider("glm", api_key="your-key")

        Create a MiniMax provider with group_id:
        >>> provider = create_llm_provider(
        ...     "minimax",
        ...     api_key="your-key",
        ...     group_id="your-group-id"
        ... )

        Create an Alibaba provider with custom model:
        >>> provider = create_llm_provider(
        ...     "alibaba",
        ...     api_key="your-key",
        ...     default_model="qwen-turbo"
        ... )
    """
    provider_class = PROVIDER_MAP.get(provider_name.lower())

    if not provider_class:
        supported_providers = ", ".join(PROVIDER_MAP.keys())
        raise ValueError(
            f"不支持的 LLM 提供商: {provider_name}. "
            f"支持的提供商: {supported_providers}"
        )

    return provider_class(api_key=api_key, **kwargs)
