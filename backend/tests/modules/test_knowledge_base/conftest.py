"""Pytest fixtures and stubs for knowledge_base module tests."""
import sys
import os
import tempfile
import types
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Set environment variables BEFORE any imports
os.environ["DASHSCOPE_API_KEY"] = "test-key-for-unit-tests"

# Create temp directory for chromadb persist
_temp_dir = tempfile.mkdtemp()
os.environ["CHROMA_PERSIST_DIR"] = _temp_dir


# =============================================================================
# Stub chromadb module
# =============================================================================
class MockChromaCollection:
    """Mock ChromaDB collection."""
    
    def __init__(self):
        self._data = {}
        self._mock_calls = []  # Track calls for assertions
    
    def add(self, ids, embeddings, documents, metadatas):
        self._mock_calls.append(('add', ids, embeddings, documents, metadatas))
        for i, doc_id in enumerate(ids):
            self._data[doc_id] = {
                "id": doc_id,
                "embedding": embeddings[i] if i < len(embeddings) else None,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            }
    
    def query(self, query_embeddings, n_results=3, where=None, include=None):
        self._mock_calls.append(('query', query_embeddings, n_results, where, include))
        if not query_embeddings or len(query_embeddings) == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        query_emb = query_embeddings[0]
        
        # ChromaDB returns lists of lists for each query embedding
        results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # Sort by mock similarity (just return in order)
        items = list(self._data.values())[:n_results]
        for i, item in enumerate(items):
            results["ids"][0].append(item["id"])
            results["documents"][0].append(item["document"])
            results["metadatas"][0].append(item["metadata"])
            results["distances"][0].append(0.5 - (i * 0.1))  # Mock distances decreasing
        
        return results
    
    def get(self, ids, include=None):
        self._mock_calls.append(('get', ids, include))
        results = {"ids": [], "documents": [], "metadatas": []}
        for doc_id in ids:
            if doc_id in self._data:
                results["ids"].append(self._data[doc_id]["id"])
                results["documents"].append(self._data[doc_id]["document"])
                results["metadatas"].append(self._data[doc_id]["metadata"])
        return results
    
    def delete(self, where=None, ids=None):
        self._mock_calls.append(('delete', where, ids))
        if ids:
            for doc_id in ids:
                self._data.pop(doc_id, None)
        elif where == {}:
            self._data.clear()
    
    def count(self):
        return len(self._data)
    
    def peek(self, limit=10):
        items = list(self._data.values())[:limit]
        return {
            "ids": [item["id"] for item in items],
            "documents": [item["document"] for item in items],
            "metadatas": [item["metadata"] for item in items],
        }


class MockChromaClient:
    """Mock ChromaDB PersistentClient."""
    
    def __init__(self, path=None, settings=None):
        self._collection = MockChromaCollection()
    
    def get_or_create_collection(self, name=None, metadata=None):
        return self._collection
    
    def get_collection(self, name=None):
        return self._collection


class MockChromaSettings:
    """Mock ChromaDB Settings."""
    def __init__(self, anonymized_telemetry=False, allow_reset=True):
        pass


# Create stub chromadb module
stub_chromadb = types.ModuleType('chromadb')
stub_chromadb.PersistentClient = MockChromaClient
stub_chromadb.ClientAPI = type('ClientAPI', (), {})
stub_chromadb.config = types.ModuleType('chromadb.config')
stub_chromadb.config.Settings = MockChromaSettings
sys.modules['chromadb'] = stub_chromadb
sys.modules['chromadb.config'] = stub_chromadb.config


# =============================================================================
# Stub pdfplumber module
# =============================================================================
class MockPDFPage:
    """Mock PDF page."""
    def __init__(self, text):
        self.text = text
    
    def extract_text(self):
        return self.text


class MockPDF:
    """Mock PDF object."""
    def __init__(self, pages_texts):
        self.pages = [MockPDFPage(text) for text in pages_texts]
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


def mock_pdfplumber_open(path):
    """Mock pdfplumber.open that returns sample text."""
    return MockPDF([
        "这是第一页的内容。包含一些数学知识点。",
        "第二页继续讲解解题方法。",
        "第三页是典型例题和解答。"
    ])


stub_pdfplumber = types.ModuleType('pdfplumber')
stub_pdfplumber.open = mock_pdfplumber_open
sys.modules['pdfplumber'] = stub_pdfplumber


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def temp_persist_dir():
    """Return a temporary directory for ChromaDB persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def embedder():
    """DashScopeEmbeddingClient instance with mocked HTTP."""
    from unittest.mock import AsyncMock, patch
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1024, "index": 0}],
            "usage": {"total_tokens": 10}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        from app.modules.knowledge_base.embedder import DashScopeEmbeddingClient
        embedder = DashScopeEmbeddingClient(api_key="test-key")
        yield embedder


@pytest.fixture
def mock_embedder():
    """Mock embedder that returns fake embeddings."""
    from unittest.mock import AsyncMock
    
    mock = AsyncMock()
    mock.embed.return_value = [[0.1] * 1024]
    mock.aembed.return_value = [[0.1] * 1024]
    return mock


@pytest.fixture
def vector_store(temp_persist_dir):
    """ChromaDBVectorStore instance with mocked ChromaDB."""
    from app.modules.knowledge_base.vector_store import ChromaDBVectorStore
    # Use the pre-stubbed chromadb which uses MockChromaClient
    store = ChromaDBVectorStore(persist_dir=temp_persist_dir)
    yield store


@pytest.fixture
def mock_vector_store():
    """Mock ChromaDBVectorStore for testing."""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    mock.add_documents = MagicMock()
    mock.similarity_search = MagicMock(return_value=[])
    mock.delete_all = MagicMock()
    mock.count = MagicMock(return_value=0)
    mock.get_stats = MagicMock(return_value={
        "collection_name": "math_knowledge",
        "dimension": 1024,
        "document_count": 0,
        "persist_dir": "/tmp/test",
        "has_documents": False,
    })
    return mock


@pytest.fixture
def ingestion_pipeline(mock_embedder, mock_vector_store):
    """IngestionPipeline instance with mocked dependencies."""
    from app.modules.knowledge_base.ingestion import IngestionPipeline
    pipeline = IngestionPipeline(
        vector_store=mock_vector_store,
        embedder=mock_embedder
    )
    return pipeline


@pytest.fixture
def rag_service(mock_embedder, mock_vector_store):
    """RAGService instance with mocked dependencies."""
    from app.modules.knowledge_base.service import RAGService
    service = RAGService(
        vector_store=mock_vector_store,
        embedder=mock_embedder
    )
    return service
