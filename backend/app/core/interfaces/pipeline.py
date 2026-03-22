"""Pipeline interface - Base class for LLM pipelines."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import ModuleContext


class IPipeline(ABC):
    """Pipeline base interface.

    Pipelines define structured LLM workflows with multiple steps.
    Used by modules for complex LLM orchestration.
    """

    @property
    @abstractmethod
    def pipeline_id(self) -> str:
        """Unique pipeline identifier.

        Returns:
            str: Unique pipeline ID (e.g., "solving_pipeline")
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        """Pipeline version.

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def steps(self) -> list[str]:
        """Ordered list of step identifiers.

        Returns:
            list[str]: List of step names in execution order
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        context: "ModuleContext",
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the pipeline.

        Runs through all steps sequentially, passing output of each step
        to the next.

        Args:
            context: Module execution context
            input_data: Input data for the pipeline
            **kwargs: Additional execution parameters

        Returns:
            dict[str, Any]: Pipeline execution result containing outputs
                          from all steps
        """
        raise NotImplementedError

    @abstractmethod
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