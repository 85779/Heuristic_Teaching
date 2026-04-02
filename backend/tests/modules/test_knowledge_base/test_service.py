"""Tests for RAGService."""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.modules.knowledge_base.service import RAGService
from app.modules.knowledge_base.models import KGChunk, KGResult, EmbeddingServiceError, ChromaDBConnectionError


class TestRAGServiceInit:
    """Tests for RAGService initialization."""
    
    def test_init_requires_vector_store_and_embedder(self, mock_embedder, mock_vector_store):
        """RAGService initializes with vector_store and embedder."""
        service = RAGService(
            vector_store=mock_vector_store,
            embedder=mock_embedder
        )
        
        assert service.vector_store is mock_vector_store
        assert service.embedder is mock_embedder
    
    def test_retrieval_timeout_default_is_5_seconds(self, mock_embedder, mock_vector_store):
        """Default RETRIEVAL_TIMEOUT is 5.0 seconds."""
        service = RAGService(
            vector_store=mock_vector_store,
            embedder=mock_embedder
        )
        assert service.RETRIEVAL_TIMEOUT == 5.0


class TestRetrieve:
    """Tests for retrieve() async method."""
    
    @pytest.mark.asyncio
    async def test_retrieve_returns_list_of_kgchunks(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() returns list of KGChunk objects."""
        # Setup mock embedder to return an embedding
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        
        # Setup mock vector store to return some results
        mock_chunks = [
            KGChunk(id="c1", content="Chunk 1", similarity=0.9),
            KGChunk(id="c2", content="Chunk 2", similarity=0.8),
        ]
        mock_vector_store.similarity_search.return_value = [
            (chunk, chunk.similarity) for chunk in mock_chunks
        ]
        
        result = await rag_service.retrieve("test query")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(c, KGChunk) for c in result)
    
    @pytest.mark.asyncio
    async def test_retrieve_calls_embedder(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() calls embedder to generate query embedding."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = []
        
        await rag_service.retrieve("test query")
        
        mock_embedder.aembed.assert_called_once_with(["test query"])
    
    @pytest.mark.asyncio
    async def test_retrieve_calls_vector_store(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() calls vector store similarity search."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = []
        
        await rag_service.retrieve("test query", top_k=5)
        
        mock_vector_store.similarity_search.assert_called_once()
        call_kwargs = mock_vector_store.similarity_search.call_args
        assert call_kwargs[1]['top_k'] == 5
    
    @pytest.mark.asyncio
    async def test_retrieve_respects_filter_metadata(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() passes filter_metadata to vector store."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = []
        
        filters = {"type": "method", "grade": "high_school"}
        await rag_service.retrieve("test", filter_metadata=filters)
        
        call_kwargs = mock_vector_store.similarity_search.call_args
        assert call_kwargs[1]['filter_metadata'] == filters
    
    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_on_empty_embedding(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() returns empty list if embedder returns empty."""
        mock_embedder.aembed.return_value = []
        
        result = await rag_service.retrieve("test query")
        
        assert result == []
        mock_vector_store.similarity_search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_retrieve_raises_embedding_error(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() raises EmbeddingServiceError if embedding fails."""
        mock_embedder.aembed.side_effect = EmbeddingServiceError("API failed")
        
        with pytest.raises(EmbeddingServiceError):
            await rag_service.retrieve("test query")
    
    @pytest.mark.asyncio
    async def test_retrieve_raises_chromadb_error(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve() raises ChromaDBConnectionError if search fails."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.side_effect = ChromaDBConnectionError("Connection lost")
        
        with pytest.raises(ChromaDBConnectionError):
            await rag_service.retrieve("test query")


class TestRetrieveWithTiming:
    """Tests for retrieve_with_timing() async method."""
    
    @pytest.mark.asyncio
    async def test_retrieve_with_timing_returns_kgresult(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve_with_timing() returns KGResult with timing."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = [
            (KGChunk(id="c1", content="Test", similarity=0.9), 0.9)
        ]
        
        result = await rag_service.retrieve_with_timing("test")
        
        assert isinstance(result, KGResult)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_retrieve_with_timing_includes_query_time(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve_with_timing() includes query_time_ms in result."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = []
        
        result = await rag_service.retrieve_with_timing("test")
        
        assert result.query_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_retrieve_with_timing_returns_failed_result_on_error(self, rag_service, mock_embedder, mock_vector_store):
        """retrieve_with_timing() returns failed KGResult on exception."""
        mock_embedder.aembed.side_effect = EmbeddingServiceError("failed")
        
        result = await rag_service.retrieve_with_timing("test")
        
        assert isinstance(result, KGResult)
        assert result.success is False
        assert result.query_time_ms >= 0


class TestEnrichHintPrompt:
    """Tests for enrich_hint_prompt() async method."""
    
    @pytest.mark.asyncio
    async def test_enrich_hint_prompt_returns_string(self, rag_service):
        """enrich_hint_prompt() returns a formatted string."""
        chunks = [
            KGChunk(id="c1", content="相关知识点：勾股定理", similarity=0.9),
            KGChunk(id="c2", content="解题方法：构造直角三角形", similarity=0.8),
        ]
        
        result = await rag_service.enrich_hint_prompt(
            hint_template="学生当前步骤：{student_input}",
            student_input="正在计算第三边",
            expected_step="应用勾股定理",
            knowledge_chunks=chunks
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_enrich_hint_prompt_includes_chunk_content(self, rag_service):
        """enrich_hint_prompt() injects chunk content into prompt."""
        chunks = [
            KGChunk(id="c1", content="这是相关知识点内容", similarity=0.9),
        ]
        
        result = await rag_service.enrich_hint_prompt(
            hint_template="Template",
            student_input="学生输入",
            expected_step="期望步骤",
            knowledge_chunks=chunks
        )
        
        assert "这是相关知识点内容" in result
    
    @pytest.mark.asyncio
    async def test_enrich_hint_prompt_returns_template_if_no_chunks(self, rag_service):
        """enrich_hint_prompt() returns original template if chunks empty."""
        template = "Original template"
        
        result = await rag_service.enrich_hint_prompt(
            hint_template=template,
            student_input="input",
            expected_step="step",
            knowledge_chunks=[]
        )
        
        assert result == template


class TestEnrichWithContext:
    """Tests for enrich_with_context() async method."""
    
    @pytest.mark.asyncio
    async def test_enrich_with_context_returns_string(self, rag_service, mock_embedder, mock_vector_store):
        """enrich_with_context() returns formatted context string."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = [
            (KGChunk(id="c1", content="Context 1", similarity=0.9), 0.9)
        ]
        
        result = await rag_service.enrich_with_context("test query")
        
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_enrich_with_context_retrieves_and_formats(self, rag_service, mock_embedder, mock_vector_store):
        """enrich_with_context() retrieves chunks and formats them."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        mock_vector_store.similarity_search.return_value = [
            (KGChunk(id="c1", content="知识内容", metadata={"type": "kp"}, similarity=0.9), 0.9)
        ]
        
        result = await rag_service.enrich_with_context("查询", top_k=3)
        
        assert isinstance(result, str)
        mock_vector_store.similarity_search.assert_called_once()


class TestGetStats:
    """Tests for get_stats() method."""
    
    def test_get_stats_returns_dict(self, rag_service, mock_vector_store):
        """get_stats() returns a dictionary."""
        result = rag_service.get_stats()
        assert isinstance(result, dict)
    
    def test_get_stats_delegates_to_vector_store(self, rag_service, mock_vector_store):
        """get_stats() calls vector_store.get_stats()."""
        rag_service.get_stats()
        
        mock_vector_store.get_stats.assert_called_once()
    
    def test_get_stats_includes_status(self, rag_service, mock_vector_store):
        """get_stats() includes status field."""
        result = rag_service.get_stats()
        
        assert "status" in result
        assert result["status"] == "healthy"
    
    def test_get_stats_includes_collection_info(self, rag_service, mock_vector_store):
        """get_stats() includes collection information."""
        result = rag_service.get_stats()
        
        assert "collection" in result
        assert "document_count" in result
        assert "dimension" in result


class TestHealthCheck:
    """Tests for health_check() async method."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self, rag_service, mock_embedder, mock_vector_store):
        """health_check() returns dictionary with health status."""
        mock_vector_store.count.return_value = 10
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        
        result = await rag_service.health_check()
        
        assert isinstance(result, dict)
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_health_check_checks_vector_store(self, rag_service, mock_vector_store):
        """health_check() checks vector store connectivity."""
        mock_vector_store.count.return_value = 5
        
        result = await rag_service.health_check()
        
        assert "vector_store" in result
        mock_vector_store.count.assert_called()
    
    @pytest.mark.asyncio
    async def test_health_check_checks_embedding_service(self, rag_service, mock_embedder):
        """health_check() checks embedding service."""
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        
        result = await rag_service.health_check()
        
        assert "embedding_service" in result
    
    @pytest.mark.asyncio
    async def test_health_check_returns_document_count(self, rag_service, mock_vector_store, mock_embedder):
        """health_check() returns document count."""
        mock_vector_store.count.return_value = 42
        mock_embedder.aembed.return_value = [[0.1] * 1024]
        
        result = await rag_service.health_check()
        
        assert result["document_count"] == 42


class TestDeleteAllDocuments:
    """Tests for delete_all_documents() async method."""
    
    @pytest.mark.asyncio
    async def test_delete_all_documents_returns_dict(self, rag_service, mock_vector_store):
        """delete_all_documents() returns result dictionary."""
        mock_vector_store.delete_all.return_value = None
        
        result = await rag_service.delete_all_documents()
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_delete_all_documents_calls_vector_store(self, rag_service, mock_vector_store):
        """delete_all_documents() calls vector_store.delete_all()."""
        await rag_service.delete_all_documents()
        
        mock_vector_store.delete_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_all_documents_returns_success_status(self, rag_service, mock_vector_store):
        """delete_all_documents() returns success status."""
        result = await rag_service.delete_all_documents()
        
        assert result["status"] == "success"


class TestGetDocumentTypes:
    """Tests for get_document_types() method."""
    
    def test_get_document_types_returns_list(self, rag_service):
        """get_document_types() returns a list."""
        result = rag_service.get_document_types()
        assert isinstance(result, list)
    
    def test_get_document_types_contains_all_types(self, rag_service):
        """get_document_types() returns all 5 document type values."""
        result = rag_service.get_document_types()
        
        assert "knowledge_point" in result
        assert "method" in result
        assert "concept" in result
        assert "example" in result
        assert "strategy" in result
    
    def test_get_document_types_returns_string_values(self, rag_service):
        """get_document_types() returns string values."""
        result = rag_service.get_document_types()
        
        assert all(isinstance(t, str) for t in result)
