"""Intervention service layer (v2) - Module 2 intervention flow.

Five-node intervention system:
  1. BreakpointLocator  (pure logic, no LLM)
  2. DimensionRouter    (Node 2a, LLM: R/M classification)
  3. SubTypeDecider     (Node 2b, LLM: level decision + escalation)
  4. HintGeneratorV2    (Node 4, LLM: R1-R4 / M1-M5 hint generation)
  5. OutputGuardrail    (Node 5, rule + LLM: output validation)
  + RAG (Module 6): Optional knowledge retrieval before hint generation
"""

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from .context_manager import ContextManager
from .locator.breaker import BreakpointLocator
from .locator.models import BreakpointLocation
from .router.dimension_router import DimensionRouter
from .decider.sub_type_decider import SubTypeDecider
from .generator.hints_v2 import HintGeneratorV2, format_student_steps
from .guardrail.guardrail import OutputGuardrail, GuardrailResult

from .models import (
    InterventionContext,
    InterventionRecord,
    InterventionRequest,
    InterventionResponse,
    Intervention,
    InterventionType,
    InterventionStatus,
    DimensionEnum,
    PromptLevelEnum,
    StudentResponseEnum,
    FrontendSignalEnum,
    FeedbackRequest,
    EscalationDecision,
)

if TYPE_CHECKING:
    from app.core.context import ModuleContext
    from app.modules.knowledge_base.service import RAGService
    from app.modules.knowledge_base.models import KGChunk


