"""Student model module implementation."""

from app.core.interfaces.module import IModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from app.core.context import ModuleContext


class StudentModelModule(IModule):
    """Module 4: Student cognitive profile system.

    Maintains per-student dimension_ratio, intervention history,
    and provides routing hints for Modules 2, 3, and 5.
    """

    @property
    def module_id(self) -> str:
        return "student_model"

    @property
    def module_name(self) -> str:
        return "Student Model Module"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []  # no hard dependencies — works standalone

    @property
    def provides_events(self) -> list[str]:
        return ["student_model.updated", "student_model.knowledge_gap_detected"]

    @property
    def subscribes_events(self) -> list[str]:
        return ["intervention.completed"]  # Module 2 writes to us

    async def initialize(self, context: "ModuleContext") -> None:
        self._context = context
        self._logger = context.logger

        from app.modules.student_model.service import ProfileManager
        self._service = ProfileManager()

        # Ensure indexes
        from app.modules.student_model.repository import StudentProfileRepository
        repo = StudentProfileRepository()
        await repo.ensure_indexes()

        from . import routes as student_routes
        student_routes.set_service(self._service)

        # Subscribe to solving completed events for auto profile tracking
        context.event_bus.subscribe("solving.completed", self._on_solving_completed)
        context.event_bus.subscribe("intervention.completed", self._on_intervention_completed)

        self._logger.info("StudentModelModule initialized")

    async def shutdown(self) -> None:
        pass

    def register_routes(self, router: "APIRouter") -> None:
        from . import routes as student_routes
        router.include_router(student_routes.router)

    async def _on_solving_completed(self, event) -> None:
        """Track solving activity in student profile."""
        data = event.data
        session_id = event.session_id
        evaluation = data.get("evaluation", {})

        if evaluation.get("is_correct") and evaluation.get("confidence", 0) > 0.5:
            from app.modules.student_model.models import InterventionRecord
            record = InterventionRecord(
                intervention_id=f"auto_{session_id}",
                problem_id=session_id,
                dimension="RESOURCE",
                level="R1",
                outcome="SOLVED",
                intervention_count=0,
            )
            try:
                await self._service.update_after_intervention(session_id, record)
            except Exception:
                pass

    async def _on_intervention_completed(self, event) -> None:
        """Handle intervention completion from Module 2."""
        pass
