"""Data models for the intervention module."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class InterventionType(str, Enum):
    """Types of interventions available."""

    HINT = "hint"
    EXPLANATION = "explanation"
    REDIRECT = "redirect"
    EXAMPLE = "example"
    SCAFFOLD = "scaffold"


class InterventionStatus(str, Enum):
    """Status of an intervention."""

    SUGGESTED = "suggested"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    IGNORED = "ignored"


class Intervention(BaseModel):
    """Intervention model representing a learning intervention."""

    id: str = Field(..., description="Unique intervention identifier")
    student_id: str = Field(..., description="Student identifier")
    session_id: str = Field(..., description="Session identifier")
    intervention_type: InterventionType = Field(..., description="Type of intervention")
    status: InterventionStatus = Field(default=InterventionStatus.SUGGESTED, description="Intervention status")
    content: str = Field(..., description="Intervention content text")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Intensity level (0.0-1.0)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    outcome_at: Optional[datetime] = Field(None, description="Outcome timestamp")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "int_12345",
                "student_id": "student_001",
                "session_id": "session_001",
                "intervention_type": "hint",
                "status": "suggested",
                "content": "Consider breaking down the problem into smaller steps.",
                "intensity": 0.3,
                "metadata": {"reason": "student_stuck", "location": "step_3"},
            }
        }


class InterventionRequest(BaseModel):
    """Request model for creating an intervention."""

    student_id: str = Field(..., description="Student identifier")
    session_id: str = Field(..., description="Session identifier")
    intervention_type: Optional[InterventionType] = Field(None, description="Desired intervention type (optional)")
    context: dict = Field(..., description="Current learning context")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "student_id": "student_001",
                "session_id": "session_001",
                "intervention_type": "hint",
                "context": {
                    "current_step": "step_3",
                    "time_on_step": 300,
                    "error_count": 2,
                    "previous_attempts": ["attempt_1", "attempt_2"],
                },
            }
        }


class InterventionResponse(BaseModel):
    """Response model for intervention operations."""

    success: bool = Field(..., description="Operation success status")
    intervention: Optional[Intervention] = Field(None, description="Generated intervention")
    message: str = Field(..., description="Response message")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "success": True,
                "intervention": None,
                "message": "Intervention generated successfully",
            }
        }