"""Tests for knowledge_base models."""
import pytest

from app.modules.knowledge_base.models import (
    DocumentType,
    KGDocument,
    KGChunk,
    KGQuery,
    KGResult,
    KGError,
    ChromaDBConnectionError,
    EmbeddingServiceError,
    RetrievalTimeoutError,
    DocumentNotFoundError,
    ValidationError,
)


class TestDocumentType:
    """Tests for DocumentType enum."""
    
    def test_document_type_has_all_five_values(self):
        """DocumentType enum should have exactly 5 values."""
        assert len(DocumentType) == 5
    
    def test_knowledge_point_value(self):
        """DocumentType should have KNOWLEDGE_POINT value."""
        assert DocumentType.KNOWLEDGE_POINT.value == "knowledge_point"
    
    def test_method_value(self):
        """DocumentType should have METHOD value."""
        assert DocumentType.METHOD.value == "method"
    
    def test_concept_value(self):
        """DocumentType should have CONCEPT value."""
        assert DocumentType.CONCEPT.value == "concept"
    
    def test_example_value(self):
        """DocumentType should have EXAMPLE value."""
        assert DocumentType.EXAMPLE.value == "example"
    
    def test_strategy_value(self):
        """DocumentType should have STRATEGY value."""
        assert DocumentType.STRATEGY.value == "strategy"
    
    def test_document_type_is_string_enum(self):
        """DocumentType should be a string enum."""
        assert isinstance(DocumentType.KNOWLEDGE_POINT, str)
        assert DocumentType.KNOWLEDGE_POINT == "knowledge_point"


class TestKGDocument:
    """Tests for KGDocument dataclass."""
    
    def test_create_kgdocument_with_required_fields(self):
        """KGDocument can be created with only required fields."""
        doc = KGDocument(
            id="test_doc_1",
            content="This is test content"
        )
        assert doc.id == "test_doc_1"
        assert doc.content == "This is test content"
        assert doc.metadata == {}
    
    def test_create_kgdocument_with_metadata(self):
        """KGDocument can be created with metadata."""
        metadata = {
            "type": "knowledge_point",
            "name": "勾股定理",
            "keywords": ["直角三角形", "平方和"],
        }
        doc = KGDocument(
            id="test_doc_2",
            content="勾股定理: a² + b² = c²",
            metadata=metadata
        )
        assert doc.id == "test_doc_2"
        assert doc.content == "勾股定理: a² + b² = c²"
        assert doc.metadata["type"] == "knowledge_point"
        assert doc.metadata["name"] == "勾股定理"
    
    def test_kgdocument_empty_metadata_defaults_to_dict(self):
        """KGDocument with empty metadata defaults to empty dict."""
        doc = KGDocument(id="test", content="test")
        assert doc.metadata == {}
    
    def test_kgdocument_metadata_none_defaults_to_dict(self):
        """KGDocument with None metadata defaults to empty dict."""
        doc = KGDocument(id="test", content="test", metadata=None)
        assert doc.metadata == {}
    
    def test_kgdocument_field_access(self):
        """KGDocument fields are accessible."""
        doc = KGDocument(
            id="doc_123",
            content="Test content",
            metadata={"grade": "high_school"}
        )
        assert doc.id == "doc_123"
        assert doc.content == "Test content"
        assert doc.metadata["grade"] == "high_school"


class TestKGChunk:
    """Tests for KGChunk dataclass."""
    
    def test_create_kgchunk_with_required_fields(self):
        """KGChunk can be created with required fields."""
        chunk = KGChunk(
            id="chunk_1",
            content="This is chunk content"
        )
        assert chunk.id == "chunk_1"
        assert chunk.content == "This is chunk content"
        assert chunk.metadata == {}
        assert chunk.similarity == 0.0
    
    def test_create_kgchunk_with_similarity(self):
        """KGChunk can be created with similarity score."""
        chunk = KGChunk(
            id="chunk_2",
            content="This is chunk content",
            similarity=0.85
        )
        assert chunk.similarity == 0.85
    
    def test_kgchunk_similarity_clamped_to_valid_range(self):
        """KGChunk clamps similarity to 0.0-1.0 range."""
        # Test upper bound
        chunk_high = KGChunk(id="c1", content="test", similarity=1.5)
        assert chunk_high.similarity == 1.0
        
        # Test lower bound
        chunk_low = KGChunk(id="c2", content="test", similarity=-0.5)
        assert chunk_low.similarity == 0.0
    
    def test_kgchunk_with_metadata(self):
        """KGChunk can be created with metadata."""
        metadata = {
            "type": "method",
            "chunk_index": 2,
            "total_chunks": 5
        }
        chunk = KGChunk(
            id="chunk_3",
            content="解题方法内容",
            metadata=metadata,
            similarity=0.72
        )
        assert chunk.metadata["type"] == "method"
        assert chunk.metadata["chunk_index"] == 2
        assert chunk.similarity == 0.72
    
    def test_kgchunk_field_access(self):
        """KGChunk fields are accessible."""
        chunk = KGChunk(
            id="chunk_456",
            content="Field access test",
            metadata={"source": "pdf"},
            similarity=0.99
        )
        assert chunk.id == "chunk_456"
        assert chunk.content == "Field access test"
        assert chunk.metadata["source"] == "pdf"
        assert chunk.similarity == 0.99


