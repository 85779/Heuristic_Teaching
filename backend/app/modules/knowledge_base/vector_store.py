"""ChromaDB Vector Store implementation for the knowledge base.

This module provides a wrapper around ChromaDB for storing and retrieving
knowledge documents using vector similarity search.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any

import chromadb
from chromadb.config import Settings

from .models import KGDocument, KGChunk, ChromaDBConnectionError

logger = logging.getLogger(__name__)


class ChromaDBVectorStore:
    """Vector store implementation using ChromaDB.
    
    Provides document storage and similarity search capabilities using
    ChromaDB's PersistentClient for local storage.
    
    Attributes:
        COLLECTION_NAME: Name of the ChromaDB collection
        EMBEDDING_DIM: Expected embedding dimension (1024)
    """
    
    COLLECTION_NAME = "math_knowledge"
    EMBEDDING_DIM = 1024  # text-embedding-v4 outputs 1024-dim vectors
    
    def __init__(self, persist_dir: Optional[str] = None):
        """Initialize the ChromaDB vector store.
        
        Args:
            persist_dir: Directory for ChromaDB persistence. If not provided,
                        uses CHROMA_PERSIST_DIR env var or "./data/chromadb".
        
        Raises:
            ChromaDBConnectionError: If ChromaDB fails to initialize.
        """
        self.persist_dir = persist_dir or os.getenv(
            "CHROMA_PERSIST_DIR", "./data/chromadb"
        )
        
        # Ensure persist directory exists
        os.makedirs(self.persist_dir, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"dimension": self.EMBEDDING_DIM}
            )
            logger.info(
                f"ChromaDB vector store initialized at {self.persist_dir}, "
                f"collection: {self.COLLECTION_NAME}"
            )
        except Exception as e:
            raise ChromaDBConnectionError(
                f"Failed to initialize ChromaDB: {e}"
            )
    
    def _document_to_chroma(
        self,
        document: KGDocument,
        embedding: List[float]
    ) -> Tuple[str, List[float], str, dict]:
        """Convert KGDocument to ChromaDB format.
        
        Args:
            document: KGDocument to convert.
            embedding: Pre-computed embedding vector.
        
        Returns:
            Tuple of (id, embedding, document text, metadata).
        """
        return (
            document.id,
            embedding,
            document.content,
            document.metadata
        )
    
    def _chroma_to_chunk(
        self,
        chroma_doc: Dict[str, Any],
        distance: float
    ) -> KGChunk:
        """Convert ChromaDB document to KGChunk.
        
        Args:
            chroma_doc: Document from ChromaDB.
            distance: Distance score from search.
        
        Returns:
            KGChunk with content and metadata.
        """
        # ChromaDB stores distance, convert to similarity
        # ChromaDB uses cosine distance (lower = more similar)
        similarity = 1.0 - distance if distance is not None else 0.0
        
        return KGChunk(
            id=chroma_doc["id"],
            content=chroma_doc["document"],
            metadata=chroma_doc.get("metadata", {}),
            similarity=max(0.0, min(1.0, similarity))
        )
    
    def add_documents(
        self,
        documents: List[KGDocument],
        embeddings: List[List[float]]
    ) -> None:
        """Add documents with pre-computed embeddings to ChromaDB.
        
        Args:
            documents: List of KGDocument objects to add.
            embeddings: List of embedding vectors (must match document order).
        
        Raises:
            ChromaDBConnectionError: If adding documents fails.
            ValueError: If document/embedding count mismatch.
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) must match "
                f"embedding count ({len(embeddings)})"
            )
        
        if not documents:
            return
        
        try:
            ids = []
            embeds = []
            documents_text = []
            metadatas = []
            
            for doc, embedding in zip(documents, embeddings):
                ids.append(doc.id)
                embeds.append(embedding)
                documents_text.append(doc.content)
                # ChromaDB only accepts scalar metadata values - convert lists to comma-separated strings
                sanitized_metadata = {}
                for key, value in (doc.metadata or {}).items():
                    if isinstance(value, list):
                        sanitized_metadata[key] = ",".join(str(v) for v in value)
                    elif value is None:
                        sanitized_metadata[key] = ""  # ChromaDB rejects None
                    elif isinstance(value, (str, int, float, bool)):
                        sanitized_metadata[key] = value
                    else:
                        sanitized_metadata[key] = str(value)
                metadatas.append(sanitized_metadata)
            
            self.collection.add(
                ids=ids,
                embeddings=embeds,
                documents=documents_text,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            
        except Exception as e:
            raise ChromaDBConnectionError(
                f"Failed to add documents to ChromaDB: {e}"
            )
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> List[Tuple[KGChunk, float]]:
        """Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector to search with.
            top_k: Number of results to return (default: 3).
            filter_metadata: Optional metadata filters.
        
        Returns:
            List of tuples containing (KGChunk, similarity_score),
            sorted by similarity (highest first).
        
        Raises:
            ChromaDBConnectionError: If search fails.
        """
        try:
            where_clause = None
            if filter_metadata:
                where_clause = filter_metadata
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            chunks_with_scores = []
            
            if results and results["ids"] and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0] if results["documents"] else []
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                for i, doc_id in enumerate(ids):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 0.0
                    
                    chunk = KGChunk(
                        id=doc_id,
                        content=documents[i] if i < len(documents) else "",
                        metadata=metadata,
                        similarity=0.0
                    )
                    
                    # Convert distance to similarity (cosine distance)
                    # Distance is in [0, 2] range, where 0 is identical
                    similarity = 1.0 - (distance / 2.0) if distance is not None else 0.0
                    similarity = max(0.0, min(1.0, similarity))
                    
                    chunks_with_scores.append((chunk, similarity))
            
            # Sort by similarity descending
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            return chunks_with_scores
            
        except Exception as e:
            raise ChromaDBConnectionError(
                f"Similarity search failed: {e}"
            )
    
    def get_by_id(self, document_id: str) -> Optional[KGChunk]:
        """Get a document by its ID.
        
        Args:
            document_id: The document ID to retrieve.
        
        Returns:
            KGChunk if found, None otherwise.
        """
        try:
            results = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if results and results["ids"] and len(results["ids"]) > 0:
                doc_id = results["ids"][0]
                document = results["documents"][0] if results["documents"] else ""
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                
                return KGChunk(
                    id=doc_id,
                    content=document,
                    metadata=metadata,
                    similarity=1.0  # Exact match
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    def delete_all(self) -> None:
        """Delete all documents in the collection.
        
        Raises:
            ChromaDBConnectionError: If deletion fails.
        """
        try:
            self.collection.delete(where={})
            logger.info("Deleted all documents from ChromaDB collection")
        except Exception as e:
            raise ChromaDBConnectionError(
                f"Failed to delete all documents: {e}"
            )
    
    def delete_by_id(self, document_id: str) -> None:
        """Delete a specific document by ID.
        
        Args:
            document_id: ID of the document to delete.
        """
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id}")
        except Exception as e:
            raise ChromaDBConnectionError(
                f"Failed to delete document {document_id}: {e}"
            )
    
    def count(self) -> int:
        """Return the number of documents in the collection.
        
        Returns:
            Total document count.
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Return collection statistics.
        
        Returns:
            Dictionary with collection stats including count,
            dimension, and collection name.
        """
        try:
            count = self.collection.count()
            
            # Try to get additional stats from peek
            peek = self.collection.peek(limit=1)
            sample_size = len(peek.get("ids", [])) if peek else 0
            
            return {
                "collection_name": self.COLLECTION_NAME,
                "dimension": self.EMBEDDING_DIM,
                "document_count": count,
                "persist_dir": self.persist_dir,
                "has_documents": count > 0,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.COLLECTION_NAME,
                "dimension": self.EMBEDDING_DIM,
                "document_count": 0,
                "persist_dir": self.persist_dir,
                "error": str(e),
            }
    
    def reset(self) -> None:
        """Reset the collection (delete all documents).
        
        This is equivalent to delete_all().
        """
        self.delete_all()
