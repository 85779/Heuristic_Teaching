"""FastAPI routes for the knowledge base module.

Provides REST API endpoints for knowledge retrieval, document
ingestion, and collection management.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .service import RAGService
from .models import KGError, DocumentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

# Shared service instance (will be set by module initialization)
_service: RAGService | None = None


def get_service() -> RAGService:
    """Get the RAG service instance.
    
    Returns:
        RAGService instance.
    
    Raises:
        HTTPException: If service is not initialized.
    """
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base service not initialized"
        )
    return _service


def set_service(service: RAGService) -> None:
    """Set the RAG service instance (called by module init).
    
    Args:
        service: RAGService instance to set.
    """
    global _service
    _service = service


# =============================================================================
# Request/Response Models
# =============================================================================

class RetrieveRequest(BaseModel):
    """Request model for knowledge retrieval."""
    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of results to return")
    filter_type: Optional[str] = Field(
        default=None,
        description="Filter by document type"
    )
    filter_grade: Optional[str] = Field(
        default=None,
        description="Filter by grade level"
    )
    filter_difficulty: Optional[str] = Field(
        default=None,
        description="Filter by difficulty"
    )


class KGChunkResponse(BaseModel):
    """Response model for a knowledge chunk."""
    id: str
    content: str
    metadata: dict
    similarity: float


class RetrieveResponse(BaseModel):
    """Response model for knowledge retrieval."""
    success: bool
    chunks: List[KGChunkResponse]
    total: int
    query_time_ms: float


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    type: str = Field(
        default="knowledge_point",
        description="Document type"
    )
    name: str = Field(..., description="Document name")
    content: str = Field(..., description="Text content to ingest")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    grade: str = Field(default="high_school", description="Grade level")
    difficulty: str = Field(default="medium", description="Difficulty level")


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    message: str
    chunks: int
    doc_id: Optional[str] = None


class BatchIngestRequest(BaseModel):
    """Request model for batch document ingestion."""
    documents: List[IngestRequest] = Field(..., description="List of documents to ingest")


class BatchIngestResponse(BaseModel):
    """Response model for batch ingestion."""
    success: bool
    total: int
    successful: int
    failed: int
    results: List[dict]


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    success: bool
    message: str


class StatsResponse(BaseModel):
    """Response model for collection stats."""
    status: str
    collection: Optional[str] = None
    dimension: Optional[int] = None
    document_count: int = 0
    persist_dir: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    vector_store: str
    embedding_service: str
    document_count: int


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_knowledge(
    request: RetrieveRequest,
    service: RAGService = Depends(get_service)
) -> RetrieveResponse:
    """Retrieve relevant knowledge chunks for a query.
    
    Args:
        request: RetrieveRequest with query and filters.
        service: RAG service instance.
    
    Returns:
        RetrieveResponse with matching chunks.
    """
    # Build filter metadata
    filter_metadata = None
    if any([request.filter_type, request.filter_grade, request.filter_difficulty]):
        filter_metadata = {}
        if request.filter_type:
            filter_metadata["type"] = request.filter_type
        if request.filter_grade:
            filter_metadata["grade"] = request.filter_grade
        if request.filter_difficulty:
            filter_metadata["difficulty"] = request.filter_difficulty
    
    try:
        chunks = await service.retrieve(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=filter_metadata
        )
        
        chunk_responses = [
            KGChunkResponse(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
                similarity=chunk.similarity
            )
            for chunk in chunks
        ]
        
        return RetrieveResponse(
            success=True,
            chunks=chunk_responses,
            total=len(chunk_responses),
            query_time_ms=0.0  # TODO: Add timing
        )
        
    except KGError as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    service: RAGService = Depends(get_service)
) -> IngestResponse:
    """Ingest a single document into the knowledge base.
    
    Args:
        request: IngestRequest with document content and metadata.
        service: RAG service instance.
    
    Returns:
        IngestResponse with ingestion status.
    """
    # Validate document type
    valid_types = [dt.value for dt in DocumentType]
    if request.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {valid_types}"
        )
    
    # Get the ingestion pipeline from service
    # Note: RAGService wraps the vector store and embedder
    # We need to access the underlying ingestion capability
    try:
        from .ingestion import IngestionPipeline
        
        pipeline = IngestionPipeline(
            vector_store=service.vector_store,
            embedder=service.embedder
        )
        
        metadata = {
            "type": request.type,
            "name": request.name,
            "keywords": request.keywords,
            "grade": request.grade,
            "difficulty": request.difficulty,
        }
        
        result = await pipeline.ingest_text_content(
            content=request.content,
            metadata=metadata
        )
        
        return IngestResponse(
            success=result.get("status") == "success",
            message=f"Ingested {result.get('chunks', 0)} chunks",
            chunks=result.get("chunks", 0),
            doc_id=result.get("doc_id")
        )
        
    except KGError as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/batch", response_model=BatchIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    service: RAGService = Depends(get_service)
) -> BatchIngestResponse:
    """Ingest multiple documents in a batch.
    
    Args:
        request: BatchIngestRequest with list of documents.
        service: RAG service instance.
    
    Returns:
        BatchIngestResponse with overall and per-document results.
    """
    # Validate all document types
    valid_types = [dt.value for dt in DocumentType]
    for doc in request.documents:
        if doc.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type '{doc.type}'. Must be one of: {valid_types}"
            )
    
    try:
        from .ingestion import IngestionPipeline
        
        pipeline = IngestionPipeline(
            vector_store=service.vector_store,
            embedder=service.embedder
        )
        
        results = []
        successful = 0
        failed = 0
        
        for doc in request.documents:
            try:
                metadata = {
                    "type": doc.type,
                    "name": doc.name,
                    "keywords": doc.keywords,
                    "grade": doc.grade,
                    "difficulty": doc.difficulty,
                }
                
                result = await pipeline.ingest_text_content(
                    content=doc.content,
                    metadata=metadata
                )
                
                results.append({
                    "name": doc.name,
                    "status": result.get("status"),
                    "chunks": result.get("chunks", 0),
                })
                
                if result.get("status") == "success":
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                results.append({
                    "name": doc.name,
                    "status": "error",
                    "error": str(e)
                })
                failed += 1
        
        return BatchIngestResponse(
            success=failed == 0,
            total=len(request.documents),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except KGError as e:
        logger.error(f"Batch ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection", response_model=DeleteResponse)
async def delete_collection(
    service: RAGService = Depends(get_service)
) -> DeleteResponse:
    """Delete all documents in the knowledge base collection.
    
    Args:
        service: RAG service instance.
    
    Returns:
        DeleteResponse with deletion status.
    """
    try:
        result = await service.delete_all_documents()
        return DeleteResponse(
            success=result.get("status") == "success",
            message=result.get("message", "Collection deleted")
        )
    except KGError as e:
        logger.error(f"Collection deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection/stats", response_model=StatsResponse)
async def get_stats(
    service: RAGService = Depends(get_service)
) -> StatsResponse:
    """Get knowledge base collection statistics.
    
    Args:
        service: RAG service instance.
    
    Returns:
        StatsResponse with collection stats.
    """
    stats = service.get_stats()
    return StatsResponse(**stats)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: RAGService = Depends(get_service)
) -> HealthResponse:
    """Perform health check on the knowledge base service.
    
    Args:
        service: RAG service instance.
    
    Returns:
        HealthResponse with component health status.
    """
    health = await service.health_check()
    return HealthResponse(**health)


@router.get("/document-types", response_model=List[str])
async def get_document_types() -> List[str]:
    """Get list of valid document types.
    
    Returns:
        List of document type strings.
    """
    return [dt.value for dt in DocumentType]
