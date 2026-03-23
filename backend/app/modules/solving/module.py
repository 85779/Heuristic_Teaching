"""Solving module implementation.

This module manages the complete problem-solving workflow including
orientation, reconstruction, transformation, and verification phases.
"""

from app.core.interfaces.module import IModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from app.core.context import ModuleContext


class SolvingModule(IModule):
    """Solving module for problem-solving workflow management.

    This module orchestrates the four-phase problem-solving process:
    - Orientation: Understanding the problem space
    - Reconstruction: Breaking down the problem
    - Transformation: Applying solution strategies
    - Verification: Validating the solution
    """

    @property
    def module_id(self) -> str:
        """Unique module identifier."""
        return "solving"

    @property
    def module_name(self) -> str:
        """Module display name."""
        return "Solving Module"

    @property
    def version(self) -> str:
        """Module version."""
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """List of module IDs this module depends on."""
        return []

    @property
    def provides_events(self) -> list[str]:
        """List of event types this module publishes."""
        return [
            "solving.started",
            "solving.orientation_completed",
            "solving.reconstruction_completed",
            "solving.transformation_completed",
            "solving.verification_completed",
            "solving.completed",
            "solving.error_detected",
            "solving.stuck_detected",
        ]

    @property
    def subscribes_events(self) -> list[str]:
        """List of event types this module subscribes to."""
        return []

    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the solving module.

        Args:
            context: Module execution context
        """
        self._context = context
        self._logger = context.logger
        self._logger.info("SolvingModule initialized")

    async def shutdown(self) -> None:
        """Shutdown the solving module."""
        if hasattr(self, '_context') and self._context:
            self._logger = getattr(self, '_logger', None)
            if self._logger:
                self._logger.info("SolvingModule shutting down")

    def register_routes(self, router: "APIRouter") -> None:
        """Register API routes for the solving module.

        Args:
            router: FastAPI APIRouter to register routes with
        """
        # Import and include the solving routes
        from . import routes as solving_routes
        router.include_router(solving_routes.router)