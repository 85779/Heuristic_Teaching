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

        # Initialize knowledge retriever for RAG-enhanced hints
        rag_service = None
        try:
            from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI
            from app.modules.knowledge_base.lightweight_retriever import LightweightRetriever
            from app.infrastructure.llm.dashscope_client import DashScopeClient
            import os

            kb = KnowledgeBaseAPI(kb_dir="data/knowledge_ontology")
            api_key = os.getenv("DASHSCOPE_API_KEY", "")
            llm = DashScopeClient(api_key=api_key, model="qwen-turbo")
            retriever = LightweightRetriever(kb_api=kb, llm_client=llm)
            # Build index in background to avoid blocking startup
            import asyncio
            asyncio.create_task(retriever.build_index())
            rag_service = retriever
            context.logger.info(f"RAG retriever initializing in background")
        except Exception:
            context.logger.warning("RAG retriever unavailable, hints will lack knowledge context")

        self._service = InterventionService(context, rag_service=rag_service)

        # Set service instance for routes
        from . import routes as intervention_routes
        intervention_routes.set_service(self._service)

        # Subscribe to solving events for automatic intervention
        event_bus = context.event_bus
        event_bus.subscribe("solving.completed", self._on_solving_completed)
        event_bus.subscribe("solving.error_detected", self._on_error_detected)
        event_bus.subscribe("solving.stuck_detected", self._on_stuck_detected)

        # Connect to Module 4 for profile updates
        self._profile_manager = None
        try:
            sm = context.registry.get_module("student_model")
            if sm and hasattr(sm, "_service"):
                self._profile_manager = sm._service
        except Exception:
            pass

        context.logger.info("InterventionModule initialized")

    async def shutdown(self) -> None:
        """Shutdown the intervention module."""
        if hasattr(self, '_context') and self._context:
            self._context.logger.info("InterventionModule shutting down")

    def register_routes(self, router: "APIRouter") -> None:
        """Register API routes for the intervention module."""
        from . import routes as intervention_routes
        router.include_router(intervention_routes.router)

    async def _on_solving_completed(self, event) -> None:
        """Auto-trigger intervention after solving completes.

        When Module 1 finishes generating a reference solution, this handler
        automatically invokes the intervention pipeline to check if the student
        needs help, and updates the student profile in Module 4.
        """
        data = event.data
        session_id = event.session_id
        evaluation = data.get("evaluation", {})
        student_work = data.get("student_work", "")
        solution_steps = data.get("solution_steps", [])

        # Only intervene if student submitted work and it had issues
        if not student_work or evaluation.get("is_correct"):
            return

        self._context.logger.info(f"Auto-intervention triggered for session {session_id}")

        try:
            from app.modules.intervention.models import InterventionRequest, InterventionType

            request = InterventionRequest(
                student_id=session_id,  # use session_id as student_id for now
                session_id=session_id,
                student_input=student_work,
                frontend_signal=None,
                intervention_type=InterventionType.HINT,
            )
            response = await self._service.create_intervention(request)

            # Update Module 4 profile with intervention result
            if self._profile_manager and response.intervention:
                from app.modules.student_model.models import InterventionRecord
                dim = getattr(response.intervention, 'dimension', 'RESOURCE')
                record = InterventionRecord(
                    intervention_id=response.intervention.id,
                    problem_id=getattr(response.intervention, 'problem_id', session_id),
                    dimension=dim if dim else "RESOURCE",
                    level=getattr(response.intervention, 'level', 'R2') or "R2",
                    outcome="MAX_ESCALATION" if not evaluation.get("can_continue") else "SOLVED",
                    intervention_count=1,
                )
                await self._profile_manager.update_after_intervention(
                    session_id, record,
                )
                self._context.logger.info(f"Profile updated for {session_id}")

        except Exception:
            self._context.logger.exception("Auto-intervention failed")

    async def _on_error_detected(self, event) -> None:
        """Handle error detected in student work — trigger intervention."""
        data = event.data
        session_id = event.session_id
        evaluation = data.get("evaluation", {})
        issues = evaluation.get("issues", [])
        if not issues:
            return

        self._context.logger.info(f"Error intervention for session {session_id}: {len(issues)} issues")
        try:
            from app.modules.intervention.models import InterventionRequest, InterventionType
            request = InterventionRequest(
                student_id=session_id, session_id=session_id,
                student_input=data.get("student_work", ""),
                frontend_signal=None, intervention_type=InterventionType.HINT,
            )
            await self._service.create_intervention(request)
            if self._profile_manager:
                from app.modules.student_model.models import InterventionRecord
                record = InterventionRecord(
                    intervention_id=f"err_{session_id}", problem_id=session_id,
                    dimension="RESOURCE", level="R1", outcome="MAX_ESCALATION",
                    intervention_count=1,
                )
                await self._profile_manager.update_after_intervention(session_id, record)
        except Exception:
            self._context.logger.exception("Error intervention failed")

    async def _on_stuck_detected(self, event) -> None:
        """Handle student stuck — trigger metacognitive intervention."""
        data = event.data
        session_id = event.session_id
        self._context.logger.info(f"Stuck intervention for session {session_id}")
        try:
            from app.modules.intervention.models import InterventionRequest, InterventionType
            request = InterventionRequest(
                student_id=session_id, session_id=session_id,
                student_input=data.get("student_input", ""),
                frontend_signal=None, intervention_type=InterventionType.HINT,
            )
            await self._service.create_intervention(request)
        except Exception:
            self._context.logger.exception("Stuck intervention failed")