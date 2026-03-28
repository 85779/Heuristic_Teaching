"""API routes for the intervention module (v2).

New endpoints for v2 flow:
  POST /interventions          - Create intervention
  POST /interventions/feedback - Process student feedback
  POST /interventions/end      - End intervention (frontend END)
  POST /interventions/escalate - Force escalate (frontend ESCALATE)
"""

from fastapi import APIRouter, HTTPException, Depends
from app.modules.intervention.models import (
    InterventionRequest,
    InterventionResponse,
    Intervention,
    FeedbackRequest,
    EndRequest,
    EscalateRequest,
)
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


# =============================================================================
# Core Endpoints (v2)
# =============================================================================

@router.post("/interventions", response_model=InterventionResponse)
async def create_intervention(
    request: InterventionRequest,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Create a new intervention (first turn or new session).

    Args:
        request: InterventionRequest with session_id, student_id, student_input
        service: Intervention service instance

    Returns:
        InterventionResponse with generated intervention
    """
    # The new v2 service uses student_input from request directly
    return await service.create_intervention(request)


@router.post("/interventions/feedback", response_model=InterventionResponse)
async def process_feedback(
    request: FeedbackRequest,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Process student feedback (accepted/not_progressed).

    Args:
        request: FeedbackRequest with session_id, student_input, frontend_signal
        service: Intervention service instance

    Returns:
        InterventionResponse with new intervention (if needed)
    """
    return await service.process_feedback(request)


@router.post("/interventions/end", response_model=InterventionResponse)
async def end_intervention(
    request: EndRequest,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """End intervention (frontend END signal).

    Args:
        request: EndRequest with session_id and optional reason
        service: Intervention service instance

    Returns:
        InterventionResponse confirming end
    """
    return await service.end_intervention(
        session_id=request.session_id,
        reason=request.reason,
    )


@router.post("/interventions/escalate", response_model=InterventionResponse)
async def escalate_intervention(
    request: EscalateRequest,
    service: InterventionService = Depends(get_service),
) -> InterventionResponse:
    """Force escalate intervention (frontend ESCALATE signal).

    Args:
        request: EscalateRequest with session_id and optional reason
        service: Intervention service instance

    Returns:
        InterventionResponse with escalated intervention
    """
    return await service.escalate_intervention(
        session_id=request.session_id,
        reason=request.reason,
    )


# =============================================================================
# Legacy Endpoints (kept for backward compatibility)
# =============================================================================

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
        InterventionResponse with intervention data
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
    """Mark an intervention as accepted by the student (legacy).

    Note: In v2, use POST /interventions/feedback instead.

    Args:
        intervention_id: Intervention identifier
        service: Intervention service instance

    Returns:
        InterventionResponse
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
    """Mark an intervention as dismissed by the student (legacy).

    Note: In v2, use POST /interventions/feedback with frontend_signal=ESCALATE instead.

    Args:
        intervention_id: Intervention identifier
        service: Intervention service instance

    Returns:
        InterventionResponse
    """
    await service.record_intervention_outcome(intervention_id, "dismissed")
    intervention = service._interventions.get(intervention_id)
    return InterventionResponse(
        success=True,
        intervention=intervention,
        message="Intervention dismissed",
    )
