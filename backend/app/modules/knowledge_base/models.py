"""Data models for the RAG Knowledge Base module.

Defines the core data structures used across the knowledge base system.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class DocumentType(str, Enum):
    """Document type enumeration for knowledge base documents.
    
    Represents the five types of knowledge documents in the system:
    - KNOWLEDGE_POINT: Core mathematical knowledge points
    - METHOD: Problem-solving methods and techniques
    - CONCEPT: Basic mathematical concepts
    - EXAMPLE: Typical examples with solutions
    - STRATEGY: Teaching strategies
    """
    KNOWLEDGE_POINT = "knowledge_point"  # 知识点
    METHOD = "method"                      # 解题方法
    CONCEPT = "concept"                   # 数学概念
    EXAMPLE = "example"                    # 典型例题
    STRATEGY = "strategy"                 # 教学策略


@dataclass
class KGDocument:
    """Knowledge base document model.
    
    Represents a document stored in the knowledge base with its content
    and associated metadata.
    
    Attributes:
        id: Unique document identifier
        content: Raw text content of the document
        metadata: Dictionary containing type, name, keywords, grade,
                 difficulty, related_kp, related_methods, etc.
    """
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate metadata fields after initialization."""
        if not self.metadata:
            self.metadata = {}


@dataclass
class KGChunk:
    """Knowledge chunk model.
    
    Represents a chunk of knowledge retrieved from the vector store,
    including the similarity score from the search.
    
    Attributes:
        id: Unique chunk identifier
        content: Text content of the chunk
        metadata: Chunk metadata (source document info, etc.)
        similarity: Similarity score from vector search (0.0 to 1.0)
    """
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    similarity: float = 0.0
    
    def __post_init__(self):
        """Validate similarity score range."""
        if not 0.0 <= self.similarity <= 1.0:
            self.similarity = max(0.0, min(1.0, self.similarity))


@dataclass
class KGQuery:
    """Knowledge base query model.
    
    Represents a query to the knowledge base with optional filtering.
    
    Attributes:
        query: The search query string
        top_k: Number of results to return (default: 3)
        filter_metadata: Optional metadata filters for refined search
    """
    query: str
    top_k: int = 3
    filter_metadata: Optional[dict] = None


@dataclass
class KGResult:
    """Knowledge base retrieval result model.
    
    Represents the result of a knowledge base query.
    
    Attributes:
        success: Whether the query was successful
        chunks: List of retrieved knowledge chunks
        total: Total number of chunks retrieved
        query_time_ms: Time taken for the query in milliseconds
    """
    success: bool
    chunks: List[KGChunk] = field(default_factory=list)
    total: int = 0
    query_time_ms: float = 0.0


# Error types for the knowledge base module
class KGError(Exception):
    """Base exception class for knowledge base errors."""
    pass


class ChromaDBConnectionError(KGError):
    """Raised when ChromaDB connection fails."""
    pass


class EmbeddingServiceError(KGError):
    """Raised when embedding service call fails."""
    pass


class RetrievalTimeoutError(KGError):
    """Raised when retrieval operation times out."""
    pass


class DocumentNotFoundError(KGError):
    """Raised when a document is not found."""
    pass


class ValidationError(KGError):
    """Raised when parameter validation fails."""
    pass
