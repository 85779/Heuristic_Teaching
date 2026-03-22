"""
Infrastructure layer for Socrates AI platform.

This module provides the foundational infrastructure components including:
- Database connectivity (MongoDB)
- LLM client implementations (OpenAI, Anthropic)
- Caching layer (Redis)
- Logging and tracing utilities
"""

from .database import MongoDBConnection
from .llm import BaseLLMClient
from .cache import RedisCache
from .logging import Tracer

__all__ = [
    "MongoDBConnection",
    "BaseLLMClient",
    "RedisCache",
    "Tracer",
]