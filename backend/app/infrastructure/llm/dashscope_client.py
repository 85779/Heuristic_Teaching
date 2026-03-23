"""
DashScope (阿里云百炼) LLM client implementation.

Provides integration with Alibaba Cloud's DashScope models including
Qwen-Turbo, Qwen-Max, and other models via the OpenAI-compatible API.
"""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI
from .base_client import BaseLLMClient, Message


class DashScopeClient(BaseLLMClient):
    """
    DashScope LLM client implementation.

    Supports Qwen-Turbo, Qwen-Max, and other DashScope models
    with both regular and streaming responses via OpenAI-compatible API.
    """

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-turbo",
        base_url: Optional[str] = None,
        timeout: float = 120.0
    ):
        """
        Initialize the DashScope client.

        Args:
            api_key: Alibaba Cloud API key
            model: Model identifier (default: qwen-turbo)
            base_url: Optional custom base URL
            timeout: Request timeout in seconds (default: 120.0)
        """
        super().__init__(api_key, model)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """
        Get or create the async OpenAI client.

        Returns:
            AsyncOpenAI: The OpenAI-compatible client instance
        """
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=3
            )
        return self._client

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        seed: Optional[int] = None,
        stop: Optional[List[str]] = None,
        response_format: Optional[Dict[str, str]] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = False,
        repetition_penalty: Optional[float] = None,
        result_format: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Send a chat completion request to DashScope.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling probability threshold
            top_k: Size of sampling candidate set
            seed: Random seed for reproducibility
            stop: Stop sequences
            response_format: Format constraint (e.g., {"type": "json_object"})
            tools: List of tool definitions for function calling
            tool_choice: Tool choice mode ("auto", "none", or specific tool)
            enable_search: Enable web search
            enable_thinking: Enable thinking mode
            repetition_penalty: Repetition penalty (1.0 to 4.0)
            result_format: Result format ("message" or "text")
            **kwargs: Additional parameters

        Returns:
            str: The assistant's response

        Raises:
            Exception: If the API request fails
        """
        self._validate_temperature(temperature)

        message_dicts = [msg.to_dict() for msg in messages]

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": message_dicts,
            "temperature": temperature,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if top_k is not None:
            request_kwargs["top_k"] = top_k
        if seed is not None:
            request_kwargs["seed"] = seed
        if stop is not None:
            request_kwargs["stop"] = stop
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        if tools is not None:
            request_kwargs["tools"] = tools
        if tool_choice is not None:
            request_kwargs["tool_choice"] = tool_choice
        if enable_search:
            request_kwargs["enable_search"] = enable_search
        if enable_thinking:
            # enable_thinking must be in extra_body for DashScope compatibility
            extra_body = request_kwargs.get("extra_body", {})
            extra_body["enable_thinking"] = True
            request_kwargs["extra_body"] = extra_body
        if repetition_penalty is not None:
            request_kwargs["repetition_penalty"] = repetition_penalty
        if result_format is not None:
            request_kwargs["result_format"] = result_format

        request_kwargs.update(kwargs)

        try:
            response = await self.client.chat.completions.create(**request_kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"DashScope chat completion failed: {str(e)}") from e

    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        seed: Optional[int] = None,
        stop: Optional[List[str]] = None,
        response_format: Optional[Dict[str, str]] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = False,
        repetition_penalty: Optional[float] = None,
        result_format: Optional[str] = None,
        incremental_output: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Send a streaming chat completion request to DashScope.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling probability threshold
            top_k: Size of sampling candidate set
            seed: Random seed for reproducibility
            stop: Stop sequences
            response_format: Format constraint (e.g., {"type": "json_object"})
            tools: List of tool definitions for function calling
            tool_choice: Tool choice mode ("auto", "none", or specific tool)
            enable_search: Enable web search
            enable_thinking: Enable thinking mode
            repetition_penalty: Repetition penalty (1.0 to 4.0)
            result_format: Result format ("message" or "text")
            incremental_output: Enable incremental output (default: True)
            **kwargs: Additional parameters

        Yields:
            str: Streaming chunks of the assistant's response

        Raises:
            Exception: If the API request fails
        """
        self._validate_temperature(temperature)

        message_dicts = [msg.to_dict() for msg in messages]

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": message_dicts,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if top_k is not None:
            request_kwargs["top_k"] = top_k
        if seed is not None:
            request_kwargs["seed"] = seed
        if stop is not None:
            request_kwargs["stop"] = stop
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        if tools is not None:
            request_kwargs["tools"] = tools
        if tool_choice is not None:
            request_kwargs["tool_choice"] = tool_choice
        if enable_search:
            request_kwargs["enable_search"] = enable_search
        if enable_thinking:
            request_kwargs["enable_thinking"] = enable_thinking
        if repetition_penalty is not None:
            request_kwargs["repetition_penalty"] = repetition_penalty
        if result_format is not None:
            request_kwargs["result_format"] = result_format
        if incremental_output:
            request_kwargs["incremental_output"] = incremental_output

        request_kwargs.update(kwargs)

        try:
            stream = await self.client.chat.completions.create(**request_kwargs)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"DashScope streaming chat failed: {str(e)}") from e

    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """
        Get embeddings using DashScope's embedding model.

        Args:
            texts: List of text strings to embed
            model: Embedding model identifier (default: text-embedding-v3)

        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            Exception: If the API request fails
        """
        embedding_model = model or "text-embedding-v3"

        try:
            response = await self.client.embeddings.create(
                model=embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise Exception(f"DashScope embedding generation failed: {str(e)}") from e

    async def count_tokens(self, text: str) -> int:
        """
        Estimate token count for the given text.

        Note: DashScope doesn't provide a direct token counting API.
        This is an approximation using character-based estimation.

        Args:
            text: Text to estimate tokens for

        Returns:
            int: Estimated number of tokens
        """
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25)

    def supports_streaming(self) -> bool:
        """
        Check if DashScope client supports streaming.

        Returns:
            bool: Always True for DashScope
        """
        return True

    def supports_embeddings(self) -> bool:
        """
        Check if DashScope client supports embeddings.

        Returns:
            bool: Always True for DashScope
        """
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the DashScope model.

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "provider": "dashscope",
            "model": self.model,
            "supports_streaming": True,
            "supports_embeddings": True,
            "base_url": self.base_url,
            "context_window": self._get_context_window(),
            "description": self._get_model_description()
        }

    def _get_context_window(self) -> int:
        """
        Get the context window size for the current model.

        Returns:
            int: Context window size in tokens
        """
        context_windows = {
            "qwen-turbo": 128000,
            "qwen-plus": 131072,
            "qwen-max": 8192,
            "qwen-max-longcontext": 30720,
            "qwen2-7b-instruct": 32768,
            "qwen2-57b-a14b-instruct": 131072,
            "qwen3.5-plus": 131072,
        }
        return context_windows.get(self.model, 8192)

    def _get_model_description(self) -> str:
        """
        Get the description for the current model.

        Returns:
            str: Model description
        """
        descriptions = {
            "qwen-turbo": "Qwen Turbo - Fast response, good for routine tasks",
            "qwen-plus": "Qwen Plus - Balanced performance and speed",
            "qwen-max": "Qwen Max - Best quality, slower response",
            "qwen-max-longcontext": "Qwen Max Long Context - Extended context support",
            "qwen3.5-plus": "Qwen 3.5 Plus - Enhanced reasoning and instruction following",
        }
        return descriptions.get(self.model, f"DashScope model: {self.model}")

    async def health_check(self) -> bool:
        """
        Verify the DashScope service is accessible.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            await self.chat(
                messages=[Message(role="user", content="Hi")],
                max_tokens=10
            )
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """
        Close the client and release resources.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None