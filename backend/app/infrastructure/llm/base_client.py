"""
Base LLM client implementation.

Abstract base class defining the interface for all LLM clients.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator


class Message:
    """
    Represents a message in an LLM conversation.

    Attributes:
        role: The role of the message sender (system, user, assistant)
        content: The message content
    """

    def __init__(self, role: str, content: str):
        """
        Initialize a message.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
        """
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """
        Convert message to dictionary.

        Returns:
            Dict[str, str]: Dictionary with role and content
        """
        return {"role": self.role, "content": self.content}


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Defines the standard interface that all LLM client implementations
    must follow for compatibility with the Socrates AI platform.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize the LLM client.

        Args:
            api_key: API key for the LLM service
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            str: The assistant's response

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Chat completion not yet implemented")

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Send a chat completion request with streaming response.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Yields:
            str: Streaming chunks of the assistant's response

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Streaming chat not yet implemented")

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for the given texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Embedding generation not yet implemented")

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.

        Args:
            text: Text to tokenize

        Returns:
            int: Number of tokens

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Token counting not yet implemented")

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if the client supports streaming responses.

        Returns:
            bool: True if streaming is supported, False otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Streaming support check not yet implemented")

    @abstractmethod
    def supports_embeddings(self) -> bool:
        """
        Check if the client supports embeddings.

        Returns:
            bool: True if embeddings are supported, False otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Embeddings support check not yet implemented")

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict[str, Any]: Model information including name, capabilities, limits

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Model info not yet implemented")

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify the LLM service is accessible.

        Returns:
            bool: True if healthy, False otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Health check not yet implemented")

    def _validate_temperature(self, temperature: float) -> None:
        """
        Validate temperature parameter.

        Args:
            temperature: Temperature value to validate

        Raises:
            ValueError: If temperature is out of valid range
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {temperature}")

    def _prepare_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Prepare messages for API request.

        Args:
            messages: List of Message objects

        Returns:
            List[Dict[str, str]]: List of message dictionaries
        """
        return [msg.to_dict() for msg in messages]