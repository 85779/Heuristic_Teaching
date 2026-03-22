"""LLM Client interface - Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import ModuleContext


class ILLMClient(ABC):
    """LLM Client base interface.

    Abstracts interaction with LLM providers (OpenAI, Anthropic, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider.

        Returns:
            str: Provider name (e.g., "openai", "anthropic")
        """
        raise NotImplementedError

    @abstractmethod
    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the LLM client.

        Called during application startup to validate configuration
        and set up the client.

        Args:
            context: Module execution context
        """
        raise NotImplementedError

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: Input prompt text
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Generated completion text
        """
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            dict[str, Any]: Response containing generated message and metadata
        """
        raise NotImplementedError

    @abstractmethod
    async def stream_complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:  # Async generator
        """Stream completions for the given prompt.

        Args:
            prompt: Input prompt text
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Async generator yielding completion chunks
        """
        raise NotImplementedError

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the client configuration.

        Returns:
            bool: True if configuration is valid
        """
        raise NotImplementedError