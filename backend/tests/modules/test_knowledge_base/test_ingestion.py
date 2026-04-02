"""Tests for IngestionPipeline."""
import pytest
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.modules.knowledge_base.ingestion import IngestionPipeline
from app.modules.knowledge_base.models import KGDocument, KGError


class TestIngestionPipelineInit:
    """Tests for IngestionPipeline initialization."""
    
    def test_init_requires_vector_store_and_embedder(self, mock_embedder, mock_vector_store):
        """Pipeline initializes with vector_store and embedder."""
        pipeline = IngestionPipeline(
            vector_store=mock_vector_store,
            embedder=mock_embedder
        )
        
        assert pipeline.vector_store is mock_vector_store
        assert pipeline.embedder is mock_embedder
    
    def test_chunk_size_is_400(self, mock_embedder, mock_vector_store):
        """Default CHUNK_SIZE is 400 characters."""
        pipeline = IngestionPipeline(
            vector_store=mock_vector_store,
            embedder=mock_embedder
        )
        assert pipeline.CHUNK_SIZE == 400
    
    def test_overlap_is_50(self, mock_embedder, mock_vector_store):
        """Default OVERLAP is 50 characters."""
        pipeline = IngestionPipeline(
            vector_store=mock_vector_store,
            embedder=mock_embedder
        )
        assert pipeline.OVERLAP == 50


class TestExtractText:
    """Tests for _extract_text() method."""
    
    def test_extract_text_returns_string(self, ingestion_pipeline):
        """_extract_text() returns extracted text string."""
        with patch('pdfplumber.open') as mock_pdf:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "第一页文字"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "第二页文字"
            
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page1, mock_page2]
            
            result = ingestion_pipeline._extract_text("/fake/path.pdf")
            
            assert isinstance(result, str)
            assert "第一页文字" in result
            assert "第二页文字" in result
    
    def test_extract_text_joins_pages_with_double_newline(self, ingestion_pipeline):
        """_extract_text() joins page texts with double newline."""
        with patch('pdfplumber.open') as mock_pdf:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2"
            
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page1, mock_page2]
            
            result = ingestion_pipeline._extract_text("/fake/path.pdf")
            
            assert "Page 1\n\nPage 2" == result
    
    def test_extract_text_skips_empty_pages(self, ingestion_pipeline):
        """_extract_text() skips pages with no text."""
        with patch('pdfplumber.open') as mock_pdf:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Has content"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = None
            mock_page3 = MagicMock()
            mock_page3.extract_text.return_value = "More content"
            
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page1, mock_page2, mock_page3]
            
            result = ingestion_pipeline._extract_text("/fake/path.pdf")
            
            assert "Has content" in result
            assert "More content" in result


class TestChunkText:
    """Tests for _chunk_text() method."""
    
    def test_chunk_text_returns_list_of_strings(self, ingestion_pipeline):
        """_chunk_text() returns list of text chunks."""
        long_text = "A" * 1000
        
        result = ingestion_pipeline._chunk_text(long_text)
        
        assert isinstance(result, list)
        assert all(isinstance(c, str) for c in result)
    
    def test_chunk_text_returns_empty_for_empty_input(self, ingestion_pipeline):
        """_chunk_text() returns empty list for empty input."""
        assert ingestion_pipeline._chunk_text("") == []
        assert ingestion_pipeline._chunk_text("   ") == []
        assert ingestion_pipeline._chunk_text(None) == []
    
    def test_chunk_text_respects_target_size(self, ingestion_pipeline):
        """_chunk_text() produces chunks of approximately target size."""
        # Create text that's clearly longer than chunk size
        long_text = "This is a longer piece of text. " * 50
        
        chunks = ingestion_pipeline._chunk_text(long_text, chunk_size=400)
        
        # Most chunks should be around 400 chars (with some tolerance)
        for chunk in chunks[:-1]:  # Last chunk might be smaller
            assert len(chunk) <= 500  # Allow some overflow for natural boundaries
    
    def test_chunk_text_splits_on_paragraph_boundaries(self, ingestion_pipeline):
        """_chunk_text() prefers paragraph boundaries."""
        text = "这是一个很长的第一段内容，包含了很多文字。" * 10 + "\n\n" + \
               "这是第二段内容，同样有很多文字。" * 10 + "\n\n" + \
               "这是第三段内容，继续添加更多文字。" * 10
        
        chunks = ingestion_pipeline._chunk_text(text)
        
        assert len(chunks) >= 1
    
    def test_chunk_text_filters_short_chunks(self, ingestion_pipeline):
        """_chunk_text() filters out chunks shorter than 50 chars."""
        text = "Short." * 5  # Will create very short chunks
        
        chunks = ingestion_pipeline._chunk_text(text)
        
        # All chunks should be at least 50 characters
        for chunk in chunks:
            assert len(chunk) >= 50
    
    def test_chunk_text_with_custom_size(self, ingestion_pipeline):
        """_chunk_text() respects custom chunk_size parameter."""
        text = "A" * 1000
        
        chunks = ingestion_pipeline._chunk_text(text, chunk_size=200)
        
        for chunk in chunks[:-1]:
            assert len(chunk) <= 250


