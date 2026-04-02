"""Tests for DashScopeEmbeddingClient.

这些测试验证使用 DashScopeClient (OpenAI兼容模式) 的新实现。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.modules.knowledge_base.embedder import DashScopeEmbeddingClient
from app.modules.knowledge_base.models import EmbeddingServiceError


class TestDashScopeEmbeddingClientInit:
    """Tests for DashScopeEmbeddingClient initialization."""
    
    def test_init_with_api_key(self):
        """Client initializes with explicit API key."""
        client = DashScopeEmbeddingClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.model == "text-embedding-v4"
    
    def test_init_without_api_key_uses_env(self):
        """Client uses DASHSCOPE_API_KEY env variable if no key provided."""
        with patch.dict('os.environ', {'DASHSCOPE_API_KEY': 'env-key-456'}):
            client = DashScopeEmbeddingClient()
            assert client.api_key == "env-key-456"
    
    def test_init_raises_if_no_api_key(self):
        """Client raises ValueError if no API key available."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('app.modules.knowledge_base.embedder.settings') as mock_settings:
                mock_settings.DASHSCOPE_API_KEY = None
                with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
                    DashScopeEmbeddingClient()
    
    def test_init_with_custom_model(self):
        """Client can use custom embedding model."""
        client = DashScopeEmbeddingClient(
            api_key="test-key",
            model="custom-embedding-model"
        )
        assert client.model == "custom-embedding-model"
    
    def test_default_model_is_text_embedding_v4(self):
        """Default embedding model is text-embedding-v4."""
        client = DashScopeEmbeddingClient(api_key="test-key")
        assert client.DEFAULT_MODEL == "text-embedding-v4"
        assert client.model == "text-embedding-v4"
    
    def test_embedding_dimension_is_1024(self):
        """Embedding dimension is 1024 for text-embedding-v4."""
        client = DashScopeEmbeddingClient(api_key="test-key")
        assert client.EMBEDDING_DIM == 1024
    
    def test_batch_size_is_10(self):
        """Batch size limit is 10 for text-embedding-v4."""
        client = DashScopeEmbeddingClient(api_key="test-key")
        assert client.BATCH_SIZE == 10


class TestEmbedderEmbed:
    """Tests for synchronous embed() method."""
    
    def test_embed_returns_list_of_float_lists(self):
        """embed() returns a list of embedding vectors."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(return_value=[[0.1] * 1024])
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = client.embed(["test text"])
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], list)
            assert len(result[0]) == 1024
    
    def test_embed_single_text(self):
        """embed() handles single text input."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(return_value=[[0.5] * 1024])
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = client.embed(["single text"])
            
            assert len(result) == 1
            assert all(x == 0.5 for x in result[0])
    
    def test_embed_raises_if_batch_exceeds_limit(self):
        """embed() raises ValueError if batch size > 10."""
        client = DashScopeEmbeddingClient(api_key="test-key")
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            client.embed(["text"] * 11)
    
    def test_embed_batch_size_at_limit(self):
        """embed() works when batch size == 10."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(return_value=[[0.1] * 1024 for _ in range(10)])
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            texts = [f"text_{i}" for i in range(10)]
            result = client.embed(texts)
            
            assert len(result) == 10


class TestEmbedderAembed:
    """Tests for async aembed() method."""
    
    @pytest.mark.asyncio
    async def test_aembed_returns_list_of_float_lists(self):
        """aembed() returns a list of embedding vectors."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(return_value=[[0.2] * 1024])
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = await client.aembed(["async text"])
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert all(x == 0.2 for x in result[0])
    
    @pytest.mark.asyncio
    async def test_aembed_empty_list_returns_empty(self):
        """aembed([]) returns empty list."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = await client.aembed([])
            assert result == []
    
    @pytest.mark.asyncio
    async def test_aembed_handles_batch_greater_than_10(self):
        """aembed() batches texts > 10 into multiple API calls."""
        call_count = 0
        
        async def mock_get_embeddings(texts, model=None):
            nonlocal call_count
            call_count += 1
            return [[0.1] * 1024 for _ in range(len(texts))]
        
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = mock_get_embeddings
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            
            # 50 texts should result in 5 batches (10 + 10 + 10 + 10 + 10)
            texts = [f"text_{i}" for i in range(50)]
            result = await client.aembed(texts)
            
            assert len(result) == 50
            assert call_count == 5


class TestEmbedderAPIErrorHandling:
    """Tests for API error handling."""
    
    @pytest.mark.asyncio
    async def test_aembed_raises_on_http_error(self):
        """aembed() raises EmbeddingServiceError on HTTP error."""
        async def mock_get_embeddings_error(texts, model=None):
            raise Exception("HTTP 401: Unauthorized")
        
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = mock_get_embeddings_error
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="bad-key")
            
            with pytest.raises(EmbeddingServiceError):
                await client.aembed(["test"])
    
    @pytest.mark.asyncio
    async def test_aembed_retries_on_service_error(self):
        """aembed() retries on transient errors."""
        call_count = 0
        
        async def mock_get_embeddings_retry(texts, model=None):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Service Unavailable")
            return [[0.1] * 1024]
        
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = mock_get_embeddings_retry
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = await client.aembed(["test"])
            
            assert call_count == 3
            assert len(result) == 1


class TestEmbedderHealthCheck:
    """Tests for health check."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self):
        """health_check() returns True when service is healthy."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(return_value=[[0.1] * 1024])
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = await client.health_check()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_error(self):
        """health_check() returns False on error."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.get_embeddings = AsyncMock(side_effect=Exception("Connection failed"))
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            result = await client.health_check()
            
            assert result is False


class TestEmbedderClose:
    """Tests for close method."""
    
    @pytest.mark.asyncio
    async def test_aclose_calls_client_close(self):
        """aclose() closes the underlying DashScopeClient."""
        with patch('app.modules.knowledge_base.embedder.DashScopeClient') as MockClient:
            mock_instance = MagicMock()
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            
            client = DashScopeEmbeddingClient(api_key="test-key")
            await client.aclose()
            
            mock_instance.close.assert_called_once()
