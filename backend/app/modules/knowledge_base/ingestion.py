"""Ingestion Pipeline for PDF document processing.

This module provides a pipeline for extracting text from PDFs,
chunking the text into manageable pieces, and ingesting them
into the vector store.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import KGDocument, DocumentType, KGError
from .vector_store import ChromaDBVectorStore
from .embedder import DashScopeEmbeddingClient

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Pipeline for ingesting PDF documents into the knowledge base.
    
    Processes PDF files through extraction, chunking, embedding,
    and storage stages.
    
    Attributes:
        CHUNK_SIZE: Target size for text chunks (in characters).
        OVERLAP: Overlap between adjacent chunks.
    """
    
    CHUNK_SIZE = 400
    OVERLAP = 50
    
    def __init__(
        self,
        vector_store: ChromaDBVectorStore,
        embedder: DashScopeEmbeddingClient
    ):
        """Initialize the ingestion pipeline.
        
        Args:
            vector_store: ChromaDB vector store instance.
            embedder: DashScope embedding client instance.
        """
        self.vector_store = vector_store
        self.embedder = embedder
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from a PDF file using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file.
        
        Returns:
            Extracted text content.
        
        Raises:
            KGError: If PDF extraction fails.
        """
        try:
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
            
        except ImportError:
            raise KGError(
                "pdfplumber is required for PDF extraction. "
                "Install with: pip install pdfplumber"
            )
        except Exception as e:
            raise KGError(f"Failed to extract text from PDF: {e}")
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = OVERLAP
    ) -> List[str]:
        """Split text into overlapping chunks.
        
        Prefers paragraph/sentence boundaries for natural splits.
        
        Args:
            text: Text to chunk.
            chunk_size: Target chunk size in characters.
            overlap: Overlap between chunks.
        
        Returns:
            List of text chunks.
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # Try to split by paragraphs first
        # Paragraphs are separated by double newlines or single newlines with space
        para_pattern = r'\n\s*\n|\n'
        paragraphs = re.split(para_pattern, text)
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If single paragraph exceeds chunk_size, split by sentences
            if len(para) > chunk_size:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Split by sentence-ending punctuation
                sentence_pattern = r'([。！？；\.\!\?\;])'
                sentences = re.split(sentence_pattern, para)
                
                # Recombine sentences with their punctuation
                combined_sentences = []
                for i in range(0, len(sentences) - 1, 2):
                    if i + 1 < len(sentences):
                        combined_sentences.append(sentences[i] + sentences[i + 1])
                    else:
                        combined_sentences.append(sentences[i])
                
                current_chunk = ""
                for sentence in combined_sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) <= chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        # Start new chunk with overlap
                        overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                        current_chunk = overlap_text + sentence + " "
                
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If adding this paragraph exceeds chunk_size
            elif len(current_chunk) + len(para) > chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + para + "\n\n"
            else:
                current_chunk += para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Filter out empty or very short chunks
        chunks = [c for c in chunks if len(c) >= 50]
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _generate_id(self, content: str, doc_type: Optional[str] = None) -> str:
        """Generate a deterministic ID from content hash.
        
        Args:
            content: Content to hash.
            doc_type: Optional document type prefix.
        
        Returns:
            SHA256-based ID string.
        """
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if doc_type:
            return f"{doc_type}_{content_hash}"
        return content_hash
    
    def _prepare_metadata(
        self,
        base_metadata: dict,
        chunk_index: int,
        total_chunks: int
    ) -> dict:
        """Prepare metadata for a chunk.
        
        Args:
            base_metadata: Base metadata from file.
            chunk_index: Index of this chunk.
            total_chunks: Total number of chunks.
        
        Returns:
            Metadata dictionary for the chunk.
        """
        metadata = base_metadata.copy()
        metadata["chunk_index"] = chunk_index
        metadata["total_chunks"] = total_chunks
        return metadata
    
    async def ingest_file(
        self,
        file_path: str,
        metadata: dict
    ) -> Dict[str, Any]:
        """Ingest a single PDF file into the knowledge base.
        
        Extracts text, chunks it, embeds, and stores in ChromaDB.
        
        Args:
            file_path: Path to the PDF file.
            metadata: Metadata dictionary containing:
                - type: Document type (knowledge_point, method, etc.)
                - name: Document name
                - keywords: List of keywords
                - grade: Grade level (default: high_school)
                - difficulty: easy/medium/hard
        
        Returns:
            Dictionary with status, chunk count, and first doc ID.
        
        Raises:
            KGError: If ingestion fails.
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise KGError(f"File not found: {file_path}")
        
        if file_path_obj.suffix.lower() != ".pdf":
            raise KGError(f"Only PDF files are supported: {file_path}")
        
        logger.info(f"Starting ingestion of {file_path}")
        
        try:
            # Stage 1: Extract text from PDF
            text = self._extract_text(file_path)
            
            if not text or not text.strip():
                raise KGError(f"Failed to extract text from {file_path}")
            
            # Stage 2: Chunk the text
            chunks = self._chunk_text(text)
            
            if not chunks:
                raise KGError(f"No valid chunks extracted from {file_path}")
            
            logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
            
            # Stage 3: Create KGDocument objects
            doc_type = metadata.get("type", "knowledge_point")
            
            documents = []
            for i, chunk_content in enumerate(chunks):
                chunk_metadata = self._prepare_metadata(metadata, i, len(chunks))
                chunk_id = self._generate_id(chunk_content, doc_type)
                
                doc = KGDocument(
                    id=chunk_id,
                    content=chunk_content,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            # Stage 4: Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} chunks...")
            embeddings = await self.embedder.aembed(
                [doc.content for doc in documents]
            )
            
            # Stage 5: Store in ChromaDB
            self.vector_store.add_documents(documents, embeddings)
            
            logger.info(
                f"Successfully ingested {file_path}: "
                f"{len(documents)} chunks created"
            )
            
            return {
                "status": "success",
                "file": str(file_path),
                "chunks": len(documents),
                "doc_id": documents[0].id if documents else None,
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed for {file_path}: {e}")
            raise KGError(f"Ingestion failed: {e}")
    
    # =========================================================================
    # Markdown Ingestion Methods
    # =========================================================================
    
    def _clean_markdown(self, text: str) -> str:
        """Clean special markers from markdown text.
        
        Removes or replaces:
        - [图形start]...[图形end] markers with descriptive text
        - [思路提示start]...[思路提示end] markers with text
        
        Args:
            text: Raw markdown text.
        
        Returns:
            Cleaned markdown text.
        """
        import re as _re
        
        # Replace [图形start]...[图形end] with [图片]
        text = _re.sub(
            r'\[图形start\](.*?)\[图形end]',
            r'[图片：\1]',
            text,
            flags=_re.DOTALL
        )
        
        # Replace [思路提示start]...[思路提示end] with [提示：...]
        text = _re.sub(
            r'\[思路提示start\](.*?)\[思路提示end]',
            r'[解题提示：\1]',
            text,
            flags=_re.DOTALL
        )
        
        # Clean up multiple blank lines
        text = _re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _chunk_markdown(
        self,
        text: str,
        chunk_size: int = 400,
        overlap: int = 50
    ) -> List[str]:
        """Split markdown text into chunks preserving structure.
        
        Strategy:
        1. Split by ## modules first
        2. Within each module, split by ### 类型 headers
           Each ### 类型 section = one semantic chunk (类型 + 所有例题 + 解析保持在一起)
           内容提要/例/反思/变式 are NOT split boundaries — they stay in the type chunk
        3. Only split by paragraphs when a type section exceeds chunk_size * 4
        
        Args:
            text: Markdown text.
            chunk_size: Target chunk size (default: 400).
            overlap: Overlap between chunks (default: 50).
        
        Returns:
            List of text chunks.
        """
        import re as _re
        
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks: List[str] = []
        
        # Split by ## modules first
        module_parts = _re.split(r'\n(?=## )', text)
        
        for module_part in module_parts:
            module_part = module_part.strip()
            if not module_part:
                continue
            
            # Extract ## module header
            module_header = ""
            if module_part.startswith('## '):
                header_end = module_part.find('\n')
                if header_end > 0:
                    module_header = module_part[:header_end]
                    module_content = module_part[header_end + 1:].strip()
                else:
                    module_content = module_part[len('## '):].strip()
            else:
                module_content = module_part
            
            if not module_content:
                continue
            
            # Split module content by ### 类型 headers
            type_pattern = r'\n(?=### 类型[^\n]*)'
            type_parts = _re.split(type_pattern, module_content)
            
            for type_part in type_parts:
                type_part = type_part.strip()
                if not type_part:
                    continue
                
                # Extract type header and content
                type_header = ""
                if type_part.startswith('### 类型'):
                    header_end = type_part.find('\n')
                    if header_end > 0:
                        type_header = type_part[:header_end]
                        type_content = type_part[header_end + 1:].strip()
                    else:
                        type_content = type_part[len('### 类型'):].strip()
                        type_header = '### 类型' + type_content.split('\n')[0] if type_content else ""
                        type_content = type_part
                        type_header = ""
                else:
                    type_content = type_part
                
                # Build chunk: module_header + type_header + content
                def make_chunk(h: str, c: str, m: str) -> str:
                    parts = []
                    if m:
                        parts.append(m)
                    if h:
                        parts.append(h)
                    if c:
                        parts.append(c)
                    return '\n'.join(parts)
                
                full = make_chunk(type_header, type_content, module_header)
                
                # If small enough, keep as one chunk
                if len(full) <= chunk_size * 4:
                    chunks.append(full)
                else:
                    # Split large content by paragraphs
                    paras = _re.split(r'\n\n+', type_content)
                    cur = ""
                    for p in paras:
                        p = p.strip()
                        if not p:
                            continue
                        entry = (type_header + "\n" + p) if type_header else p
                        if len(entry) <= chunk_size:
                            if len(cur) + len(entry) + 1 <= chunk_size:
                                cur += entry + "\n\n"
                            else:
                                if cur.strip():
                                    chunks.append(make_chunk("", cur.strip(), module_header))
                                cur = entry + "\n\n"
                        else:
                            if cur.strip():
                                chunks.append(make_chunk("", cur.strip(), module_header))
                            cur = ""
                            # Split by sentences for very long paragraphs
                            sents = _re.split(r'([。！？\.\!\?])', p)
                            comb = []
                            for i in range(0, len(sents) - 1, 2):
                                comb.append(sents[i] + (sents[i + 1] if i + 1 < len(sents) else ''))
                            if len(sents) % 2 == 1 and sents[-1].strip():
                                comb.append(sents[-1])
                            for s in comb:
                                s = s.strip()
                                if not s:
                                    continue
                                sent_entry = s
                                if type_header:
                                    sent_entry = type_header + "\n" + s
                                if len(cur) + len(sent_entry) + 1 <= chunk_size:
                                    cur += sent_entry + " "
                                else:
                                    if cur.strip():
                                        chunks.append(make_chunk("", cur.strip(), module_header))
                                    ov = cur[-overlap:].strip() if len(cur) > overlap else ""
                                    cur = (ov + " " + sent_entry).strip() + " "
                    if cur.strip():
                        chunks.append(make_chunk("", cur.strip(), module_header))
        
        # Filter very short chunks
        chunks = [c for c in chunks if len(c) >= 50]
        
        logger.debug(f"Split markdown into {len(chunks)} chunks")
        return chunks
    
    def _extract_markdown_structure(self, text: str) -> dict:
        """Extract structural metadata from markdown.
        
        Parses #, ##, ### headers to build chapter/module/type hierarchy.
        
        Args:
            text: Cleaned markdown text.
        
        Returns:
            dict with chapter, module, type fields (all optional str).
        """
        import re as _re
        
        result = {"chapter": "", "module": "", "type": ""}
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('# ') and not result["chapter"]:
                result["chapter"] = line[2:].strip()
            elif line.startswith('## ') and not result["module"]:
                result["module"] = line[3:].strip()
            elif line.startswith('### 类型') and not result["type"]:
                result["type"] = line[4:].strip()
                break  # type found, stop scanning
        
        return result
    
    async def ingest_markdown(
        self,
        file_path: str,
        metadata: dict
    ) -> Dict[str, Any]:
        """Ingest a single Markdown file into the knowledge base.
        
        Args:
            file_path: Path to the Markdown file.
            metadata: Metadata dictionary containing:
                - type: Document type (knowledge_point, method, etc.)
                - name: Document name
                - keywords: List of keywords
                - grade: Grade level
                - difficulty: easy/medium/hard
        
        Returns:
            Dictionary with status, chunk count, and first doc ID.
        
        Raises:
            KGError: If ingestion fails.
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise KGError(f"File not found: {file_path}")
        
        if file_path_obj.suffix.lower() != ".md":
            raise KGError(f"Only Markdown files are supported: {file_path}")
        
        import re as _re

        logger.info(f"Starting markdown ingestion of {file_path}")
        
        try:
            # Stage 1: Read and clean markdown
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            text = self._clean_markdown(text)
            
            if not text or not text.strip():
                raise KGError(f"Empty or invalid markdown file: {file_path}")
            
            # Stage 1b: Extract structural metadata from first headers
            structure = self._extract_markdown_structure(text)
            
            # Stage 2: Chunk the markdown
            chunks = self._chunk_markdown(text)
            
            if not chunks:
                raise KGError(f"No valid chunks extracted from {file_path}")
            
            logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
            
            # Stage 3: Create KGDocument objects
            doc_type = metadata.get("type", "knowledge_point")
            
            documents = []
            for i, chunk_content in enumerate(chunks):
                chunk_metadata = self._prepare_metadata(metadata, i, len(chunks))
                chunk_metadata["chapter"] = structure.get("chapter", "")
                chunk_metadata["module"] = structure.get("module", "")
                # Extract type from chunk content if present
                type_match = _re.search(r'^### (.+)$', chunk_content, _re.MULTILINE)
                if type_match:
                    chunk_metadata["type"] = type_match.group(1).strip()
                chunk_id = self._generate_id(chunk_content, doc_type)
                
                doc = KGDocument(
                    id=chunk_id,
                    content=chunk_content,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            # Stage 4: Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} chunks...")
            embeddings = await self.embedder.aembed(
                [doc.content for doc in documents]
            )
            
            # Stage 5: Store in ChromaDB
            self.vector_store.add_documents(documents, embeddings)
            
            logger.info(
                f"Successfully ingested markdown {file_path}: "
                f"{len(documents)} chunks created"
            )
            
            return {
                "status": "success",
                "file": str(file_path),
                "chunks": len(documents),
                "doc_id": documents[0].id if documents else None,
            }
            
        except KGError:
            raise
        except Exception as e:
            logger.error(f"Markdown ingestion failed for {file_path}: {e}")
            raise KGError(f"Markdown ingestion failed: {e}")
    
    async def ingest_directory(
        self,
        dir_path: str,
        file_type: str = "knowledge_point",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """Ingest all PDF files in a directory.
        
        Args:
            dir_path: Path to directory containing PDF files.
            file_type: Default document type for files.
            recursive: Whether to search subdirectories.
        
        Returns:
            List of ingestion results for each file.
        
        Raises:
            KGError: If directory processing fails.
        """
        dir_path_obj = Path(dir_path)
        
        if not dir_path_obj.exists() or not dir_path_obj.is_dir():
            raise KGError(f"Directory not found: {dir_path}")
        
        # Find all PDF files
        if recursive:
            pdf_files = list(dir_path_obj.rglob("*.pdf"))
        else:
            pdf_files = list(dir_path_obj.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {dir_path}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files in {dir_path}")
        
        results = []
        errors = []
        
        for pdf_file in pdf_files:
            try:
                metadata = {
                    "type": file_type,
                    "name": pdf_file.stem,  # filename without extension
                    "keywords": [],
                    "grade": "high_school",
                    "difficulty": "medium",
                    "source_file": str(pdf_file),
                }
                
                result = await self.ingest_file(str(pdf_file), metadata)
                results.append(result)
                
            except Exception as e:
                error_msg = f"Failed to ingest {pdf_file}: {e}"
                logger.error(error_msg)
                errors.append({"file": str(pdf_file), "error": str(e)})
                results.append({
                    "status": "error",
                    "file": str(pdf_file),
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        logger.info(
            f"Directory ingestion complete: {success_count}/{len(results)} succeeded"
        )
        
        return results
    
    async def ingest_text_content(
        self,
        content: str,
        metadata: dict
    ) -> Dict[str, Any]:
        """Ingest raw text content directly.
        
        Useful for testing or when content is already available.
        
        Args:
            content: Text content to ingest.
            metadata: Metadata dictionary.
        
        Returns:
            Ingestion result dictionary.
        """
        try:
            # Chunk the text
            chunks = self._chunk_text(content)
            
            if not chunks:
                raise KGError("No valid chunks extracted from content")
            
            # Create documents
            doc_type = metadata.get("type", "knowledge_point")
            
            documents = []
            for i, chunk_content in enumerate(chunks):
                chunk_metadata = self._prepare_metadata(metadata, i, len(chunks))
                chunk_id = self._generate_id(chunk_content, doc_type)
                
                doc = KGDocument(
                    id=chunk_id,
                    content=chunk_content,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            # Generate embeddings
            embeddings = await self.embedder.aembed(
                [doc.content for doc in documents]
            )
            
            # Store
            self.vector_store.add_documents(documents, embeddings)
            
            return {
                "status": "success",
                "chunks": len(documents),
                "doc_id": documents[0].id if documents else None,
            }
            
        except Exception as e:
            raise KGError(f"Text ingestion failed: {e}")
