"""Module 6: RAG Knowledge Base System.

This module provides retrieval-augmented generation (RAG) capabilities
for the Socrates tutoring system, enabling semantic search across
a knowledge base of mathematical concepts, methods, and examples.
"""

from .service import RAGService
from .models import (
    KGDocument,
    KGChunk,
    KGQuery,
    KGResult,
    DocumentType,
    KGError,
    ChromaDBConnectionError,
    EmbeddingServiceError,
    RetrievalTimeoutError,
    DocumentNotFoundError,
    ValidationError,
)

__all__ = [
    # Main service
    "RAGService",
    # Models
    "KGDocument",
    "KGChunk",
    "KGQuery",
    "KGResult",
    "DocumentType",
    # Exceptions
    "KGError",
    "ChromaDBConnectionError",
    "EmbeddingServiceError",
    "RetrievalTimeoutError",
    "DocumentNotFoundError",
    "ValidationError",
]

__version__ = "1.0.0"
