"""Student model API routes."""

from fastapi import APIRouter, HTTPException, Depends
from app.modules.student_model.models import (
    StudentProfile,
    InterventionRecord,
    RoutingHint,
)

router = APIRouter(prefix="/profile", tags=["student-model"])

_service = None


def set_service(service) -> None:
    global _service
    _service = service


def get_service():
    if _service is None:
        raise HTTPException(status_code=503, detail="Student model service not initialized")
    return _service


@router.get("/{student_id}", response_model=StudentProfile)
async def get_profile(student_id: str, service=Depends(get_service)) -> StudentProfile:
    """Get student profile (creates default if new)."""
    return await service.get_profile(student_id)


@router.get("/{student_id}/dimension-ratio")
async def get_dimension_ratio(student_id: str, service=Depends(get_service)) -> dict:
    """Get student dimension_ratio."""
    ratio = await service.get_dimension_ratio(student_id)
    return {"student_id": student_id, "dimension_ratio": ratio}


@router.get("/{student_id}/routing-hint", response_model=RoutingHint)
async def get_routing_hint(student_id: str, service=Depends(get_service)) -> RoutingHint:
    """Get routing hint for dimension decisions."""
    return await service.get_routing_hint(student_id)


@router.post("/{student_id}/intervention", response_model=StudentProfile)
async def record_intervention(
    student_id: str,
    record: InterventionRecord,
    service=Depends(get_service),
) -> StudentProfile:
    """Record an intervention outcome (called by Module 2)."""
    return await service.update_after_intervention(student_id, record)


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "module": "student_model"}
