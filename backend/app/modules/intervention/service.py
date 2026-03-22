"""Intervention service layer.

Provides business logic for intervention management, analysis, and delivery.
"""


class InterventionService:
    """Service for managing learning interventions."""

    async def analyze_student_state(self, student_id: str, session_id: str) -> dict:
        """Analyze student's current learning state.

        Args:
            student_id: Student identifier
            session_id: Current session identifier

        Returns:
            dict: Analysis results including error patterns, progress indicators
        """
        raise NotImplementedError

    async def determine_intervention_type(self, analysis: dict) -> str:
        """Determine the appropriate type of intervention.

        Args:
            analysis: Student state analysis results

        Returns:
            str: Intervention type (e.g., "hint", "explanation", "redirect")
        """
        raise NotImplementedError

    async def calculate_intensity(self, analysis: dict) -> float:
        """Calculate intervention intensity (0.0 to 1.0).

        Args:
            analysis: Student state analysis results

        Returns:
            float: Intensity score
        """
        raise NotImplementedError

    async def generate_intervention(self, analysis: dict, intervention_type: str) -> dict:
        """Generate intervention content.

        Args:
            analysis: Student state analysis results
            intervention_type: Type of intervention to generate

        Returns:
            dict: Generated intervention with content and metadata
        """
        raise NotImplementedError

    async def deliver_intervention(self, intervention: dict, session_id: str) -> dict:
        """Deliver intervention to the student.

        Args:
            intervention: Intervention to deliver
            session_id: Target session identifier

        Returns:
            dict: Delivery status and tracking information
        """
        raise NotImplementedError

    async def record_intervention_outcome(self, intervention_id: str, outcome: str) -> None:
        """Record the outcome of an intervention.

        Args:
            intervention_id: Intervention identifier
            outcome: Outcome (e.g., "accepted", "dismissed", "ignored")
        """
        raise NotImplementedError