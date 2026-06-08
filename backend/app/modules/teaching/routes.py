"""Teaching strategy API routes."""

from fastapi import APIRouter, HTTPException, Depends
from app.modules.teaching.models import TeachingStrategy, StrategyRequest

router = APIRouter(prefix="/teaching", tags=["teaching"])

_service = None


def set_service(service) -> None:
    global _service
    _service = service


def get_service():
    if _service is None:
        raise HTTPException(status_code=503, detail="Teaching service not initialized")
    return _service


@router.post("/strategy", response_model=TeachingStrategy)
async def get_strategy(
    request: StrategyRequest,
    service=Depends(get_service),
) -> TeachingStrategy:
    """Get teaching strategy for a student."""
    return await service.select_strategy(request.student_id)


@router.get("/strategy/{student_id}", response_model=TeachingStrategy)
async def get_strategy_by_id(
    student_id: str,
    service=Depends(get_service),
) -> TeachingStrategy:
    """Get teaching strategy by student ID."""
    return await service.select_strategy(student_id)


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "module": "teaching"}
