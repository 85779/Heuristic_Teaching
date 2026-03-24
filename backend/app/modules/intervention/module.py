"""Intervention module implementation.

This module provides targeted learning interventions based on student
problem-solving analysis.
"""

from app.core.interfaces.module import IModule
from app.modules.intervention.service import InterventionService
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from app.core.context import ModuleContext


class InterventionModule(IModule):
    """Intervention module for providing targeted learning support.

    This module analyzes student problem-solving behavior and provides
    appropriate interventions at optimal moments.
    """

    @property
    def module_id(self) -> str:
        """Unique module identifier."""
        return "intervention"

    @property
    def module_name(self) -> str:
        """Module display name."""
        return "Intervention Module"

    @property
    def version(self) -> str:
        """Module version."""
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """List of module IDs this module depends on."""
        return ["solving"]

    @property
    def provides_events(self) -> list[str]:
        """List of event types this module publishes."""
        return [
            "intervention.suggested",
            "intervention.delivered",
            "intervention.dismissed",
        ]

    @property
    def subscribes_events(self) -> list[str]:
        """List of event types this module subscribes to."""
        return [
            "solving.step_completed",
            "solving.error_detected",
            "solving.stuck_detected",
        ]

    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the intervention module.

        Args:
            context: Module execution context
        """
        self._context = context
        self._service = InterventionService(context)

        # Set service instance for routes
        from . import routes as intervention_routes
        intervention_routes.set_service(self._service)

        # Subscribe to solving events
        event_bus = context.event_bus
        event_bus.subscribe("solving.stuck_detected", self._on_stuck_detected)
        event_bus.subscribe("solving.error_detected", self._on_error_detected)
        event_bus.subscribe("solving.step_completed", self._on_step_completed)

        context.logger.info("InterventionModule initialized")

    async def shutdown(self) -> None:
        """Shutdown the intervention module."""
        if hasattr(self, '_context') and self._context:
            self._context.logger.info("InterventionModule shutting down")

    def register_routes(self, router: "APIRouter") -> None:
        """Register API routes for the intervention module.

        Args:
            router: FastAPI APIRouter to register routes with
        """
        from . import routes as intervention_routes
        router.include_router(intervention_routes.router)

    async def _on_stuck_detected(self, event) -> None:
        """Handle solving.stuck_detected event."""
        # Could trigger intervention flow here
        pass

    async def _on_error_detected(self, event) -> None:
        """Handle solving.error_detected event."""
        pass

    async def _on_step_completed(self, event) -> None:
        """Handle solving.step_completed event."""
        pass