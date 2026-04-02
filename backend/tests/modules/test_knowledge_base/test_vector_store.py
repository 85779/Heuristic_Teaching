"""Tests for ChromaDBVectorStore."""
import pytest
from unittest.mock import MagicMock, patch

from app.modules.knowledge_base.vector_store import ChromaDBVectorStore
from app.modules.knowledge_base.models import KGDocument, KGChunk, ChromaDBConnectionError


class TestChromaDBVectorStoreInit:
    """Tests for ChromaDBVectorStore initialization."""
    
    def test_init_uses_chroma_persist_dir_from_env(self):
        """Vector store uses CHROMA_PERSIST_DIR env variable."""
        with patch('chromadb.PersistentClient') as mock_client, \
             patch.dict('os.environ', {'CHROMA_PERSIST_DIR': '/custom/path'}):
            store = ChromaDBVectorStore()
            assert store.persist_dir == '/custom/path'
    
    def test_init_uses_provided_persist_dir(self):
        """Vector store uses provided persist_dir over env var."""
        with patch('chromadb.PersistentClient') as mock_client:
            store = ChromaDBVectorStore(persist_dir="/my/custom/path")
            assert store.persist_dir == "/my/custom/path"
    
    def test_init_creates_directory_if_not_exists(self, tmp_path):
        """Vector store creates persist directory if it doesn't exist."""
        test_dir = str(tmp_path / "new_chroma_dir")
        
        with patch('chromadb.PersistentClient') as mock_client:
            store = ChromaDBVectorStore(persist_dir=test_dir)
            import os
            assert os.path.exists(test_dir)
    
    def test_init_gets_or_creates_collection(self):
        """Vector store calls get_or_create_collection on init."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            
            store = ChromaDBVectorStore(persist_dir="/test")
            
            mock_instance.get_or_create_collection.assert_called_once()
            call_kwargs = mock_instance.get_or_create_collection.call_args
            assert call_kwargs[1]['name'] == "math_knowledge"
    
    def test_collection_name_is_math_knowledge(self):
        """Collection name is math_knowledge."""
        with patch('chromadb.PersistentClient'):
            store = ChromaDBVectorStore(persist_dir="/test")
            assert store.COLLECTION_NAME == "math_knowledge"
    
    def test_embedding_dimension_is_1024(self):
        """Embedding dimension is 1024 for text-embedding-v4."""
        with patch('chromadb.PersistentClient'):
            store = ChromaDBVectorStore(persist_dir="/test")
            assert store.EMBEDDING_DIM == 1024


class TestAddDocuments:
    """Tests for add_documents() method."""
    
    def test_add_documents_stores_documents(self, vector_store):
        """add_documents() stores documents in ChromaDB."""
        documents = [
            KGDocument(id="doc1", content="Content 1", metadata={"type": "kp"}),
            KGDocument(id="doc2", content="Content 2", metadata={"type": "method"}),
        ]
        embeddings = [[0.1] * 1024, [0.2] * 1024]
        
        vector_store.add_documents(documents, embeddings)
        
        # Verify collection.add was called via mock_calls
        add_calls = [c for c in vector_store.collection._mock_calls if c[0] == 'add']
        assert len(add_calls) >= 1
    
    def test_add_documents_raises_on_count_mismatch(self, vector_store):
        """add_documents() raises ValueError if doc/embedding count mismatch."""
        documents = [
            KGDocument(id="doc1", content="Content 1"),
            KGDocument(id="doc2", content="Content 2"),
        ]
        embeddings = [[0.1] * 1024]  # Only one embedding
        
        with pytest.raises(ValueError, match="must match"):
            vector_store.add_documents(documents, embeddings)
    
    def test_add_documents_does_nothing_for_empty_list(self, vector_store):
        """add_documents() returns early if documents list is empty."""
        vector_store.add_documents([], [])
        # No exception means success (early return)


class TestSimilaritySearch:
    """Tests for similarity_search() method."""
    
    def test_similarity_search_returns_list_of_tuples(self, vector_store):
        """similarity_search() returns list of (KGChunk, float) tuples."""
        # First add a document
        doc = KGDocument(id="doc1", content="Test content", metadata={"type": "kp"})
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        results = vector_store.similarity_search(
            query_embedding=[0.1] * 1024,
            top_k=3
        )
        
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], KGChunk)
            assert isinstance(item[1], float)
    
    def test_similarity_search_returns_sorted_by_similarity(self, vector_store):
        """similarity_search() returns results sorted by similarity descending."""
        # Add multiple documents
        docs = [
            KGDocument(id="doc1", content="Content 1", metadata={"type": "kp"}),
            KGDocument(id="doc2", content="Content 2", metadata={"type": "method"}),
            KGDocument(id="doc3", content="Content 3", metadata={"type": "concept"}),
        ]
        embeddings = [[0.1] * 1024, [0.5] * 1024, [0.3] * 1024]
        vector_store.add_documents(docs, embeddings)
        
        results = vector_store.similarity_search(
            query_embedding=[0.4] * 1024,
            top_k=3
        )
        
        # Results should be sorted by similarity (highest first)
        if len(results) >= 2:
            assert results[0][1] >= results[1][1]
    
    def test_similarity_search_with_filter_metadata(self, vector_store):
        """similarity_search() accepts filter_metadata parameter."""
        doc = KGDocument(id="doc1", content="Test content", metadata={"type": "kp"})
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        results = vector_store.similarity_search(
            query_embedding=[0.1] * 1024,
            top_k=3,
            filter_metadata={"type": "kp"}
        )
        
        assert isinstance(results, list)
    
    def test_similarity_search_empty_results_when_no_matches(self, vector_store):
        """similarity_search() returns empty list when no matches."""
        results = vector_store.similarity_search(
            query_embedding=[0.1] * 1024,
            top_k=3
        )
        
        assert results == []


class TestDeleteOperations:
    """Tests for delete operations."""
    
    def test_delete_all_clears_collection(self, vector_store):
        """delete_all() clears all documents from collection."""
        # Add some documents first
        docs = [
            KGDocument(id="doc1", content="Content 1"),
            KGDocument(id="doc2", content="Content 2"),
        ]
        vector_store.add_documents(docs, [[0.1] * 1024, [0.2] * 1024])
        
        # Verify count is 2
        assert vector_store.count() == 2
        
        # Delete all
        vector_store.delete_all()
        
        # Verify collection.delete was called via mock_calls
        delete_calls = [c for c in vector_store.collection._mock_calls if c[0] == 'delete']
        assert len(delete_calls) >= 1
        # Verify one of the calls had where={}
        where_calls = [c for c in delete_calls if c[1] == {}]
        assert len(where_calls) >= 1
    
    def test_delete_by_id_removes_specific_document(self, vector_store):
        """delete_by_id() removes a specific document."""
        doc = KGDocument(id="doc_to_delete", content="Will be deleted")
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        assert vector_store.count() == 1
        
        vector_store.delete_by_id("doc_to_delete")
        
        # Verify collection.delete was called via mock_calls
        delete_calls = [c for c in vector_store.collection._mock_calls if c[0] == 'delete']
        assert len(delete_calls) >= 1


class TestCount:
    """Tests for count() method."""
    
    def test_count_returns_integer(self, vector_store):
        """count() returns an integer."""
        result = vector_store.count()
        assert isinstance(result, int)
    
    def test_count_after_adding_documents(self, vector_store):
        """count() reflects added documents."""
        doc = KGDocument(id="doc1", content="Content 1")
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        assert vector_store.count() >= 1


class TestGetStats:
    """Tests for get_stats() method."""
    
    def test_get_stats_returns_dict(self, vector_store):
        """get_stats() returns a dictionary."""
        stats = vector_store.get_stats()
        assert isinstance(stats, dict)
    
    def test_get_stats_contains_required_fields(self, vector_store):
        """get_stats() contains expected fields."""
        stats = vector_store.get_stats()
        
        assert "collection_name" in stats
        assert "dimension" in stats
        assert "document_count" in stats
        assert "persist_dir" in stats
    
    def test_get_stats_values(self, vector_store):
        """get_stats() returns correct values."""
        stats = vector_store.get_stats()
        
        assert stats["collection_name"] == "math_knowledge"
        assert stats["dimension"] == 1024
        assert isinstance(stats["document_count"], int)


class TestGetById:
    """Tests for get_by_id() method."""
    
    def test_get_by_id_returns_kgchunk_when_found(self, vector_store):
        """get_by_id() returns KGChunk if document exists."""
        doc = KGDocument(
            id="find_me",
            content="This is the content",
            metadata={"type": "kp"}
        )
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        chunk = vector_store.get_by_id("find_me")
        
        assert chunk is not None
        assert isinstance(chunk, KGChunk)
        assert chunk.id == "find_me"
        assert chunk.content == "This is the content"
    
    def test_get_by_id_returns_none_when_not_found(self, vector_store):
        """get_by_id() returns None if document doesn't exist."""
        chunk = vector_store.get_by_id("nonexistent_id")
        assert chunk is None


