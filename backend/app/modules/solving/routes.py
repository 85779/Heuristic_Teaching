"""API routes for the solving module."""

from fastapi import APIRouter, HTTPException, Depends
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


@router.post("/sessions", response_model=SolvingSession)
async def create_session(problem_id: str) -> SolvingSession:
    """Create a new problem-solving session.

    Args:
        problem_id: ID of the problem to solve

    Returns:
        SolvingSession: The created session

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.get("/sessions/{session_id}", response_model=SolvingSession)
async def get_session(session_id: str) -> SolvingSession:
    """Get a problem-solving session by ID.

    Args:
        session_id: ID of the session

    Returns:
        SolvingSession: The session details

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.post("/sessions/{session_id}/orientation", response_model=OrientationResult)
async def process_orientation(session_id: str) -> OrientationResult:
    """Process the orientation phase for a session.

    Args:
        session_id: ID of the solving session

    Returns:
        OrientationResult: Orientation phase results

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.post("/sessions/{session_id}/reconstruction", response_model=ReconstructionResult)
async def process_reconstruction(session_id: str) -> ReconstructionResult:
    """Process the reconstruction phase for a session.

    Args:
        session_id: ID of the solving session

    Returns:
        ReconstructionResult: Reconstruction phase results

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.post("/sessions/{session_id}/transformation", response_model=TransformationResult)
async def process_transformation(session_id: str) -> TransformationResult:
    """Process the transformation phase for a session.

    Args:
        session_id: ID of the solving session

    Returns:
        TransformationResult: Transformation phase results

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.post("/sessions/{session_id}/verification", response_model=VerificationResult)
async def process_verification(session_id: str) -> VerificationResult:
    """Process the verification phase for a session.

    Args:
        session_id: ID of the solving session

    Returns:
        VerificationResult: Verification phase results

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


@router.post("/sessions/{session_id}/complete", response_model=SolvingSession)
async def complete_session(session_id: str) -> SolvingSession:
    """Complete a problem-solving session.

    Args:
        session_id: ID of the solving session

    Returns:
        SolvingSession: The completed session

    Raises:
        NotImplementedError
    """
    raise NotImplementedError


# ============== Reference Solution Endpoint ==============

# Global service instance (will be initialized by module)
_service: Optional[ReferenceSolutionService] = None


def get_service() -> ReferenceSolutionService:
    """Get or create the service instance."""
    global _service
    if _service is None:
        _service = ReferenceSolutionService()
    return _service


@router.post("/reference", response_model=SolvingResponse)
async def generate_reference_solution(
    request: SolvingRequest,
) -> SolvingResponse:
    """Generate reference solution for a problem.
    
    This is the main entry point for Module 1: takes a problem
    (with optional student work) and returns either:
    - A complete reference solution (if evaluation passes)
    - Error feedback (if student work has issues)
    
    Args:
        request: SolvingRequest with:
            - problem: LaTeX problem statement
            - student_work: Optional LaTeX student work
            - model: Model to use (default: qwen-turbo)
            - temperature: Temperature (default: 0.7)
    
    Returns:
        SolvingResponse with:
            - success: Whether solution was generated
            - evaluation: Evaluation result
            - solution: ReferenceSolution (if success)
            - error_feedback: ErrorFeedback (if not success)
    """
    service = get_service()
    return await service.generate(request)