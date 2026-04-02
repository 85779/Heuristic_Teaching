"""DashScope Embedding Client for generating text embeddings.

This module provides a client for the DashScope embedding API using the
existing DashScopeClient infrastructure with OpenAI-compatible API.
It handles batching, error handling, and API key management.
"""

import os
import asyncio
import logging
from typing import List, Optional

from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.config import settings

from .models import EmbeddingServiceError

logger = logging.getLogger(__name__)


class DashScopeEmbeddingClient:
    """Client for DashScope embedding API.
    
    Provides synchronous and asynchronous methods for generating
    text embeddings using the DashScope text-embedding-v4 model
    via OpenAI-compatible API.
    
    Attributes:
        DEFAULT_MODEL: Default embedding model name
        EMBEDDING_DIM: Output embedding dimension (1536 for text-embedding-v4)
        BATCH_SIZE: Maximum texts per API call
    """
    
    DEFAULT_MODEL = "text-embedding-v4"
    EMBEDDING_DIM = 1024  # text-embedding-v4 outputs 1024-dim vectors
    BATCH_SIZE = 10  # Max batch size for text-embedding-v4
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the DashScope embedding client.
        
        Args:
            api_key: DashScope API key. If not provided, reads from
                    DASHSCOPE_API_KEY environment variable or app settings.
            model: Embedding model name. If not provided, uses
                  text-embedding-v4.
        
        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # Priority: explicit param > env var > settings
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or settings.DASHSCOPE_API_KEY
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY must be provided or set in environment"
            )
        
        self.model = model or self.DEFAULT_MODEL
        
        # Use existing DashScopeClient with OpenAI-compatible endpoint
        self._client = DashScopeClient(
            api_key=self.api_key,
            model=self.model,
        )
    
    async def aembed(self, texts: List[str]) -> List[List[float]]:
        """Async embed using DashScopeClient OpenAI-compatible API.
        
        Batches texts and calls DashScope API. Handles texts longer
        than BATCH_SIZE by splitting into multiple calls.
        
        Args:
            texts: List of text strings to embed.
        
        Returns:
            List of embedding vectors (1536-dim each), in same order as input.
        
        Raises:
            EmbeddingServiceError: If API call fails after retries.
        """
        if not texts:
            return []
        
        all_embeddings: List[List[float]] = []
        
        # Process in batches
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i:i + self.BATCH_SIZE]
            
            # Retry logic with exponential backoff
            max_retries = 3
            last_error: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    embeddings = await self._client.get_embeddings(batch, model=self.model)
                    all_embeddings.extend(embeddings)
                    break
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Embedding attempt {attempt + 1} failed, "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries} embedding attempts failed: {e}"
                        )
                        raise EmbeddingServiceError(
                            f"Failed to get embeddings after {max_retries} attempts: {e}"
                        ) from last_error
        
        return all_embeddings
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embed - batch call to DashScope API.
        
        This is a convenience method that wraps the async version.
        For production use, prefer aembed() for better performance.
        
        Args:
            texts: List of text strings to embed (max 25 per call for v4).
        
        Returns:
            List of embedding vectors (1536-dim each).
        
        Raises:
            EmbeddingServiceError: If API call fails.
            ValueError: If texts count exceeds batch size.
        """
        if len(texts) > self.BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(texts)} exceeds maximum {self.BATCH_SIZE}. "
                "Please batch larger inputs manually."
            )
        
        try:
            return asyncio.run(self.aembed(texts))
        except RuntimeError as e:
            if "event loop" in str(e).lower():
                # If no event loop is running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.aembed(texts))
                finally:
                    loop.close()
            raise
    
    async def embed_with_retry(
        self,
        texts: List[str],
        max_retries: int = 3
    ) -> List[List[float]]:
        """Embed texts with retry logic.
        
        Args:
            texts: List of text strings to embed.
            max_retries: Maximum number of retry attempts (default: 3).
        
        Returns:
            List of embedding vectors.
        """
        return await self.aembed(texts)
    
    async def aclose(self) -> None:
        """Close the HTTP client connection."""
        await self._client.close()
    
    async def health_check(self) -> bool:
        """Check if the embedding service is healthy."""
        try:
            test_embedding = await self._client.get_embeddings(
                ["health check"], model=self.model
            )
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            return False
