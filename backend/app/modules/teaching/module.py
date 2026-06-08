"""Teaching strategy module implementation."""

from app.core.interfaces.module import IModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from app.core.context import ModuleContext


class TeachingModule(IModule):
    """Module 5: Teaching strategy selection.

    Provides personalized teaching strategies (lecture/practice/discussion
    ratios) based on student cognitive profiles from Module 4.
    """

    @property
    def module_id(self) -> str:
        return "teaching"

    @property
    def module_name(self) -> str:
        return "Teaching Strategy Module"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return ["student_model"]

    @property
    def provides_events(self) -> list[str]:
        return ["teaching.strategy_selected"]

    @property
    def subscribes_events(self) -> list[str]:
        return []

    async def initialize(self, context: "ModuleContext") -> None:
        self._context = context
        self._logger = context.logger

        # Get ProfileManager from Module 4
        profile_manager = None
        try:
            sm = context.registry.get_module("student_model")
            if sm and hasattr(sm, "_service"):
                profile_manager = sm._service
        except Exception:
            self._logger.warning("Module 4 not available, using default strategies")

        from app.modules.teaching.service import StrategySelector
        self._service = StrategySelector(profile_manager=profile_manager)

        from . import routes as teaching_routes
        teaching_routes.set_service(self._service)

        self._logger.info("TeachingModule initialized")

    async def shutdown(self) -> None:
        pass

    def register_routes(self, router: "APIRouter") -> None:
        from . import routes as teaching_routes
        router.include_router(teaching_routes.router)
