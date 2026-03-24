"""Intervention service layer.

Provides business logic for intervention management, analysis, and delivery.
"""

import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

# Import sub-modules
from .locator.breaker import BreakpointLocator
from .locator.models import BreakpointLocation
from .analyzer.analyzer import BreakpointAnalyzer
from .generator.generator import HintGenerator

# Import models
from .models import Intervention, InterventionType, InterventionStatus

if TYPE_CHECKING:
    from app.core.context import ModuleContext


class InterventionService:
    """Service for managing learning interventions."""

    def __init__(self, context: Optional["ModuleContext"] = None):
        """Initialize the intervention service.
        
        Args:
            context: Module context (optional, for accessing other modules/state)
        """
        self._context = context
        self._locator = BreakpointLocator()
        self._analyzer = BreakpointAnalyzer()
        self._generator = HintGenerator()
        self._interventions: dict[str, Intervention] = {}  # in-memory store

    async def generate(
        self,
        problem: str,
        student_work: str,
        student_steps: List[dict],
        solution_steps: List[dict],
        intensity: float,
        session_id: str,
        student_id: str,
    ) -> Intervention:
        """
        Main entry point: Generate an intervention hint.
        
        Flow:
        1. BreakpointLocator.locate() → BreakpointLocation
        2. BreakpointAnalyzer.analyze() → BreakpointAnalysis
        3. HintGenerator.generate() → GeneratedHint
        4. Return Intervention object
        
        Args:
            problem: The problem statement (LaTeX)
            student_work: Student's work so far (LaTeX)
            student_steps: List of student's steps as dicts (from session state)
            solution_steps: List of reference solution steps as dicts
            intensity: Intervention intensity (0.0~1.0)
            session_id: Current session ID
            student_id: Student ID
        
        Returns:
            Intervention object with generated hint content
        """
        # Step 1: Locate breakpoint - convert dicts to TeachingStep
        from app.modules.solving.models import TeachingStep
        
        student_steps_obj = [
            TeachingStep(
                step_id=s.get("step_id", f"s{i+1}"),
                step_name=s.get("step_name", ""),
                content=s.get("content", ""),
            )
            for i, s in enumerate(student_steps)
        ]
        solution_steps_obj = [
            TeachingStep(
                step_id=s.get("step_id", f"s{i+1}"),
                step_name=s.get("step_name", ""),
                content=s.get("content", ""),
            )
            for i, s in enumerate(solution_steps)
        ]
        location = self._locator.locate(student_steps_obj, solution_steps_obj)
        
        # Step 2: Analyze (LLM call)
        solution_step_contents = [s["content"] for s in solution_steps]
        analysis = await self._analyzer.analyze(
            breakpoint_location=location,
            problem=problem,
            student_work=student_work,
            solution_steps=solution_step_contents,
        )
        
        # Step 3: Generate hint (LLM call)
        hint = await self._generator.generate(
            analysis=analysis,
            problem=problem,
            intensity=intensity,
        )
        
        # Step 4: Build and return Intervention
        intervention = Intervention(
            id=f"int_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            session_id=session_id,
            intervention_type=InterventionType.HINT,
            status=InterventionStatus.SUGGESTED,
            content=hint.content,
            intensity=intensity,
            metadata={
                "breakpoint_location": location.gap_description,
                "breakpoint_type": location.breakpoint_type.value,
                "hint_level": hint.level,
                "approach_used": hint.approach_used,
                "required_knowledge": analysis.required_knowledge,
                "required_connection": analysis.required_connection,
            },
        )
        
        self._interventions[intervention.id] = intervention
        return intervention

    async def analyze_student_state(self, student_id: str, session_id: str) -> dict:
        """Analyze student's current learning state.

        Args:
            student_id: Student identifier
            session_id: Current session identifier

        Returns:
            dict: Analysis results including error patterns, progress indicators
        """
        # Simplified: return empty analysis dict
        # Full implementation would pull from state manager
        return {
            "student_id": student_id,
            "session_id": session_id,
            "current_step": None,
            "error_count": 0,
        }

    async def determine_intervention_type(self, analysis: dict) -> str:
        """Determine the appropriate type of intervention.

        Args:
            analysis: Student state analysis results

        Returns:
            str: Intervention type (e.g., "hint", "explanation", "redirect")
        """
        # Simplified: always return "hint"
        return "hint"

    async def calculate_intensity(self, analysis: dict) -> float:
        """Calculate intervention intensity (0.0 to 1.0).

        Args:
            analysis: Student state analysis results

        Returns:
            float: Intensity score
        """
        # Simplified: return 0.5 as default
        # Intensity is passed externally in generate()
        return 0.5

    async def generate_intervention(self, analysis: dict, intervention_type: str) -> dict:
        """Generate intervention content.

        Args:
            analysis: Student state analysis results
            intervention_type: Type of intervention to generate

        Returns:
            dict: Generated intervention with content and metadata
        """
        # Simplified: just return a basic structure
        # Main logic is in generate()
        return {
            "content": "Intervention content",
            "type": intervention_type,
        }

    async def deliver_intervention(self, intervention_id: str, session_id: str) -> dict:
        """Deliver intervention to the student.

        Args:
            intervention_id: Intervention identifier
            session_id: Target session identifier

        Returns:
            dict: Delivery status and tracking information
        """
        intervention = self._interventions.get(intervention_id)
        if intervention:
            intervention.status = InterventionStatus.DELIVERED
            intervention.delivered_at = datetime.utcnow()
        return {
            "delivered": intervention is not None,
            "intervention_id": intervention_id,
        }

    async def record_intervention_outcome(self, intervention_id: str, outcome: str) -> None:
        """Record the outcome of an intervention.

        Args:
            intervention_id: Intervention identifier
            outcome: Outcome (e.g., "accepted", "dismissed", "ignored")
        """
        intervention = self._interventions.get(intervention_id)
        if intervention:
            intervention.status = InterventionStatus(outcome)
            intervention.outcome_at = datetime.utcnow()