class TestGenerateId:
    """Tests for _generate_id() method."""
    
    def test_generate_id_returns_string(self, ingestion_pipeline):
        """_generate_id() returns a string ID."""
        result = ingestion_pipeline._generate_id("test content")
        assert isinstance(result, str)
    
    def test_generate_id_is_deterministic(self, ingestion_pipeline):
        """_generate_id() generates same ID for same content."""
        content = "test content for hashing"
        
        id1 = ingestion_pipeline._generate_id(content)
        id2 = ingestion_pipeline._generate_id(content)
        
        assert id1 == id2
    
    def test_generate_id_differs_for_different_content(self, ingestion_pipeline):
        """_generate_id() generates different IDs for different content."""
        id1 = ingestion_pipeline._generate_id("content A")
        id2 = ingestion_pipeline._generate_id("content B")
        
        assert id1 != id2
    
    def test_generate_id_with_doc_type_prefix(self, ingestion_pipeline):
        """_generate_id() prepends doc_type when provided."""
        content = "test content"
        
        id_without = ingestion_pipeline._generate_id(content)
        id_with = ingestion_pipeline._generate_id(content, doc_type="method")
        
        assert id_with.startswith("method_")
        assert id_without != id_with
    
    def test_generate_id_uses_sha256_hash(self, ingestion_pipeline):
        """_generate_id() uses first 16 chars of SHA256 hash."""
        content = "specific content"
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        
        result = ingestion_pipeline._generate_id(content)
        
        assert result == expected_hash


class TestPrepareMetadata:
    """Tests for _prepare_metadata() method."""
    
    def test_prepare_metadata_adds_chunk_index(self, ingestion_pipeline):
        """_prepare_metadata() adds chunk_index to metadata."""
        base = {"type": "kp"}
        result = ingestion_pipeline._prepare_metadata(base, chunk_index=2, total_chunks=10)
        
        assert result["chunk_index"] == 2
    
    def test_prepare_metadata_adds_total_chunks(self, ingestion_pipeline):
        """_prepare_metadata() adds total_chunks to metadata."""
        base = {"type": "kp"}
        result = ingestion_pipeline._prepare_metadata(base, chunk_index=0, total_chunks=5)
        
        assert result["total_chunks"] == 5
    
    def test_prepare_metadata_preserves_base_metadata(self, ingestion_pipeline):
        """_prepare_metadata() keeps original metadata fields."""
        base = {"type": "method", "name": "TestMethod", "grade": "high_school"}
        result = ingestion_pipeline._prepare_metadata(base, chunk_index=0, total_chunks=3)
        
        assert result["type"] == "method"
        assert result["name"] == "TestMethod"
        assert result["grade"] == "high_school"
    
    def test_prepare_metadata_does_not_mutate_original(self, ingestion_pipeline):
        """_prepare_metadata() doesn't modify the base metadata."""
        base = {"type": "kp"}
        ingestion_pipeline._prepare_metadata(base, chunk_index=1, total_chunks=5)
        
        assert "chunk_index" not in base


