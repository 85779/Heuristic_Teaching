"""Recommendation API routes for Module 3."""

from fastapi import APIRouter, HTTPException, Depends
from app.modules.recommendation.models import (
    RecommendRequest,
    RecommendResponse,
    TriggerEvent,
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Module reference (set during initialization)
_module = None


def set_module(module) -> None:
    """Set the module instance.
    
    Called by RecommendationModule.initialize() to wire up the service.
    """
    global _module
    _module = module


def _get_service():
    """Get the recommendation service from the module.
    
    Returns:
        RecommendationService instance.
        
    Raises:
        HTTPException: If module not initialized.
    """
    if _module is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation module not initialized",
        )
    if not hasattr(_module, "_service") or _module._service is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation service not initialized",
        )
    return _module._service


@router.post("/recommend", response_model=RecommendResponse)
async def trigger_recommendation(
    request: RecommendRequest,
    service=Depends(_get_service),
) -> RecommendResponse:
    """Trigger a problem recommendation.
    
    Called when:
    - Student finishes a problem (outcome=SOLVED)
    - Student gets stuck at max escalation (outcome=MAX_ESCALATION)  
    - Student abandons a problem (outcome=ABANDONED)
    - Student manually requests next problem (outcome=MANUAL)
    
    Args:
        request: Recommendation request with student_id, trigger, etc.
        service: Injected recommendation service.
        
    Returns:
        RecommendResponse with generated problem and metadata.
    """
    try:
        response = await service.recommend(
            student_id=request.student_id,
            trigger=request.trigger,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}",
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Health status dict.
    """
    return {"status": "ok", "module": "recommendation"}