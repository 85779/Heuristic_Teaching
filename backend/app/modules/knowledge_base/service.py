"""RAG Service - Core service class for knowledge retrieval.

This module provides the main RAGService class that orchestrates
retrieval and hint enrichment using the knowledge base.
"""

import logging
import time
from typing import List, Optional, Dict, Any

from .models import (
    KGDocument,
    KGChunk,
    KGQuery,
    KGResult,
    KGError,
    EmbeddingServiceError,
    ChromaDBConnectionError,
)
from .vector_store import ChromaDBVectorStore
from .embedder import DashScopeEmbeddingClient
from .prompts import format_hint_enrichment, format_context_from_chunks

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for knowledge base queries.
    
    Provides retrieval of relevant knowledge chunks and enrichment
    of prompts with retrieved context.
    
    Attributes:
        RETRIEVAL_TIMEOUT: Default retrieval timeout in seconds.
    """
    
    RETRIEVAL_TIMEOUT = 5.0
    
    def __init__(
        self,
        vector_store: ChromaDBVectorStore,
        embedder: DashScopeEmbeddingClient
    ):
        """Initialize the RAG service.
        
        Args:
            vector_store: ChromaDB vector store instance.
            embedder: DashScope embedding client instance.
        """
        self.vector_store = vector_store
        self.embedder = embedder
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> List[KGChunk]:
        """Retrieve top_k relevant knowledge chunks for a query.
        
        Args:
            query: Search query string.
            top_k: Number of results to return (default: 3).
            filter_metadata: Optional metadata filters.
        
        Returns:
            List of KGChunk objects sorted by relevance.
        
        Raises:
            EmbeddingServiceError: If embedding generation fails.
            ChromaDBConnectionError: If vector search fails.
            RetrievalTimeoutError: If retrieval exceeds timeout.
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate query embedding
            query_embedding = await self.embedder.aembed([query])
            
            if not query_embedding or len(query_embedding) == 0:
                logger.warning("Query embedding returned empty result")
                return []
            
            embedding = query_embedding[0]
            
            # Step 2: Search ChromaDB
            results = self.vector_store.similarity_search(
                query_embedding=embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # Extract chunks from results
            chunks = [chunk for chunk, _ in results]
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Retrieved {len(chunks)} chunks for query '{query[:50]}...' "
                f"in {elapsed_ms:.2f}ms"
            )
            
            return chunks
            
        except EmbeddingServiceError as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
        except ChromaDBConnectionError as e:
            logger.error(f"Vector search failed: {e}")
            raise
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Retrieval failed after {elapsed_ms:.2f}ms: {e}")
            raise
    
    async def retrieve_with_timing(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> KGResult:
        """Retrieve chunks and return with timing information.
        
        Args:
            query: Search query string.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filters.
        
        Returns:
            KGResult with chunks, count, and timing.
        """
        start_time = time.time()
        
        try:
            chunks = await self.retrieve(query, top_k, filter_metadata)
            elapsed_ms = (time.time() - start_time) * 1000
            
            return KGResult(
                success=True,
                chunks=chunks,
                total=len(chunks),
                query_time_ms=elapsed_ms
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Retrieval with timing failed: {e}")
            
            return KGResult(
                success=False,
                chunks=[],
                total=0,
                query_time_ms=elapsed_ms
            )
    
    async def enrich_hint_prompt(
        self,
        hint_template: str,
        student_input: str,
        expected_step: str,
        knowledge_chunks: List[KGChunk]
    ) -> str:
        """Enrich hint prompt with retrieved knowledge chunks.
        
        Takes a hint template and injects relevant knowledge from
        the knowledge base to create an enriched prompt for LLM.
        
        Args:
            hint_template: Base hint template (can be custom or from prompts.py).
            student_input: Student's current input/step.
            expected_step: Expected next step content.
            knowledge_chunks: Retrieved knowledge chunks.
        
        Returns:
            Enriched prompt string with knowledge context.
        """
        if not knowledge_chunks:
            logger.warning("No knowledge chunks provided for enrichment")
            return hint_template
        
        # Use the format function from prompts module
        enriched = format_hint_enrichment(
            chunks=knowledge_chunks,
            student_input=student_input,
            expected_step=expected_step
        )
        
        logger.debug(
            f"Enriched hint with {len(knowledge_chunks)} knowledge chunks"
        )
        
        return enriched
    
    async def enrich_with_context(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> str:
        """Retrieve knowledge and format as context string.
        
        Convenience method that retrieves chunks and formats them
        into a context string for use in prompts.
        
        Args:
            query: Search query string.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filters.
        
        Returns:
            Formatted context string.
        """
        chunks = await self.retrieve(query, top_k, filter_metadata)
        return format_context_from_chunks(chunks)
    
    def get_stats(self) -> Dict[str, Any]:
        """Return knowledge base statistics.
        
        Returns:
            Dictionary with collection stats including document count,
            dimension, and health status.
        """
        try:
            stats = self.vector_store.get_stats()
            return {
                "status": "healthy",
                "collection": stats.get("collection_name"),
                "dimension": stats.get("dimension"),
                "document_count": stats.get("document_count"),
                "persist_dir": stats.get("persist_dir"),
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the RAG service.
        
        Checks both vector store and embedding service.
        
        Returns:
            Dictionary with health status of each component.
        """
        results = {
            "status": "healthy",
            "vector_store": "unknown",
            "embedding_service": "unknown",
            "document_count": 0,
        }
        
        # Check vector store
        try:
            count = self.vector_store.count()
            results["vector_store"] = "healthy"
            results["document_count"] = count
        except Exception as e:
            results["vector_store"] = f"unhealthy: {str(e)}"
            results["status"] = "degraded"
        
        # Check embedding service
        try:
            test_embedding = await self.embedder.aembed(["health check"])
            if test_embedding and len(test_embedding) > 0:
                results["embedding_service"] = "healthy"
            else:
                results["embedding_service"] = "unhealthy: empty response"
                results["status"] = "degraded"
        except Exception as e:
            results["embedding_service"] = f"unhealthy: {str(e)}"
            results["status"] = "degraded"
        
        return results
    
    async def delete_all_documents(self) -> Dict[str, Any]:
        """Delete all documents from the knowledge base.
        
        Returns:
            Result dictionary with status.
        """
        try:
            self.vector_store.delete_all()
            return {
                "status": "success",
                "message": "All documents deleted"
            }
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_document_types(self) -> List[str]:
        """Get list of valid document types.
        
        Returns:
            List of document type strings.
        """
        from .models import DocumentType
        return [dt.value for dt in DocumentType]
