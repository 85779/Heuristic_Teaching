"""API routes for the solving module."""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.modules.solving.models import (
    SolvingSession,
    OrientationResult,
    ReconstructionResult,
    TransformationResult,
    VerificationResult,
    SolvingRequest,
    SolvingResponse,
)
from app.modules.solving.service import ReferenceSolutionService

router = APIRouter(prefix="/solving", tags=["solving"])

# ===== Service references (set by module initialize()) =====
_service: Optional[ReferenceSolutionService] = None
_phase_service = None


def set_service(service: ReferenceSolutionService) -> None:
    global _service
    _service = service


def set_phase_service(service) -> None:
    global _phase_service
    _phase_service = service


def get_service() -> ReferenceSolutionService:
    if _service is None:
        raise HTTPException(status_code=503, detail="Solving service not initialized")
    return _service


def get_phase_service():
    if _phase_service is None:
        raise HTTPException(status_code=503, detail="Phase service not initialized")
    return _phase_service


# ===== Session Management =====

@router.post("/sessions", response_model=SolvingSession)
async def create_session(problem: str, service=Depends(get_phase_service)) -> SolvingSession:
    """Create a new 4-phase solving session."""
    return service.create_session(problem)


@router.get("/sessions/{session_id}", response_model=SolvingSession)
async def get_session(session_id: str, service=Depends(get_phase_service)) -> SolvingSession:
    """Get session by ID."""
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


# ===== 4-Phase Workflow =====

@router.post("/sessions/{session_id}/orientation", response_model=OrientationResult)
async def process_orientation(
    session_id: str, problem: str, service=Depends(get_phase_service),
) -> OrientationResult:
    """Phase 1: Problem orientation — understand, identify concepts, set goals."""
    return await service.process_orientation(session_id, problem)


@router.post("/sessions/{session_id}/reconstruction", response_model=ReconstructionResult)
async def process_reconstruction(
    session_id: str, service=Depends(get_phase_service),
) -> ReconstructionResult:
    """Phase 2: Problem reconstruction — break down, find relationships."""
    return await service.process_reconstruction(session_id)


@router.post("/sessions/{session_id}/transformation", response_model=TransformationResult)
async def process_transformation(
    session_id: str, service=Depends(get_phase_service),
) -> TransformationResult:
    """Phase 3: Solution transformation — choose strategies, plan steps."""
    return await service.process_transformation(session_id)


@router.post("/sessions/{session_id}/verification", response_model=VerificationResult)
async def process_verification(
    session_id: str, service=Depends(get_phase_service),
) -> VerificationResult:
    """Phase 4: Solution verification — validate, check errors."""
    return await service.process_verification(session_id)


@router.post("/sessions/{session_id}/complete", response_model=SolvingSession)
async def complete_session(
    session_id: str, service=Depends(get_phase_service),
) -> SolvingSession:
    """Complete the solving session."""
    return await service.complete_session(session_id)


# ===== Reference Solution (standalone, non-session) =====

@router.post("/reference", response_model=SolvingResponse)
async def generate_reference_solution(
    request: SolvingRequest,
    session_id: Optional[str] = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    service: ReferenceSolutionService = Depends(get_service),
) -> SolvingResponse:
    """Generate a reference solution (or error feedback) for a math problem."""
    resolved_session_id = getattr(request, 'session_id', None) or session_id or x_session_id
    return await service.generate(request, session_id=resolved_session_id)