class TestKGQuery:
    """Tests for KGQuery dataclass."""
    
    def test_create_kgquery_with_required_fields(self):
        """KGQuery can be created with only query."""
        query = KGQuery(query="勾股定理")
        assert query.query == "勾股定理"
        assert query.top_k == 3
        assert query.filter_metadata is None
    
    def test_create_kgquery_with_top_k(self):
        """KGQuery can specify top_k."""
        query = KGQuery(query="解题方法", top_k=5)
        assert query.query == "解题方法"
        assert query.top_k == 5
    
    def test_create_kgquery_with_filter_metadata(self):
        """KGQuery can specify filter_metadata."""
        filters = {"type": "method", "grade": "high_school"}
        query = KGQuery(
            query="函数",
            top_k=10,
            filter_metadata=filters
        )
        assert query.query == "函数"
        assert query.top_k == 10
        assert query.filter_metadata["type"] == "method"
        assert query.filter_metadata["grade"] == "high_school"
    
    def test_kgquery_field_access(self):
        """KGQuery fields are accessible."""
        query = KGQuery(
            query="测试查询",
            top_k=7,
            filter_metadata={"difficulty": "hard"}
        )
        assert query.query == "测试查询"
        assert query.top_k == 7
        assert query.filter_metadata["difficulty"] == "hard"


class TestKGResult:
    """Tests for KGResult dataclass."""
    
    def test_create_success_result(self):
        """KGResult can represent a successful query."""
        chunks = [
            KGChunk(id="c1", content="chunk 1", similarity=0.9),
            KGChunk(id="c2", content="chunk 2", similarity=0.8),
        ]
        result = KGResult(
            success=True,
            chunks=chunks,
            total=2,
            query_time_ms=15.5
        )
        assert result.success is True
        assert len(result.chunks) == 2
        assert result.total == 2
        assert result.query_time_ms == 15.5
    
    def test_create_empty_result(self):
        """KGResult can represent an empty result."""
        result = KGResult(success=True)
        assert result.success is True
        assert result.chunks == []
        assert result.total == 0
        assert result.query_time_ms == 0.0
    
    def test_create_failed_result(self):
        """KGResult can represent a failed query."""
        result = KGResult(
            success=False,
            chunks=[],
            total=0,
            query_time_ms=500.0
        )
        assert result.success is False
        assert result.chunks == []
        assert result.total == 0
        assert result.query_time_ms == 500.0
    
    def test_kgresult_default_values(self):
        """KGResult has correct default values."""
        result = KGResult(success=True)
        assert result.chunks == []
        assert result.total == 0
        assert result.query_time_ms == 0.0


class TestKGErrorExceptions:
    """Tests for KGError exception classes."""
    
    def test_kg_error_is_base_exception(self):
        """KGError should be a subclass of Exception."""
        with pytest.raises(KGError):
            raise KGError("test error")
    
    def test_chromadb_connection_error(self):
        """ChromaDBConnectionError can be raised."""
        with pytest.raises(ChromaDBConnectionError):
            raise ChromaDBConnectionError("connection failed")
    
    def test_embedding_service_error(self):
        """EmbeddingServiceError can be raised."""
        with pytest.raises(EmbeddingServiceError):
            raise EmbeddingServiceError("embedding failed")
    
    def test_retrieval_timeout_error(self):
        """RetrievalTimeoutError can be raised."""
        with pytest.raises(RetrievalTimeoutError):
            raise RetrievalTimeoutError("timeout")
    
    def test_document_not_found_error(self):
        """DocumentNotFoundError can be raised."""
        with pytest.raises(DocumentNotFoundError):
            raise DocumentNotFoundError("document missing")
    
    def test_validation_error(self):
        """ValidationError can be raised."""
        with pytest.raises(ValidationError):
            raise ValidationError("invalid input")
    
    def test_exception_inheritance_tree(self):
        """All KGErrors inherit from KGError."""
        assert issubclass(ChromaDBConnectionError, KGError)
        assert issubclass(EmbeddingServiceError, KGError)
        assert issubclass(RetrievalTimeoutError, KGError)
        assert issubclass(DocumentNotFoundError, KGError)
        assert issubclass(ValidationError, KGError)
