"""
Event type definitions and validation.

This module provides:
- Standard event type constants
- Event schema definitions
- Event validation utilities
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventCategory(Enum):
    """Event categories for organization."""

    SOLVING = "solving"
    INTERVENTION = "intervention"
    STUDENT_MODEL = "student_model"
    RECOMMENDATION = "recommendation"
    SYSTEM = "system"


class EventSeverity(Enum):
    """Event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Event schemas for validation
EVENT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "solving.started": {
        "required_fields": ["problem_id", "session_id"],
        "optional_fields": ["student_level", "time_limit"]
    },
    "solving.step_completed": {
        "required_fields": ["step_name", "result", "session_id"],
        "optional_fields": ["duration_ms", "tokens_used"]
    },
    "solving.completed": {
        "required_fields": ["session_id", "success", "steps_completed"],
        "optional_fields": ["total_time_ms", "final_answer"]
    },
    "intervention.breakpoint_detected": {
        "required_fields": ["session_id", "step_name", "breakpoint_type"],
        "optional_fields": ["severity", "context"]
    },
    "intervention.hint_delivered": {
        "required_fields": ["session_id", "hint_content", "intensity_level"],
        "optional_fields": ["response_expected"]
    },
    "student_model.updated": {
        "required_fields": ["session_id", "update_type"],
        "optional_fields": ["knowledge_state", "ability_estimate"]
    },
    "recommendation.generated": {
        "required_fields": ["session_id", "recommendation_type"],
        "optional_fields": ["recommendations", "confidence"]
    }
}


class EventType:
    """Standard event type constants."""

    # Solving module events
    SOLVING_STARTED = "solving.started"
    SOLVING_STEP_COMPLETED = "solving.step_completed"
    SOLVING_COMPLETED = "solving.completed"
    SOLVING_FAILED = "solving.failed"

    # Intervention module events
    INTERVENTION_BREAKPOINT_DETECTED = "intervention.breakpoint_detected"
    INTERVENTION_HINT_DELIVERED = "intervention.hint_delivered"
    INTERVENTION_ESCALATED = "intervention.escalated"

    # Student model events
    STUDENT_MODEL_UPDATED = "student_model.updated"
    STUDENT_MODEL_KNOWLEDGE_GAP_DETECTED = "student_model.knowledge_gap_detected"

    # Recommendation module events
    RECOMMENDATION_GENERATED = "recommendation.generated"

    # System events
    MODULE_INITIALIZED = "system.module_initialized"
    MODULE_SHUTDOWN = "system.module_shutdown"
    SESSION_STARTED = "system.session_started"
    SESSION_ENDED = "system.session_ended"

    @classmethod
    def get_category(cls, event_type: str) -> Optional[EventCategory]:
        """
        Get the category for an event type.

        Args:
            event_type: Event type string

        Returns:
            EventCategory if found, None otherwise
        """
        for cat in EventCategory:
            prefix = cat.name.lower() + "."
            if event_type.startswith(prefix):
                return cat
        return None

    @classmethod
    def is_valid_type(cls, event_type: str) -> bool:
        """
        Check if an event type is valid.

        Args:
            event_type: Event type string

        Returns:
            True if event type is valid
        """
        return event_type in EVENT_SCHEMAS

    @classmethod
    def list_by_category(cls, category: EventCategory) -> List[str]:
        """
        List all event types in a category.

        Args:
            category: Event category

        Returns:
            List of event type strings
        """
        prefix = category.name.lower() + "."
        return [et for et in EVENT_SCHEMAS.keys() if et.startswith(prefix)]


class EventValidator:
    """Validator for event data."""

    def __init__(self):
        """Initialize the event validator."""
        self.logger = logging.getLogger(__name__)

    def validate_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Validate event data against schema.

        Args:
            event_type: Event type
            data: Event data to validate

        Returns:
            True if validation passes
        """
        return len(self.get_validation_errors(event_type, data)) == 0

    def get_validation_errors(self, event_type: str, data: Dict[str, Any]) -> List[str]:
        """
        Get list of validation errors.

        Args:
            event_type: Event type
            data: Event data to validate

        Returns:
            List of error messages
        """
        errors = []
        if event_type not in EVENT_SCHEMAS:
            return [f"Unknown event type: {event_type}"]
        schema = EVENT_SCHEMAS[event_type]
        required = schema.get("required_fields", [])
        errors.extend(self.validate_required_fields(data, required))
        return errors

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate that required fields are present.

        Args:
            data: Event data
            required_fields: List of required field names

        Returns:
            List of missing field names
        """
        return [f for f in required_fields if f not in data]