class TestIngestFile:
    """Tests for ingest_file() async method."""
    
    @pytest.mark.asyncio
    async def test_ingest_file_returns_success_dict(self, ingestion_pipeline, tmp_path):
        """ingest_file() returns status dict on success."""
        # Create a fake PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        # Mock _extract_text to return valid long content
        long_text = "这是一段很长的测试内容。" * 50
        with patch.object(ingestion_pipeline, '_extract_text', return_value=long_text):
            metadata = {
                "type": "knowledge_point",
                "name": "Test Doc",
                "keywords": ["test"],
            }
            
            result = await ingestion_pipeline.ingest_file(str(pdf_file), metadata)
            
            assert result["status"] == "success"
            assert "chunks" in result
            assert "doc_id" in result
    
    @pytest.mark.asyncio
    async def test_ingest_file_raises_if_file_not_found(self, ingestion_pipeline):
        """ingest_file() raises KGError if file doesn't exist."""
        with pytest.raises(KGError, match="File not found"):
            await ingestion_pipeline.ingest_file("/nonexistent/file.pdf", {})
    
    @pytest.mark.asyncio
    async def test_ingest_file_raises_if_not_pdf(self, ingestion_pipeline, tmp_path):
        """ingest_file() raises KGError if file is not PDF."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        
        with pytest.raises(KGError, match="Only PDF files"):
            await ingestion_pipeline.ingest_file(str(txt_file), {})
    
    @pytest.mark.asyncio
    async def test_ingest_file_calls_embedder(self, ingestion_pipeline, tmp_path):
        """ingest_file() calls embedder to generate embeddings."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")
        
        long_text = "这是一段很长的测试内容。" * 50
        with patch.object(ingestion_pipeline, '_extract_text', return_value=long_text):
            metadata = {"type": "kp", "name": "Test"}
            
            await ingestion_pipeline.ingest_file(str(pdf_file), metadata)
            
            ingestion_pipeline.embedder.aembed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingest_file_calls_vector_store(self, ingestion_pipeline, tmp_path):
        """ingest_file() stores documents in vector store."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")
        
        long_text = "这是一段很长的测试内容。" * 50
        with patch.object(ingestion_pipeline, '_extract_text', return_value=long_text):
            metadata = {"type": "kp", "name": "Test"}
            
            await ingestion_pipeline.ingest_file(str(pdf_file), metadata)
            
            ingestion_pipeline.vector_store.add_documents.assert_called_once()


class TestIngestTextContent:
    """Tests for ingest_text_content() async method."""
    
    @pytest.mark.asyncio
    async def test_ingest_text_content_returns_success_dict(self, ingestion_pipeline):
        """ingest_text_content() returns success dict."""
        result = await ingestion_pipeline.ingest_text_content(
            content="这是一段很长的测试内容。" * 50,
            metadata={"type": "concept", "name": "测试概念"}
        )
        
        assert result["status"] == "success"
        assert "chunks" in result
        assert "doc_id" in result
    
    @pytest.mark.asyncio
    async def test_ingest_text_content_chunks_text(self, ingestion_pipeline):
        """ingest_text_content() chunks the provided text."""
        long_content = "测试内容. " * 100
        
        result = await ingestion_pipeline.ingest_text_content(
            content=long_content,
            metadata={"type": "method"}
        )
        
        assert result["chunks"] >= 1
    
    @pytest.mark.asyncio
    async def test_ingest_text_content_raises_on_empty_chunks(self, ingestion_pipeline):
        """ingest_text_content() raises KGError if no valid chunks."""
        with pytest.raises(KGError, match="No valid chunks"):
            await ingestion_pipeline.ingest_text_content(
                content="短",
                metadata={"type": "kp"}
            )
    
    @pytest.mark.asyncio
    async def test_ingest_text_content_generates_embeddings(self, ingestion_pipeline):
        """ingest_text_content() calls embedder for embeddings."""
        await ingestion_pipeline.ingest_text_content(
            content="这是一段很长的测试内容。" * 50,
            metadata={"type": "kp"}
        )
        
        ingestion_pipeline.embedder.aembed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingest_text_content_stores_documents(self, ingestion_pipeline):
        """ingest_text_content() stores documents in vector store."""
        await ingestion_pipeline.ingest_text_content(
            content="这是一段很长的测试内容。" * 50,
            metadata={"type": "kp"}
        )
        
        ingestion_pipeline.vector_store.add_documents.assert_called_once()


class TestIngestDirectory:
    """Tests for ingest_directory() async method."""
    
    @pytest.mark.asyncio
    async def test_ingest_directory_returns_list_of_results(self, ingestion_pipeline, tmp_path):
        """ingest_directory() returns list of ingestion results."""
        # Create a subdirectory with a PDF
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "doc1.pdf").write_bytes(b"fake pdf 1")
        (pdf_dir / "doc2.pdf").write_bytes(b"fake pdf 2")
        
        results = await ingestion_pipeline.ingest_directory(str(pdf_dir))
        
        assert isinstance(results, list)
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_ingest_directory_returns_empty_if_no_pdfs(self, ingestion_pipeline, tmp_path):
        """ingest_directory() returns empty list if no PDFs found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        results = await ingestion_pipeline.ingest_directory(str(empty_dir))
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_ingest_directory_handles_non_recursive(self, ingestion_pipeline, tmp_path):
        """ingest_directory() can search non-recursively."""
        # Create subdir with PDF
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        (sub_dir / "nested.pdf").write_bytes(b"fake")
        
        # Without recursive=True, should not find nested PDF
        results = await ingestion_pipeline.ingest_directory(str(tmp_path), recursive=False)
        
        assert len(results) == 0
