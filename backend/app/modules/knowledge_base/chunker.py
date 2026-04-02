"""Markdown-aware text chunker for OCR output.

Designed for markdown text with LaTeX formulas ($...$ and $$...$$).
Preserves structural units: headers, formulas, paragraphs.
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class MarkdownChunker:
    """Splits markdown text into chunks while preserving structure.
    
    Strategy:
    1. Extract all LaTeX expressions first (inline $...$ and display $$...$$)
    2. Split on ## headers (section boundaries)
    3. Split remaining blocks by paragraphs (\n\n)
    4. For each block, try to respect chunk_size
    5. Within blocks, split by sentences or lines
    
    Attributes:
        chunk_size: Target chunk size in characters.
        overlap: Overlap between chunks.
    """
    
    # Patterns for LaTeX expressions
    DISPLAY_MATH_PATTERN = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
    INLINE_MATH_PATTERN = re.compile(r'\$(.+?)\$', re.DOTALL)
    
    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        """Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters (default: 400).
            overlap: Overlap between chunks for context continuity (default: 50).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def _split_by_headers(self, text: str) -> List[Tuple[str, str]]:
        """Split text by ## headers.
        
        Args:
            text: Markdown text.
        
        Returns:
            List of (header, content) tuples. Header includes "## ".
            First element may have empty header if text starts without header.
        """
        sections: List[Tuple[str, str]] = []
        
        # Split keeping the header
        parts = re.split(r'\n(?=## )', text)
        
        current_header = ""
        current_content = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith("## "):
                # Save previous section
                if current_content:
                    sections.append((current_header, current_content))
                # Start new section
                header_end = part.index("\n")
                if header_end == -1:
                    current_header = part
                    current_content = ""
                else:
                    current_header = part[:header_end]
                    current_content = part[header_end + 1:].strip()
            else:
                # Continuation of current section
                if current_content:
                    current_content += "\n" + part
                else:
                    current_content = part
        
        # Don't forget the last section
        if current_content:
            sections.append((current_header, current_content))
        
        return sections
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by double newlines (paragraphs)."""
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_block(self, text: str) -> List[str]:
        """Split a block of text into sub-chunks respecting size limits.
        
        Prefers splitting at sentence boundaries (。！？.\n) 
        or line boundaries.
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks: List[str] = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find a good split point in the last 20% of the chunk
            search_start = start + int(self.chunk_size * 0.7)
            search_text = text[search_start:end]
            
            # Look for sentence-ending punctuation or newlines
            split_match = re.search(r'([。！？\n]|[\.!?]\s)', search_text)
            
            if split_match:
                split_pos = search_start + split_match.end()
                chunks.append(text[start:split_pos])
                start = split_pos
            else:
                # Hard split at chunk boundary
                chunks.append(text[start:end])
                start = end - self.overlap  # Overlap for continuity
        
        return chunks
    
    def chunk(self, text: str) -> List[str]:
        """Split markdown text into chunks.
        
        Args:
            text: Markdown text (from OCR output).
        
        Returns:
            List of text chunks.
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # Split by ## headers first
        sections = self._split_by_headers(text)
        
        all_chunks: List[str] = []
        
        for header, content in sections:
            if not content:
                continue
            
            # Split content by paragraphs
            paragraphs = self._split_by_paragraphs(content)
            
            for para in paragraphs:
                if not para:
                    continue
                
                # If paragraph is small enough, keep it
                if len(para) <= self.chunk_size:
                    chunk_text = para
                    if header:
                        chunk_text = header + "\n" + chunk_text
                    all_chunks.append(chunk_text)
                else:
                    # Split large paragraph
                    sub_chunks = self._split_block(para)
                    for i, sub in enumerate(sub_chunks):
                        chunk_text = sub
                        if header:
                            chunk_text = header + "\n" + chunk_text
                        all_chunks.append(chunk_text)
        
        return all_chunks


def chunk_markdown(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Convenience function to chunk markdown text.
    
    Args:
        text: Markdown text to chunk.
        chunk_size: Target chunk size (default: 400).
        overlap: Overlap between chunks (default: 50).
    
    Returns:
        List of text chunks.
    """
    chunker = MarkdownChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk(text)
