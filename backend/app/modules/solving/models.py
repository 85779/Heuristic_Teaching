"""Data models for the solving module."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SolvingSession(BaseModel):
    """Model representing a problem-solving session."""

    session_id: str = Field(..., description="Unique session identifier")
    problem_id: str = Field(..., description="ID of the problem being solved")
    status: str = Field(default="started", description="Current session status")
    current_phase: str = Field(default="orientation", description="Current phase")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OrientationResult(BaseModel):
    """Model for orientation phase results."""

    session_id: str = Field(..., description="Session ID")
    understanding: str = Field(..., description="Problem understanding")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts identified")
    goals: List[str] = Field(default_factory=list, description="Learning goals")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class ReconstructionResult(BaseModel):
    """Model for reconstruction phase results."""

    session_id: str = Field(..., description="Session ID")
    components: List[str] = Field(default_factory=list, description="Problem components")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Component relationships")
    breakdown: str = Field(..., description="Problem breakdown")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class TransformationResult(BaseModel):
    """Model for transformation phase results."""

    session_id: str = Field(..., description="Session ID")
    strategies: List[str] = Field(default_factory=list, description="Solution strategies")
    approach: str = Field(..., description="Proposed approach")
    steps: List[str] = Field(default_factory=list, description="Solution steps")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class VerificationResult(BaseModel):
    """Model for verification phase results."""

    session_id: str = Field(..., description="Session ID")
    is_valid: bool = Field(..., description="Whether solution is valid")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    corrections: List[str] = Field(default_factory=list, description="Suggested corrections")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class SolvingEvent(BaseModel):
    """Model for solving-related events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    session_id: str = Field(..., description="Associated session ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")