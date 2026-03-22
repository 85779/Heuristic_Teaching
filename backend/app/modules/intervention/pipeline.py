"""Intervention pipeline for LLM-based intervention generation."""

from app.core.interfaces.pipeline import IPipeline
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.context import ModuleContext


class InterventionPipeline(IPipeline):
    """Pipeline for generating learning interventions using LLM.

    Orchestrates multiple steps: analysis, decision, intensity calculation,
    and hint generation.
    """

    @property
    def pipeline_id(self) -> str:
        """Unique pipeline identifier."""
        return "intervention_pipeline"

    @property
    def version(self) -> str:
        """Pipeline version."""
        return "1.0.0"

    @property
    def steps(self) -> list[str]:
        """Ordered list of step identifiers."""
        return [
            "location",
            "analysis",
            "decision",
            "intensity",
            "hint",
        ]

    async def execute(
        self,
        context: "ModuleContext",
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the intervention pipeline.

        Args:
            context: Module execution context
            input_data: Input data including student_id, session_id, problem_data
            **kwargs: Additional execution parameters

        Returns:
            dict[str, Any]: Pipeline execution result with intervention
        """
        raise NotImplementedError

    async def execute_step(
        self,
        step_name: str,
        context: "ModuleContext",
        input_data: dict[str, Any],
        previous_steps: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a single pipeline step.

        Args:
            step_name: Name of the step to execute
            context: Module execution context
            input_data: Input data for this step
            previous_steps: Results from previous steps

        Returns:
            dict[str, Any]: Step execution result
        """
        raise NotImplementedError