class InterventionService:
    """Service for managing v2 intervention flow.

    Five-node pipeline:
      1. BreakpointLocator  → locate breakpoint
      2. DimensionRouter    → classify R/M
      3. SubTypeDecider     → decide level + escalation
      4. HintGeneratorV2    → generate hint (+ optional RAG knowledge)
      5. OutputGuardrail     → validate output
    """

    def __init__(
        self,
        context: Optional["ModuleContext"] = None,
        enable_thinking: bool = False,
        rag_service: Optional["RAGService"] = None,
    ):
        """Initialize the intervention service.

        Args:
            context: Module context (optional, for accessing other modules/state)
            enable_thinking: Enable deep thinking mode for qwen3.5-plus (default: False)
            rag_service: Optional RAG service for knowledge retrieval (default: None)
        """
        self._context = context
        self._context_manager = ContextManager()
        self._locator = BreakpointLocator()
        self._router = DimensionRouter()
        self._decider = SubTypeDecider()
        self._generator = HintGeneratorV2()
        self._guardrail = OutputGuardrail()
        self._enable_thinking = enable_thinking
        self._rag_service = rag_service
        # In-memory store for completed interventions
        self._interventions: Dict[str, Intervention] = {}

    # =======================================================================
    # Main Entry Points
    # =======================================================================

    async def create_intervention(
        self,
        request: InterventionRequest,
    ) -> InterventionResponse:
        """Create a new intervention (first turn or new session).

        Flow:
          1. Load solving state from SessionState
          2. Run BreakpointLocator → breakpoint location
          3. Run DimensionRouter → R/M classification
          4. Run SubTypeDecider → level + escalation decision
          5. Run HintGeneratorV2 → hint content
          6. Run OutputGuardrail → validate hint
          7. Record intervention turn
          8. Return hint to student

        Args:
            request: InterventionRequest with session_id, student_id, student_input

        Returns:
            InterventionResponse with generated intervention
        """
        session_id = request.session_id
        student_id = request.student_id
        student_input = request.student_input or ""

        # Step 0: Load solving state from SessionState
        solving_state = self._load_solving_state(session_id)
        if not solving_state:
            return InterventionResponse(
                success=False,
                intervention=None,
                message=f"No solving state found for session {session_id}",
                breakpoint_location=None,
            )

        problem_context = solving_state.get("problem", "")
        solution_steps = solving_state.get("solution_steps", [])
        student_steps = solving_state.get("student_steps", [])
        student_work = solving_state.get("student_work", "")

        # Step 1: Get or create context
        ctx = self._context_manager.get_or_create_context(
            session_id=session_id,
            student_id=student_id,
            problem_context=problem_context,
            student_input=student_input,
            solution_steps=solution_steps,
            student_steps=student_steps,
        )

        # Handle frontend END signal
        if request.frontend_signal == FrontendSignalEnum.END:
            ctx.status = InterventionStatus.COMPLETED
            return InterventionResponse(
                success=True,
                intervention=None,
                message="干预已结束",
                breakpoint_location=None,
            )

        # Step 2: Run BreakpointLocator
        breakpoint_location = await self._locate_breakpoint(student_steps, solution_steps)
        self._context_manager.update_breakpoint_location(session_id, breakpoint_location)

        # If no breakpoint, return early
        breakpoint_type = breakpoint_location.breakpoint_type
        if hasattr(breakpoint_type, 'value'):
            breakpoint_type = breakpoint_type.value
        if breakpoint_type == "NO_BREAKPOINT":
            return InterventionResponse(
                success=True,
                intervention=None,
                message="学生解题步骤与参考解法一致，无断点",
                breakpoint_location=self._location_to_dict(breakpoint_location),
            )

        # Step 3: Run DimensionRouter (Node 2a)
        dimension_result = await self._router.route(
            student_input=student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            breakpoint_type=breakpoint_type,
            intervention_memory=ctx.intervention_memory,
            problem_context=problem_context,
        )
        self._context_manager.update_dimension_result(session_id, dimension_result)

        # Step 4: Run SubTypeDecider (Node 2b)
        sub_type_result = await self._decider.decide(
            dimension=dimension_result.dimension,
            student_input=student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            intervention_memory=ctx.intervention_memory,
            frontend_signal=request.frontend_signal,
            current_level=ctx.current_level,
            problem_context=problem_context,
        )
        self._context_manager.update_sub_type_result(session_id, sub_type_result)

        # Step 5: Retrieve knowledge from RAG (Module 6)
        knowledge_context = await self._retrieve_knowledge(
            problem_context=problem_context,
            expected_step=breakpoint_location.expected_step_content,
        )

        # Step 6: Run HintGeneratorV2 (Node 4)
        hint_content = await self._generator.generate(
            level=sub_type_result.sub_type,
            problem_context=problem_context,
            student_input=student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            student_steps=student_steps,
            enable_thinking=self._enable_thinking,
            knowledge_context=knowledge_context,
        )

        # Step 6: Run OutputGuardrail (Node 5)
        guardrail_result = await self._guardrail.check(
            content=hint_content,
            level=sub_type_result.sub_type.value,
        )

        # If guardrail fails, try to regenerate or use fallback
        if not guardrail_result.passed:
            # Try with a slightly more constrained prompt
            hint_content = self._fallback_hint(
                level=sub_type_result.sub_type,
                problem_context=problem_context,
                expected_step=breakpoint_location.expected_step_content,
            )

        # Step 7: Record intervention turn
        self._context_manager.record_intervention(
            session_id=session_id,
            student_q=student_input or student_work,
            system_a=hint_content,
            prompt_level=sub_type_result.sub_type.value,
            prompt_content=f"level={sub_type_result.sub_type.value}, dimension={dimension_result.dimension.value}",
            student_response=StudentResponseEnum.NOT_PROGRESSED,  # Initial response unknown
        )

        # Step 8: Apply escalation decision
        new_level = self._context_manager.apply_escalation(
            session_id,
            sub_type_result.escalation_decision,
        )

        # Step 9: Create and store intervention
        intervention = Intervention(
            id=f"int_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            session_id=session_id,
            intervention_type=InterventionType.HINT,
            status=InterventionStatus.SUGGESTED,
            content=hint_content,
            intensity=0.5,  # Intensity not used in v2
            metadata={
                "breakpoint_location": breakpoint_location.gap_description,
                "breakpoint_type": breakpoint_type,
                "dimension": dimension_result.dimension.value,
                "prompt_level": sub_type_result.sub_type.value,
                "hint_direction": sub_type_result.hint_direction,
                "reasoning": sub_type_result.reasoning,
                "escalation_action": sub_type_result.escalation_decision.action.value if sub_type_result.escalation_decision else "maintain",
                "new_level": new_level,
                "turn": self._context_manager.get_turn_count(session_id),
            },
            created_at=datetime.utcnow(),
        )

        self._interventions[intervention.id] = intervention

        # Persist to MongoDB
        await self._persist_intervention(intervention)

        return InterventionResponse(
            success=True,
            intervention=intervention,
            message=f"Generated {sub_type_result.sub_type.value} hint",
            breakpoint_location=self._location_to_dict(breakpoint_location),
        )

    async def process_feedback(
        self,
        request: FeedbackRequest,
    ) -> InterventionResponse:
        """Process student feedback (accepted/not_progressed).

        Flow:
          1. Load context from ContextManager
          2. Check frontend signal (END/ESCALATE)
          3. If ESCALATE → force escalate to next level
          4. If NOT_PROGRESSED → run escalation decision
          5. If ACCEPTED → update student steps, re-run locator
          6. Generate new hint
          7. Return new intervention

        Args:
            request: FeedbackRequest with session_id, student_input, frontend_signal

        Returns:
            InterventionResponse with new intervention (or terminal state)
        """
        session_id = request.session_id
        student_input = request.student_input or ""

        # Get existing context
        ctx = self._context_manager.get_context(session_id)
        if not ctx:
            return InterventionResponse(
                success=False,
                intervention=None,
                message=f"No active intervention found for session {session_id}",
                breakpoint_location=None,
            )

        # Handle frontend signals first
        if request.frontend_signal == FrontendSignalEnum.END:
            ctx.status = InterventionStatus.COMPLETED
            return InterventionResponse(
                success=True,
                intervention=None,
                message="学生主动结束干预",
                breakpoint_location=None,
            )

        if request.frontend_signal == FrontendSignalEnum.ESCALATE:
            new_level = self._context_manager.handle_frontend_signal(
                session_id, FrontendSignalEnum.ESCALATE
            )
            if new_level == "TERMINATED":
                return InterventionResponse(
                    success=True,
                    intervention=None,
                    message="已达到最高干预级别，干预终止",
                    breakpoint_location=None,
                )
            # Fall through to generate new hint at escalated level
            ctx.student_input = student_input
            return await self._generate_hint_at_current_level(ctx, session_id)

        # Determine student response
        # If student_input has significant new content → accepted
        student_response = self._determine_student_response(student_input, ctx)

        # Update context with new student input
        ctx.student_input = student_input

        if student_response == StudentResponseEnum.ACCEPTED:
            # Student made progress → update student steps and re-run
            # (In practice, Module 1 would update student_steps in SessionState)
            return await self._handle_student_progress(ctx, session_id, student_input)
        else:
            # Student did not progress → run escalation decision
            return await self._handle_no_progress(ctx, session_id, student_input)

    async def end_intervention(
        self,
        session_id: str,
        reason: Optional[str] = None,
    ) -> InterventionResponse:
        """End intervention (frontend END signal).

        Args:
            session_id: Session identifier
            reason: Optional end reason

        Returns:
            InterventionResponse
        """
        ctx = self._context_manager.get_context(session_id)
        if ctx:
            ctx.status = InterventionStatus.COMPLETED

        return InterventionResponse(
            success=True,
            intervention=None,
            message=f"干预已结束: {reason or '学生主动结束'}",
            breakpoint_location=None,
        )

    async def escalate_intervention(
        self,
        session_id: str,
        reason: Optional[str] = None,
    ) -> InterventionResponse:
        """Force escalate intervention (frontend ESCALATE signal).

        Args:
            session_id: Session identifier
            reason: Optional escalation reason

        Returns:
            InterventionResponse with escalated intervention
        """
        ctx = self._context_manager.get_context(session_id)
        if not ctx:
            return InterventionResponse(
                success=False,
                intervention=None,
                message=f"No active intervention found for session {session_id}",
                breakpoint_location=None,
            )

        # Handle frontend ESCALATE signal
        new_level = self._context_manager.handle_frontend_signal(
            session_id, FrontendSignalEnum.ESCALATE
        )

        if new_level == "TERMINATED":
            return InterventionResponse(
                success=True,
                intervention=None,
                message="已达到最高干预级别，干预终止",
                breakpoint_location=None,
            )

        return await self._generate_hint_at_current_level(ctx, session_id)

    # =======================================================================
    # Helper Methods
    # =======================================================================

    def _load_solving_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load solving state from SessionState.

        Args:
            session_id: Session identifier

        Returns:
            Solving state dict or None
        """
        if self._context is None:
            return None

        try:
            state = self._context.state_manager.get_module_state(session_id, "solving")
            return state
        except Exception:
            return None

    def _format_knowledge_context(
        self,
        chunks: List["KGChunk"],
    ) -> str:
        """Format retrieved knowledge chunks as a context string.

        Args:
            chunks: List of KGChunk objects from RAG retrieval.

        Returns:
            Formatted knowledge context string for prompt injection.
        """
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks[:3], 1):
            content = chunk.content
            metadata = chunk.metadata or {}
            chapter = metadata.get("chapter", "")
            chunk_type = metadata.get("type", "知识点")
            header = f"【知识点 {i}】（{chunk_type}）"
            if chapter:
                header += f" — {chapter}"
            context_parts.append(f"{header}\n{content}")

        return "\n\n".join(context_parts)

    async def _retrieve_knowledge(
        self,
        problem_context: str,
        expected_step: str,
        top_k: int = 3,
    ) -> str:
        """Retrieve relevant knowledge chunks from RAG service.

        Args:
            problem_context: Problem text for retrieval query.
            expected_step: Expected next step for targeted retrieval.
            top_k: Number of chunks to retrieve (default: 3).

        Returns:
            Formatted knowledge context string, or empty string if RAG unavailable.
        """
        if self._rag_service is None:
            return ""

        try:
            # Combine problem and expected step as query for better retrieval
            query = f"{problem_context}\n\n下一步: {expected_step}"
            chunks = await self._rag_service.retrieve(
                query=query,
                top_k=top_k,
            )
            return self._format_knowledge_context(chunks)
        except Exception:
            # RAG failures should not break the intervention flow
            return ""

    async def _locate_breakpoint(
        self,
        student_steps: List[Dict[str, Any]],
        solution_steps: List[Dict[str, Any]],
    ) -> BreakpointLocation:
        """Locate breakpoint using BreakpointLocator.

        Args:
            student_steps: Student's steps
            solution_steps: Reference solution steps

        Returns:
            BreakpointLocation
        """
        # Convert to TeachingStep-like objects
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

        return self._locator.locate(student_steps_obj, solution_steps_obj)

    async def _persist_intervention(self, intervention: Intervention) -> None:
        """Save intervention to MongoDB.

        Args:
            intervention: Intervention to persist
        """
        try:
            from app.infrastructure.database.repositories.intervention_repo import InterventionRepository
            if not hasattr(self, '_intervention_repo'):
                self._intervention_repo = InterventionRepository()
            # Serialize intervention, handling any enum values
            intervention_dict = intervention.model_dump(mode='json')
            await self._intervention_repo.save_intervention(intervention_dict)
        except Exception as e:
            # Log but don't fail - graceful degradation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to persist intervention {intervention.id}: {e}")

    async def _generate_hint_at_current_level(
        self,
        ctx: InterventionContext,
        session_id: str,
    ) -> InterventionResponse:
        """Generate hint at current intervention level.

        Args:
            ctx: InterventionContext
            session_id: Session identifier

        Returns:
            InterventionResponse with generated hint
        """
        # Load solving state
        solving_state = self._load_solving_state(session_id)
        if not solving_state:
            return InterventionResponse(
                success=False,
                intervention=None,
                message=f"No solving state found for session {session_id}",
                breakpoint_location=None,
            )

        problem_context = solving_state.get("problem", "")
        solution_steps = solving_state.get("solution_steps", [])
        student_steps = solving_state.get("student_steps", [])
        student_work = solving_state.get("student_work", "")

        # Re-run locator if student_steps changed
        breakpoint_location = await self._locate_breakpoint(student_steps, solution_steps)
        self._context_manager.update_breakpoint_location(session_id, breakpoint_location)

        # Extract breakpoint_type as string (handle both enum and string)
        breakpoint_type_str = breakpoint_location.breakpoint_type
        if hasattr(breakpoint_type_str, 'value'):
            breakpoint_type_str = breakpoint_type_str.value

        # Get current level
        current_level_str = ctx.current_level
        try:
            current_level = PromptLevelEnum(current_level_str)
        except ValueError:
            current_level = PromptLevelEnum.R1

        # Determine dimension from level prefix
        if current_level_str.startswith("R"):
            dimension = DimensionEnum.RESOURCE
        else:
            dimension = DimensionEnum.METACOGNITIVE

        # Retrieve knowledge from RAG
        knowledge_context = await self._retrieve_knowledge(
            problem_context=problem_context,
            expected_step=breakpoint_location.expected_step_content,
        )

        # Generate hint at current level
        hint_content = await self._generator.generate(
            level=current_level,
            problem_context=problem_context,
            student_input=ctx.student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            student_steps=student_steps,
            enable_thinking=self._enable_thinking,
            knowledge_context=knowledge_context,
        )

        # Guardrail check
        guardrail_result = await self._guardrail.check(
            content=hint_content,
            level=current_level_str,
        )

        if not guardrail_result.passed:
            hint_content = self._fallback_hint(
                level=current_level,
                problem_context=problem_context,
                expected_step=breakpoint_location.expected_step_content,
            )

        # Record intervention
        self._context_manager.record_intervention(
            session_id=session_id,
            student_q=ctx.student_input or student_work,
            system_a=hint_content,
            prompt_level=current_level_str,
            prompt_content=f"level={current_level_str}, dimension={dimension.value}",
            student_response=StudentResponseEnum.NOT_PROGRESSED,
        )

        # Create intervention
        intervention = Intervention(
            id=f"int_{uuid.uuid4().hex[:8]}",
            student_id=ctx.student_id,
            session_id=session_id,
            intervention_type=InterventionType.HINT,
            status=InterventionStatus.SUGGESTED,
            content=hint_content,
            intensity=0.5,
            metadata={
                "breakpoint_location": breakpoint_location.gap_description,
                "breakpoint_type": breakpoint_type_str,
                "dimension": dimension.value,
                "prompt_level": current_level_str,
                "turn": self._context_manager.get_turn_count(session_id),
                "mode": "escalation",
            },
            created_at=datetime.utcnow(),
        )

        self._interventions[intervention.id] = intervention

        # Persist to MongoDB
        await self._persist_intervention(intervention)

        return InterventionResponse(
            success=True,
            intervention=intervention,
            message=f"Generated escalated {current_level_str} hint",
            breakpoint_location=self._location_to_dict(breakpoint_location),
        )

    async def _handle_student_progress(
        self,
        ctx: InterventionContext,
        session_id: str,
        student_input: str,
    ) -> InterventionResponse:
        """Handle student making progress (accepted).

        When student provides new content that differs from their previous input,
        we treat it as PROGRESSED. However, we must re-run BreakpointLocator
        to check if they've moved past the old breakpoint or encountered a NEW
        one at a different position.

        Args:
            ctx: InterventionContext
            session_id: Session identifier
            student_input: Student's new input

        Returns:
            InterventionResponse — continues with new hint if new breakpoint found,
            or ends if student has resolved the breakpoint.
        """
        # Step 1: Update student_steps in context with new input
        # (In production, Module 1 would do this; here we append as a new step)
        solving_state = self._load_solving_state(session_id)
        if solving_state:
            student_steps = solving_state.get("student_steps", [])
            solution_steps = solving_state.get("solution_steps", [])
            problem_context = solving_state.get("problem", "")
            student_work = solving_state.get("student_work", "")

            # Append new student input as a step
            new_step = {
                "step_id": f"s{len(student_steps) + 1}",
                "step_name": "学生推进",
                "content": student_input,
            }
            updated_student_steps = student_steps + [new_step]

            # Update in-memory context
            ctx.student_steps = updated_student_steps

            # Step 2: Re-run BreakpointLocator to check for new breakpoint
            breakpoint_location = await self._locate_breakpoint(
                updated_student_steps, solution_steps
            )
            self._context_manager.update_breakpoint_location(session_id, breakpoint_location)

            # Check breakpoint type safely
            breakpoint_type = breakpoint_location.breakpoint_type
            if hasattr(breakpoint_type, 'value'):
                breakpoint_type = breakpoint_type.value

            # Step 3: If new breakpoint found, continue intervention
            if breakpoint_type != "NO_BREAKPOINT":
                # Re-run dimension router for the new breakpoint
                dimension_result = await self._router.route(
                    student_input=student_input,
                    expected_step=breakpoint_location.expected_step_content,
                    breakpoint_type=breakpoint_type,
                    intervention_memory=ctx.intervention_memory,
                    problem_context=problem_context,
                )
                self._context_manager.update_dimension_result(session_id, dimension_result)

                # Re-run sub-type decider
                sub_type_result = await self._decider.decide(
                    dimension=dimension_result.dimension,
                    student_input=student_input,
                    expected_step=breakpoint_location.expected_step_content,
                    intervention_memory=ctx.intervention_memory,
                    frontend_signal=None,
                    current_level=ctx.current_level,
                    problem_context=problem_context,
                )
                self._context_manager.update_sub_type_result(session_id, sub_type_result)

                # Retrieve knowledge from RAG
                knowledge_context = await self._retrieve_knowledge(
                    problem_context=problem_context,
                    expected_step=breakpoint_location.expected_step_content,
                )

                # Generate new hint
                hint_content = await self._generator.generate(
                    level=sub_type_result.sub_type,
                    problem_context=problem_context,
                    student_input=student_input,
                    expected_step=breakpoint_location.expected_step_content,
                    student_steps=updated_student_steps,
                    enable_thinking=self._enable_thinking,
                    knowledge_context=knowledge_context,
                )

                # Guardrail check
                guardrail_result = await self._guardrail.check(
                    content=hint_content,
                    level=sub_type_result.sub_type.value,
                )
                if not guardrail_result.passed:
                    hint_content = guardrail_result.revised_content or self._fallback_hint(
                        level=sub_type_result.sub_type,
                        problem_context=problem_context,
                        expected_step=breakpoint_location.expected_step_content,
                    )

                # Record
                self._context_manager.record_intervention(
                    session_id=session_id,
                    student_q=student_input,
                    system_a=hint_content,
                    prompt_level=sub_type_result.sub_type.value,
                    prompt_content=f"level={sub_type_result.sub_type.value}",
                    student_response=StudentResponseEnum.ACCEPTED,
                )

                # Create intervention
                intervention = Intervention(
                    id=f"int_{uuid.uuid4().hex[:8]}",
                    student_id=ctx.student_id,
                    session_id=session_id,
                    intervention_type=InterventionType.HINT,
                    status=InterventionStatus.SUGGESTED,
                    content=hint_content,
                    intensity=0.5,
                    metadata={
                        "breakpoint_location": breakpoint_location.gap_description,
                        "breakpoint_type": breakpoint_type,
                        "dimension": dimension_result.dimension.value,
                        "prompt_level": sub_type_result.sub_type.value,
                        "reasoning": sub_type_result.reasoning,
                        "turn": self._context_manager.get_turn_count(session_id),
                        "mode": "continue_after_progress",
                    },
                )
                self._interventions[intervention.id] = intervention
                await self._persist_intervention(intervention)

                return InterventionResponse(
                    success=True,
                    intervention=intervention,
                    message=f"学生已推进到下一步，继续干预（新断点: {breakpoint_type} @ pos {breakpoint_location.breakpoint_position}）",
                    breakpoint_location=self._location_to_dict(breakpoint_location),
                )

        # Step 4: No new breakpoint found → student has resolved the original or completed
        ctx.status = InterventionStatus.COMPLETED

        return InterventionResponse(
            success=True,
            intervention=None,
            message="学生已成功推进，原断点已解除，干预结束",
            breakpoint_location=None,
        )

    async def _handle_no_progress(
        self,
        ctx: InterventionContext,
        session_id: str,
        student_input: str,
    ) -> InterventionResponse:
        """Handle student not making progress.

        Args:
            ctx: InterventionContext
            session_id: Session identifier
            student_input: Student's input

        Returns:
            InterventionResponse with escalated intervention
        """
        # Load solving state
        solving_state = self._load_solving_state(session_id)
        if not solving_state:
            return InterventionResponse(
                success=False,
                intervention=None,
                message=f"No solving state found for session {session_id}",
                breakpoint_location=None,
            )

        problem_context = solving_state.get("problem", "")
        solution_steps = solving_state.get("solution_steps", [])
        student_steps = solving_state.get("student_steps", [])
        student_work = solving_state.get("student_work", "")

        # Re-run locator
        breakpoint_location = await self._locate_breakpoint(student_steps, solution_steps)

        # Get dimension from context
        dimension = ctx.dimension_result.dimension if ctx.dimension_result else DimensionEnum.RESOURCE

        # Extract breakpoint_type safely (handle both enum and string)
        breakpoint_type_str = breakpoint_location.breakpoint_type
        if hasattr(breakpoint_type_str, 'value'):
            breakpoint_type_str = breakpoint_type_str.value

        # Re-run decider to get escalation decision
        sub_type_result = await self._decider.decide(
            dimension=dimension,
            student_input=student_input or ctx.student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            intervention_memory=ctx.intervention_memory,
            frontend_signal=None,
            current_level=ctx.current_level,
            problem_context=problem_context,
        )

        # Apply escalation
        new_level = self._context_manager.apply_escalation(
            session_id, sub_type_result.escalation_decision
        )

        if new_level == "TERMINATED":
            return InterventionResponse(
                success=True,
                intervention=None,
                message="已达到最高干预级别，干预终止",
                breakpoint_location=self._location_to_dict(breakpoint_location),
            )

        # Update sub_type_result with new level
        self._context_manager.update_sub_type_result(session_id, sub_type_result)

        # Retrieve knowledge from RAG
        knowledge_context = await self._retrieve_knowledge(
            problem_context=problem_context,
            expected_step=breakpoint_location.expected_step_content,
        )

        # Generate hint at new level
        hint_content = await self._generator.generate(
            level=sub_type_result.sub_type,
            problem_context=problem_context,
            student_input=student_input or ctx.student_input or student_work,
            expected_step=breakpoint_location.expected_step_content,
            student_steps=student_steps,
            enable_thinking=self._enable_thinking,
            knowledge_context=knowledge_context,
        )

        # Guardrail check
        guardrail_result = await self._guardrail.check(
            content=hint_content,
            level=sub_type_result.sub_type.value,
        )

        if not guardrail_result.passed:
            hint_content = self._fallback_hint(
                level=sub_type_result.sub_type,
                problem_context=problem_context,
                expected_step=breakpoint_location.expected_step_content,
            )

        # Record intervention
        self._context_manager.record_intervention(
            session_id=session_id,
            student_q=student_input or ctx.student_input or student_work,
            system_a=hint_content,
            prompt_level=new_level,
            prompt_content=f"level={new_level}, dimension={dimension.value}",
            student_response=StudentResponseEnum.NOT_PROGRESSED,
        )

        # Create intervention
        intervention = Intervention(
            id=f"int_{uuid.uuid4().hex[:8]}",
            student_id=ctx.student_id,
            session_id=session_id,
            intervention_type=InterventionType.HINT,
            status=InterventionStatus.SUGGESTED,
            content=hint_content,
            intensity=0.5,
            metadata={
                "breakpoint_location": breakpoint_location.gap_description,
                "breakpoint_type": breakpoint_type_str,
                "dimension": dimension.value,
                "prompt_level": new_level,
                "reasoning": sub_type_result.reasoning,
                "escalation_action": sub_type_result.escalation_decision.action.value if sub_type_result.escalation_decision else "maintain",
                "turn": self._context_manager.get_turn_count(session_id),
                "mode": "escalation",
            },
            created_at=datetime.utcnow(),
        )

        self._interventions[intervention.id] = intervention

        # Persist to MongoDB
        await self._persist_intervention(intervention)

        return InterventionResponse(
            success=True,
            intervention=intervention,
            message=f"Generated escalated {new_level} hint",
            breakpoint_location=self._location_to_dict(breakpoint_location),
        )

    def _determine_student_response(
        self,
        student_input: str,
        ctx: InterventionContext,
    ) -> StudentResponseEnum:
        """Determine if student made progress.

        Args:
            student_input: Student's new input
            ctx: InterventionContext

        Returns:
            StudentResponseEnum.ACCEPTED if progress, NOT_PROGRESSED otherwise
        """
        if not student_input or student_input.strip() == "":
            return StudentResponseEnum.NOT_PROGRESSED

        # If student_input is significantly different from last input → progress
        if ctx.student_input and student_input != ctx.student_input:
            # Simple heuristic: if student provided new content, assume progress
            if len(student_input.strip()) > 10:
                return StudentResponseEnum.ACCEPTED

        return StudentResponseEnum.NOT_PROGRESSED

    def _fallback_hint(
        self,
        level: PromptLevelEnum,
        problem_context: str,
        expected_step: str,
    ) -> str:
        """Generate a fallback hint when guardrail fails.

        Args:
            level: Prompt level
            problem_context: Problem text
            expected_step: Expected next step

        Returns:
            Fallback hint content
        """
        level_str = level.value

        fallback_map = {
            "R1": "回顾一下题目中的已知条件，思考它们和所求目标之间有什么关系？",
            "R2": "思考一下解决这个问题可能需要用到哪些数学定理或方法。",
            "R3": "尝试从已知条件出发，先求出某个中间量。",
            "R4": f"参考步骤：{expected_step[:50]}..." if expected_step else "请仔细阅读参考解法的下一步。",
            "M1": "你觉得当前的解题方向是否正确？是否应该尝试其他方法？",
            "M2": "尝试从不同的角度来思考这个问题。",
            "M3": "考虑使用换元法或者数学归纳法来推进。",
            "M4": "尝试分解问题为更小的子问题来解决。",
            "M5": "参考类似题目的解法，尝试套用相同的思路。",
        }

        return fallback_map.get(level_str, "请仔细思考题目中的条件。")

    @staticmethod
    def _location_to_dict(location: BreakpointLocation) -> Dict[str, Any]:
        """Convert BreakpointLocation to dict for response.

        Args:
            location: BreakpointLocation

        Returns:
            Dict representation
        """
        breakpoint_type = location.breakpoint_type
        if hasattr(breakpoint_type, 'value'):
            breakpoint_type = breakpoint_type.value
        return {
            "breakpoint_position": location.breakpoint_position,
            "breakpoint_type": breakpoint_type,
            "expected_step_content": location.expected_step_content,
            "gap_description": location.gap_description,
            "student_last_step": location.student_last_step,
        }

    # =======================================================================
    # Legacy Methods (for backward compatibility)
    # =======================================================================

    async def generate(
        self,
        session_id: str,
        intensity: float = 0.5,
        student_work: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> Intervention:
        """Legacy generate method (backward compatibility).

        For new code, use create_intervention() instead.
        """
        request = InterventionRequest(
            student_id=student_id or "unknown",
            session_id=session_id,
            student_input=student_work or "",
            frontend_signal=None,
            intervention_type=InterventionType.HINT,
        )
        response = await self.create_intervention(request)
        if response.intervention:
            return response.intervention
        raise ValueError(response.message)

    async def record_intervention_outcome(
        self,
        intervention_id: str,
        outcome: str,
    ) -> None:
        """Record intervention outcome (legacy method).

        For new code, use process_feedback() instead.
        """
        intervention = self._interventions.get(intervention_id)
        if intervention:
            intervention.status = InterventionStatus(outcome)
            intervention.outcome_at = datetime.utcnow()
            # Persist to MongoDB
            await self._persist_intervention(intervention)

    async def analyze_student_state(
        self,
        student_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Analyze student state (stub for backward compatibility)."""
        return {
            "student_id": student_id,
            "session_id": session_id,
            "current_step": None,
            "error_count": 0,
        }

    async def determine_intervention_type(self, analysis: Dict[str, Any]) -> str:
        """Determine intervention type (stub for backward compatibility)."""
        return "hint"

    async def calculate_intensity(self, analysis: Dict[str, Any]) -> float:
        """Calculate intensity (stub for backward compatibility)."""
        return 0.5

    async def generate_intervention(
        self,
        analysis: Dict[str, Any],
        intervention_type: str,
    ) -> Dict[str, Any]:
        """Generate intervention (stub for backward compatibility)."""
        return {"content": "Intervention content", "type": intervention_type}

    async def deliver_intervention(
        self,
        intervention_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Deliver intervention (stub for backward compatibility)."""
        intervention = self._interventions.get(intervention_id)
        if intervention:
            intervention.status = InterventionStatus.DELIVERED
            intervention.delivered_at = datetime.utcnow()
        return {
            "delivered": intervention is not None,
            "intervention_id": intervention_id,
        }
