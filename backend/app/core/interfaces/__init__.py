"""Core interfaces for the modular architecture."""

from .module import IModule
from .pipeline import IPipeline
from .repository import IRepository
from .llm_client import ILLMClient

__all__ = ["IModule", "IPipeline", "IRepository", "ILLMClient"]