class TestDocumentConversions:
    """Tests for document conversion helpers."""
    
    def test_document_to_chroma(self, vector_store):
        """_document_to_chroma() returns correct tuple."""
        doc = KGDocument(
            id="test_doc",
            content="Test content",
            metadata={"key": "value"}
        )
        embedding = [0.1] * 1024
        
        result = vector_store._document_to_chroma(doc, embedding)
        
        assert result[0] == "test_doc"
        assert result[1] == embedding
        assert result[2] == "Test content"
        assert result[3] == {"key": "value"}
    
    def test_chroma_to_chunk(self, vector_store):
        """_chroma_to_chunk() converts ChromaDB format to KGChunk."""
        chroma_doc = {
            "id": "chunk_123",
            "document": "Converted content",
            "metadata": {"type": "method"}
        }
        distance = 0.4  # Lower distance = higher similarity
        
        chunk = vector_store._chroma_to_chunk(chroma_doc, distance)
        
        assert isinstance(chunk, KGChunk)
        assert chunk.id == "chunk_123"
        assert chunk.content == "Converted content"
        assert chunk.metadata["type"] == "method"
        # Similarity = 1.0 - distance (direct conversion)
        assert chunk.similarity == 0.6
    
    def test_chroma_to_chunk_handles_none_distance(self, vector_store):
        """_chroma_to_chunk() handles None distance."""
        chroma_doc = {"id": "c1", "document": "content"}
        
        chunk = vector_store._chroma_to_chunk(chroma_doc, None)
        
        assert chunk.similarity == 0.0


class TestReset:
    """Tests for reset() method."""
    
    def test_reset_is_equivalent_to_delete_all(self, vector_store):
        """reset() calls delete_all()."""
        doc = KGDocument(id="doc1", content="Content 1")
        vector_store.add_documents([doc], [[0.1] * 1024])
        
        vector_store.reset()
        
        # Verify collection.delete was called via mock_calls
        delete_calls = [c for c in vector_store.collection._mock_calls if c[0] == 'delete']
        assert len(delete_calls) >= 1
