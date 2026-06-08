"""Student model data models."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class InterventionRecord(BaseModel):
    """Record of a single intervention event for dimension tracking."""

    intervention_id: str
    problem_id: str
    dimension: str  # "RESOURCE" or "METACOGNITIVE"
    level: str  # e.g., "R2", "M3"
    outcome: str  # "SOLVED", "MAX_ESCALATION", "ABANDONED"
    intervention_count: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topic: Optional[str] = None  # optional knowledge point topic


class StudentProfile(BaseModel):
    """Student cognitive profile stored in MongoDB."""

    student_id: str
    dimension_ratio: float = 0.5  # R-type ratio, 0.0-1.0
    intervention_history: list[InterventionRecord] = Field(default_factory=list)

    total_interventions: int = 0
    total_solved: int = 0
    total_escalation: int = 0

    ratio_trend: str = "stable"  # "rising", "falling", "stable"
    trend_confidence: float = 0.0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoutingHint(BaseModel):
    """Routing hint for Module 2 dimension routing decisions."""

    student_id: str
    is_new_student: bool = True
    dimension_ratio: float = 0.5
    ratio_trend: str = "stable"
    trend_confidence: float = 0.0
    weak_dimensions: list[str] = Field(default_factory=list)
    recommended_dimension_hint: str = ""
    recent_intervention_summary: str = ""
    confidence: float = 0.0
