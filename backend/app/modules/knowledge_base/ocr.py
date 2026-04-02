"""SimpleTex OCR Client for document image recognition.

Handles PDF pages rendered as images via SimpleTex API
(https://server.simpletex.cn/api/simpletex_ocr) for:
- Chinese/English text recognition
- LaTeX formula extraction
- Markdown-formatted output
"""

import io
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

import fitz
from PIL import Image
import requests
import urllib3

from app.modules.knowledge_base.models import KGError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


@dataclass
class OcrResult:
    """Result of a single page OCR operation."""
    page_index: int
    markdown: str
    request_id: str


class SimpleTexOcrClient:
    """Client for SimpleTex document OCR API.
    
    Supports:
    - Chinese and English text recognition (80+ languages)
    - LaTeX formulas (symbols, matrices, equations)
    - Mixed text and formula layouts
    - Document pages, double-column layouts
    
    Attributes:
        api_url: SimpleTex API endpoint URL
        token: User Authorization Token
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
    """
    
    API_URL = "https://server.simpletex.cn/api/simpletex_ocr"
    REC_MODES = ["auto", "document", "formula"]
    
    def __init__(
        self,
        token: str,
        api_url: Optional[str] = None,
        timeout: int = 120,
        verify_ssl: bool = False,
    ):
        """Initialize SimpleTex OCR client.
        
        Args:
            token: SimpleTex UAT token.
            api_url: Custom API URL (optional).
            timeout: Request timeout in seconds (default: 120).
            verify_ssl: Whether to verify SSL (default: False).
        
        Raises:
            ValueError: If token is empty.
        """
        if not token:
            raise ValueError("SimpleTex token is required")
        
        self.token = token
        self.api_url = api_url or self.API_URL
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self._session = requests.Session()
        self._session.verify = verify_ssl
        
        logger.info(f"SimpleTexOcrClient initialized (url={self.api_url})")
    
    def _render_page_to_image(
        self,
        pdf_path: str,
        page_index: int,
        dpi: int = 150,
    ) -> Tuple[bytes, Tuple[int, int]]:
        """Render a PDF page to PNG image.
        
        Args:
            pdf_path: Path to the PDF file.
            page_index: 0-based page index.
            dpi: Rendering DPI (default: 150).
        
        Returns:
            Tuple of (PNG bytes, (width, height)).
        
        Raises:
            KGError: If PDF cannot be opened or page doesn't exist.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise KGError(f"Cannot open PDF {pdf_path}: {e}")
        
        if page_index < 0 or page_index >= len(doc):
            doc.close()
            raise KGError(f"Page index {page_index} out of range (0-{len(doc)-1})")
        
        page = doc[page_index]
        pix = page.get_pixmap(dpi=dpi)
        width, height = pix.width, pix.height
        
        img_buffer = io.BytesIO()
        img = Image.frombytes("RGB", [width, height], pix.samples)
        img.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()
        doc.close()
        
        return img_bytes, (width, height)
    
    def _ocr_image(
        self,
        image_bytes: bytes,
        filename: str,
        rec_mode: str = "document",
    ) -> OcrResult:
        """Send an image to SimpleTex OCR API.
        
        Args:
            image_bytes: PNG image binary data.
            filename: Filename for the request.
            rec_mode: Recognition mode - "auto", "document", or "formula".
        
        Returns:
            OcrResult with markdown content.
        
        Raises:
            KGError: If OCR fails.
        """
        if rec_mode not in self.REC_MODES:
            raise ValueError(f"Invalid rec_mode: {rec_mode}")
        
        headers = {"token": self.token}
        files = {
            "file": (filename, image_bytes, "image/png"),
        }
        data = {"rec_mode": rec_mode}
        
        try:
            resp = self._session.post(
                self.api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            raise KGError(f"OCR request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise KGError(f"OCR request failed: {e}")
        
        if resp.status_code != 200:
            raise KGError(f"OCR HTTP {resp.status_code}: {resp.text[:200]}")
        
        try:
            result = resp.json()
        except Exception as e:
            raise KGError(f"Invalid JSON response: {e}")
        
        if not result.get("status"):
            err = result.get("err_info", {})
            raise KGError(
                f"OCR failed: {err.get('err_msg', 'unknown')} "
                f"({err.get('err_type', 'unknown')})"
            )
        
        res = result.get("res", {})
        info = res.get("info", {})
        
        return OcrResult(
            page_index=0,
            markdown=info.get("markdown", ""),
            request_id=result.get("request_id", ""),
        )
    
    def ocr_page(
        self,
        pdf_path: str,
        page_index: int,
        dpi: int = 150,
        rec_mode: str = "document",
    ) -> OcrResult:
        """OCR a single PDF page.
        
        Args:
            pdf_path: Path to PDF file.
            page_index: 0-based page index.
            dpi: Rendering DPI (default: 150).
            rec_mode: Recognition mode - "auto", "document", or "formula".
        
        Returns:
            OcrResult with markdown content.
        """
        img_bytes, (w, h) = self._render_page_to_image(pdf_path, page_index, dpi)
        filename = f"page_{page_index}.png"
        
        result = self._ocr_image(img_bytes, filename, rec_mode)
        result.page_index = page_index
        
        logger.debug(
            f"OCR page {page_index} ({w}x{h}, DPI {dpi}): "
            f"{len(result.markdown)} chars, request_id={result.request_id}"
        )
        
        return result
    
    def ocr_pdf(
        self,
        pdf_path: str,
        dpi: int = 150,
        rec_mode: str = "document",
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> List[OcrResult]:
        """OCR all pages (or a range) of a PDF.
        
        Args:
            pdf_path: Path to PDF file.
            dpi: Rendering DPI (default: 150).
            rec_mode: Recognition mode (default: "document").
            start_page: First page to OCR (0-based, default: 0).
            end_page: Last page to OCR (0-based, exclusive).
                     None means to the end of the PDF.
        
        Returns:
            List of OcrResult, one per page.
        
        Raises:
            KGError: If PDF cannot be opened.
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            raise KGError(f"Cannot open PDF {pdf_path}: {e}")
        
        if end_page is None:
            end_page = total_pages
        
        results: List[OcrResult] = []
        
        for page_idx in range(start_page, end_page):
            try:
                result = self.ocr_page(pdf_path, page_idx, dpi, rec_mode)
                results.append(result)
            except KGError as e:
                logger.warning(f"OCR page {page_idx} failed: {e}")
                # Continue with other pages
                continue
        
        logger.info(
            f"OCRed {len(results)}/{end_page - start_page} pages "
            f"from {pdf_path}"
        )
        
        return results
    
    def close(self):
        """Close the HTTP session."""
        self._session.close()
