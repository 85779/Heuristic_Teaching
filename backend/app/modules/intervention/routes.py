"""API routes for the intervention module."""

from fastapi import APIRouter, HTTPException, Depends
from app.modules.intervention.models import InterventionRequest, InterventionResponse, Intervention
from app.modules.intervention.service import InterventionService

router = APIRouter()

# Shared service instance (will be set by module initialization)
_service: InterventionService | None = None


def get_service() -> InterventionService:
    """Get the intervention service instance."""
    if _service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _service


def set_service(service: InterventionService) -> None:
    """Set the intervention service instance (called by module init)."""
    global _service
    _service = service


@router.post("/interventions", response_model=InterventionResponse)
async def create_intervention(
    request: InterventionRequest,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Create a new learning intervention.

    Args:
        request: Intervention request with student context
        service: Intervention service instance

    Returns:
        InterventionResponse: Operation result with intervention data
    """
    try:
        intervention = await service.generate(
            session_id=request.session_id,
            student_work=request.context.get("student_work"),
            intensity=request.context.get("intensity", 0.5),
            student_id=request.student_id,
        )
        return InterventionResponse(
            success=True,
            intervention=intervention,
            message="Intervention generated successfully",
        )
    except Exception as e:
        return InterventionResponse(
            success=False,
            intervention=None,
            message=f"Failed to generate intervention: {str(e)}",
        )


@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Retrieve an intervention by ID.

    Args:
        intervention_id: Intervention identifier
        service: Intervention service instance

    Returns:
        InterventionResponse: Operation result with intervention data
    """
    intervention = service._interventions.get(intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return InterventionResponse(
        success=True,
        intervention=intervention,
        message="Intervention retrieved successfully",
    )


@router.post("/interventions/{intervention_id}/accept", response_model=InterventionResponse)
async def accept_intervention(
    intervention_id: str,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Mark an intervention as accepted by the student.

    Args:
        intervention_id: Intervention identifier
        service: Intervention service instance

    Returns:
        InterventionResponse: Operation result
    """
    await service.record_intervention_outcome(intervention_id, "accepted")
    intervention = service._interventions.get(intervention_id)
    return InterventionResponse(
        success=True,
        intervention=intervention,
        message="Intervention accepted",
    )


@router.post("/interventions/{intervention_id}/dismiss", response_model=InterventionResponse)
async def dismiss_intervention(
    intervention_id: str,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Mark an intervention as dismissed by the student.

    Args:
        intervention_id: Intervention identifier
        service: Intervention service instance

    Returns:
        InterventionResponse: Operation result
    """
    await service.record_intervention_outcome(intervention_id, "dismissed")
    intervention = service._interventions.get(intervention_id)
    return InterventionResponse(
        success=True,
        intervention=intervention,
        message="Intervention dismissed",
    )
