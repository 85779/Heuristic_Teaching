"""Solving pipeline for orchestrating the problem-solving workflow."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.context import ModuleContext


class SolvingPipeline:
    """Pipeline for orchestrating the four-phase problem-solving workflow.

    This pipeline manages the sequential execution of orientation,
    reconstruction, transformation, and verification phases.
    """

    def __init__(self, context: "ModuleContext"):
        """Initialize the solving pipeline.

        Args:
            context: Module execution context
        """
        raise NotImplementedError

    async def execute(self, problem_id: str) -> str:
        """Execute the complete solving pipeline.

        Args:
            problem_id: ID of the problem to solve

        Returns:
            str: Session ID of the completed solving session

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    async def run_orientation(self, session_id: str) -> None:
        """Run the orientation phase.

        Args:
            session_id: ID of the solving session

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    async def run_reconstruction(self, session_id: str) -> None:
        """Run the reconstruction phase.

        Args:
            session_id: ID of the solving session

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    async def run_transformation(self, session_id: str) -> None:
        """Run the transformation phase.

        Args:
            session_id: ID of the solving session

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    async def run_verification(self, session_id: str) -> None:
        """Run the verification phase.

        Args:
            session_id: ID of the solving session

        Raises:
            NotImplementedError
        """
        raise NotImplementedError