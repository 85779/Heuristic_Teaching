"""Module 6: RAG Knowledge Base System.

This module provides retrieval-augmented generation (RAG) capabilities
for the Socrates tutoring system.

Includes both:
- ChromaDB-based RAG (requires chromadb)
- Lightweight embedding-based retriever (no external DB, uses DashScope embeddings)
"""

# ChromaDB-based RAG (optional — requires chromadb)
try:
    from .service import RAGService
except ImportError:
    RAGService = None

# Lightweight retriever (always available)
try:
    from .lightweight_retriever import LightweightRetriever, KnowledgeChunk
except ImportError:
    LightweightRetriever = None
    KnowledgeChunk = None

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
    "RAGService",
    "LightweightRetriever",
    "KnowledgeChunk",
    "KGDocument",
    "KGChunk",
    "KGQuery",
    "KGResult",
    "DocumentType",
    "KGError",
    "ChromaDBConnectionError",
    "EmbeddingServiceError",
    "RetrievalTimeoutError",
    "DocumentNotFoundError",
    "ValidationError",
]

__version__ = "1.0.0"
