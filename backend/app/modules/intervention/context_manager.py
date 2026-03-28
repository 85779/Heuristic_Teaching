"""Context Manager for Module 2 intervention state.

Manages InterventionContext across the entire intervention lifecycle:
- Create/restore context per session
- Update breakpoint, dimension, sub-type results
- Apply escalation/switching decisions
- Record intervention history
- Persist to MongoDB
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import (
    InterventionContext,
    InterventionRecord,
    BreakpointLocation,
    DimensionResult,
    SubTypeResult,
    EscalationDecision,
    EscalationAction,
    InterventionStatus,
    DimensionEnum,
    PromptLevelEnum,
    StudentResponseEnum,
    FrontendSignalEnum,
    QaHistory,
)

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages intervention context lifecycle.

    In-memory store with MongoDB persistence.
    """

    def __init__(self):
        """Initialize the context manager."""
        # In-memory store: session_id -> InterventionContext
        self._contexts: Dict[str, InterventionContext] = {}
        # Turn counter per session
        self._turn_counters: Dict[str, int] = {}
        # Singleton repo instance for MongoDB
        self._repo = None

    # =======================================================================
    # Context Lifecycle
    # =======================================================================

    async def persist_context(self, session_id: str) -> None:
        """Persist context to MongoDB.

        Args:
            session_id: Session identifier
        """
        try:
            from app.infrastructure.database.repositories.intervention_repo import InterventionRepository
            self._repo = self._repo or InterventionRepository()
            await self._repo.upsert_context(session_id, self.save_context(session_id))
        except Exception as e:
            logger.warning(f"Failed to persist context for session {session_id}: {e}")

    async def load_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load context from MongoDB.

        Args:
            session_id: Session identifier

        Returns:
            Optional[Dict[str, Any]]: The context dict if found, None otherwise
        """
        try:
            from app.infrastructure.database.repositories.intervention_repo import InterventionRepository
            self._repo = self._repo or InterventionRepository()
            return await self._repo.get_latest_context(session_id)
        except Exception as e:
            logger.warning(f"Failed to load context for session {session_id}: {e}")
            return None

    def get_or_create_context(
        self,
        session_id: str,
        student_id: str,
        problem_context: str,
        student_input: str,
        solution_steps: List[Dict[str, Any]],
        student_steps: List[Dict[str, Any]],
        persist: bool = True,
    ) -> InterventionContext:
        """Get existing context or create new one for session.

        Args:
            session_id: Session identifier
            student_id: Student identifier
            problem_context: Problem text
            student_input: Student's current input
            solution_steps: Reference solution steps
            student_steps: Student's steps so far
            persist: Whether to persist to MongoDB (default True)

        Returns:
            InterventionContext for this session
        """
        if session_id in self._contexts:
            ctx = self._contexts[session_id]
            # Update student_input for new turn
            ctx.student_input = student_input
            return ctx

        # Create new context
        ctx = InterventionContext(
            session_id=session_id,
            student_id=student_id,
            problem_context=problem_context,
            student_input=student_input,
            solution_steps=solution_steps,
            student_steps=student_steps,
            breakpoint_location=None,
            dimension_result=None,
            sub_type_result=None,
            intervention_memory=[],
            current_level="",
            status=InterventionStatus.ACTIVE,
        )
        self._contexts[session_id] = ctx
        self._turn_counters[session_id] = 0

        # Persist new context if requested
        if persist:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.persist_context(session_id))
                else:
                    loop.run_until_complete(self.persist_context(session_id))
            except Exception as e:
                logger.warning(f"Failed to persist new context for session {session_id}: {e}")

        return ctx

    def get_context(self, session_id: str) -> Optional[InterventionContext]:
        """Get existing context for session.

        Args:
            session_id: Session identifier

        Returns:
            InterventionContext if exists, None otherwise
        """
        return self._contexts.get(session_id)

    def restore_from_session(
        self,
        session_id: str,
        student_id: str,
        problem_context: str,
        solution_steps: List[Dict[str, Any]],
        student_steps: List[Dict[str, Any]],
        **kwargs,
    ) -> InterventionContext:
        """Restore context from stored state (e.g., from MongoDB).

        Args:
            session_id: Session identifier
            student_id: Student identifier
            problem_context: Problem text
            solution_steps: Reference solution steps
            student_steps: Student's steps
            **kwargs: Additional fields (current_level, intervention_memory, etc.)

        Returns:
            Restored InterventionContext
        """
        memory = kwargs.get("intervention_memory", [])
        current_level = kwargs.get("current_level", "")
        status_str = kwargs.get("status", "active")

        try:
            status = InterventionStatus(status_str)
        except ValueError:
            status = InterventionStatus.ACTIVE

        # Restore InterventionRecord objects from dicts
        restored_memory = []
        for r in memory:
            if isinstance(r, dict):
                qa_history_dict = r.get("qa_history", {})
                if isinstance(qa_history_dict, dict):
                    qa_history = QaHistory(
                        student_q=qa_history_dict.get("student_q", ""),
                        system_a=qa_history_dict.get("system_a", ""),
                    )
                else:
                    qa_history = QaHistory(student_q="", system_a="")

                restored_memory.append(InterventionRecord(
                    turn=r.get("turn", 0),
                    qa_history=qa_history,
                    prompt_level=r.get("prompt_level", ""),
                    prompt_content=r.get("prompt_content", ""),
                    student_response=StudentResponseEnum(r.get("student_response", "not_progressed")),
                    frontend_signal=FrontendSignalEnum(r["frontend_signal"]) if r.get("frontend_signal") else None,
                    breakpoint_status=r.get("breakpoint_status", "persistent"),
                    created_at=r.get("created_at", datetime.utcnow()),
                ))
            else:
                restored_memory.append(r)

        ctx = InterventionContext(
            session_id=session_id,
            student_id=student_id,
            problem_context=problem_context,
            student_input="",
            solution_steps=solution_steps,
            student_steps=student_steps,
            breakpoint_location=None,
            dimension_result=None,
            sub_type_result=None,
            intervention_memory=restored_memory,
            current_level=current_level,
            status=status,
        )

        self._contexts[session_id] = ctx
        self._turn_counters[session_id] = len(restored_memory)
        return ctx

    def save_context(self, session_id: str) -> Dict[str, Any]:
        """Serialize context for MongoDB storage.

        Args:
            session_id: Session identifier

        Returns:
            Dict ready for MongoDB storage
        """
        ctx = self._contexts.get(session_id)
        if not ctx:
            return {}

        memory_dicts = []
        for r in ctx.intervention_memory:
            if isinstance(r, dict):
                memory_dicts.append(r)
            else:
                memory_dicts.append({
                    "turn": r.turn,
                    "qa_history": {
                        "student_q": r.qa_history.student_q,
                        "system_a": r.qa_history.system_a,
                    },
                    "prompt_level": r.prompt_level,
                    "prompt_content": r.prompt_content,
                    "student_response": r.student_response.value,
                    "frontend_signal": r.frontend_signal.value if r.frontend_signal else None,
                    "breakpoint_status": r.breakpoint_status,
                    "created_at": r.created_at,
                })

        return {
            "session_id": session_id,
            "student_id": ctx.student_id,
            "problem_context": ctx.problem_context,
            "current_level": ctx.current_level,
            "status": ctx.status.value,
            "intervention_memory": memory_dicts,
            "breakpoint_location": None,
            "dimension_result": None,
            "sub_type_result": None,
            "updated_at": datetime.utcnow(),
        }

    # =======================================================================
    # State Updates
    # =======================================================================

    def update_breakpoint_location(
        self,
        session_id: str,
        location: BreakpointLocation,
    ) -> None:
        """Update breakpoint location for session.

        Args:
            session_id: Session identifier
            location: BreakpointLocation from locator
        """
        ctx = self._contexts.get(session_id)
        if ctx:
            ctx.breakpoint_location = location

    def update_dimension_result(
        self,
        session_id: str,
        result: DimensionResult,
    ) -> None:
        """Update dimension routing result.

        Args:
            session_id: Session identifier
            result: DimensionResult from Node 2a
        """
        ctx = self._contexts.get(session_id)
        if ctx:
            ctx.dimension_result = result

    def update_sub_type_result(
        self,
        session_id: str,
        result: SubTypeResult,
    ) -> None:
        """Update sub-type decision result.

        Args:
            session_id: Session identifier
            result: SubTypeResult from Node 2b
        """
        ctx = self._contexts.get(session_id)
        if ctx:
            ctx.sub_type_result = result
            ctx.current_level = result.sub_type.value

    def update_student_steps(
        self,
        session_id: str,
        student_steps: List[Dict[str, Any]],
    ) -> None:
        """Update student steps (after student makes progress).

        Args:
            session_id: Session identifier
            student_steps: Updated student steps
        """
        ctx = self._contexts.get(session_id)
        if ctx:
            ctx.student_steps = student_steps

    # =======================================================================
    # Intervention History
    # =======================================================================

    def record_intervention(
        self,
        session_id: str,
        student_q: str,
        system_a: str,
        prompt_level: str,
        prompt_content: str,
        student_response: StudentResponseEnum,
        frontend_signal: Optional[FrontendSignalEnum] = None,
        breakpoint_status: str = "persistent",
    ) -> InterventionRecord:
        """Record an intervention turn.

        Args:
            session_id: Session identifier
            student_q: Student's question/behavior
            system_a: System's hint content
            prompt_level: Current prompt level (R1-R4 / M1-M5)
            prompt_content: Full prompt sent to LLM
            student_response: Student's response (accepted/not_progressed)
            frontend_signal: Optional frontend signal (END/ESCALATE)
            breakpoint_status: "resolved" or "persistent"

        Returns:
            Created InterventionRecord
        """
        ctx = self._contexts.get(session_id)
        if not ctx:
            raise ValueError(f"No context found for session {session_id}")

        # Increment turn counter
        turn = self._turn_counters.get(session_id, 0) + 1
        self._turn_counters[session_id] = turn

        record = InterventionRecord(
            turn=turn,
            qa_history=QaHistory(student_q=student_q, system_a=system_a),
            prompt_level=prompt_level,
            prompt_content=prompt_content,
            student_response=student_response,
            frontend_signal=frontend_signal,
            breakpoint_status=breakpoint_status,
            created_at=datetime.utcnow(),
        )

        ctx.intervention_memory.append(record)

        # Persist to MongoDB (fire-and-forget)
        self._schedule_persist(session_id)

        return record

    # =======================================================================
    # Escalation & Switching Logic
    # =======================================================================

    def apply_escalation(
        self,
        session_id: str,
        decision: EscalationDecision,
    ) -> str:
        """Apply escalation decision, handle switching.

        This implements the PRD escalation logic:
        - MAINTAIN: stay at current level
        - ESCALATE: move to next level in same dimension
        - SWITCH_TO_RESOURCE: switch from M to R at R1
        - MAX_LEVEL_REACHED: terminate intervention

        Args:
            session_id: Session identifier
            decision: EscalationDecision from Node 2b

        Returns:
            New level string (or "TERMINATED")
        """
        ctx = self._contexts.get(session_id)
        if not ctx:
            return ""

        action = decision.action

        if action == EscalationAction.MAINTAIN:
            # Stay at current level
            return ctx.current_level

        elif action == EscalationAction.ESCALATE:
            # Move to next level in same dimension
            new_level = decision.to_level
            if new_level:
                ctx.current_level = new_level
                self._schedule_persist(session_id)
                return new_level
            # Compute next level if not provided
            current = ctx.current_level
            if current.startswith("R"):
                next_r = _next_resource_level(current)
                ctx.current_level = next_r
                self._schedule_persist(session_id)
                return next_r
            elif current.startswith("M"):
                next_m = _next_metacognitive_level(current)
                ctx.current_level = next_m
                self._schedule_persist(session_id)
                return next_m
            return current

        elif action == EscalationAction.SWITCH_TO_RESOURCE:
            # M-side failure → switch to R-side from R1
            ctx.current_level = PromptLevelEnum.R1.value
            ctx.dimension_result = None  # Clear dimension result for new routing
            self._schedule_persist(session_id)
            return PromptLevelEnum.R1.value

        elif action == EscalationAction.MAX_LEVEL_REACHED:
            # R-side R4 max → terminate
            ctx.status = InterventionStatus.TERMINATED
            self._schedule_persist(session_id)
            return "TERMINATED"

        return ctx.current_level

    def handle_frontend_signal(
        self,
        session_id: str,
        signal: FrontendSignalEnum,
    ) -> str:
        """Handle frontend signal (END / ESCALATE).

        Args:
            session_id: Session identifier
            signal: FrontendSignalEnum

        Returns:
            "TERMINATED", "ESCALATED", or current level
        """
        ctx = self._contexts.get(session_id)
        if not ctx:
            return ""

        if signal == FrontendSignalEnum.END:
            ctx.status = InterventionStatus.COMPLETED
            self._schedule_persist(session_id)
            return "TERMINATED"

        elif signal == FrontendSignalEnum.ESCALATE:
            # Force escalate to next level
            current = ctx.current_level
            if current.startswith("R"):
                next_r = _next_resource_level(current)
                if next_r == current:
                    # Already at max R level
                    ctx.status = InterventionStatus.TERMINATED
                    self._schedule_persist(session_id)
                    return "TERMINATED"
                ctx.current_level = next_r
                self._schedule_persist(session_id)
                return next_r
            elif current.startswith("M"):
                next_m = _next_metacognitive_level(current)
                if next_m == current:
                    ctx.status = InterventionStatus.TERMINATED
                    self._schedule_persist(session_id)
                    return "TERMINATED"
                ctx.current_level = next_m
                self._schedule_persist(session_id)
                return next_m
            return current

        return ctx.current_level

    def _schedule_persist(self, session_id: str) -> None:
        """Schedule async context persistence without blocking.
        
        Args:
            session_id: Session identifier
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.persist_context(session_id))
        except RuntimeError:
            # No running event loop — skip persistence (will persist on next sync point)
            pass

    # =======================================================================
    # Context Queries
    # =======================================================================

    def get_turn_count(self, session_id: str) -> int:
        """Get current turn number for session.

        Args:
            session_id: Session identifier

        Returns:
            Turn number (1-indexed)
        """
        return self._turn_counters.get(session_id, 0)

    def get_memory_summary(
        self,
        session_id: str,
        max_turns: int = 3,
    ) -> str:
        """Get summary of recent intervention memory.

        Args:
            session_id: Session identifier
            max_turns: Number of recent turns to include

        Returns:
            Formatted summary string
        """
        ctx = self._contexts.get(session_id)
        if not ctx or not ctx.intervention_memory:
            return "无历史干预记录"

        recent = ctx.intervention_memory[-max_turns:]
        summary = f"近{len(recent)}轮干预记录：\n"

        for r in recent:
            student_response_val = r.student_response
            if hasattr(student_response_val, 'value'):
                student_response_val = student_response_val.value
            summary += f"- 第{r.turn}轮 ({r.prompt_level}): 学生反馈={student_response_val}\n"

            # Handle qa_history as dict or object
            qa_history = r.qa_history
            if isinstance(qa_history, dict):
                student_q = qa_history.get("student_q", "")
            else:
                student_q = getattr(qa_history, "student_q", "")

            if student_q:
                q_preview = student_q[:30] + "..." if len(student_q) > 30 else student_q
                summary += f"  学生说: {q_preview}\n"

        if len(ctx.intervention_memory) > max_turns:
            old = ctx.intervention_memory[:-max_turns]
            old_levels = [r.prompt_level for r in old]
            old_responses = []
            for r in old:
                sr = r.student_response
                if hasattr(sr, 'value'):
                    sr = sr.value
                old_responses.append(sr)
            summary += f"\n早期{len(old)}轮：尝试了 {', '.join(set(old_levels))}，"
            if all(r == "not_progressed" for r in old_responses):
                summary += "均未推进。"
            elif any(r == "accepted" for r in old_responses):
                summary += "有推进。"
            else:
                summary += "结果混杂。"

        return summary

    def is_session_active(self, session_id: str) -> bool:
        """Check if session is still active.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists and status is ACTIVE
        """
        ctx = self._contexts.get(session_id)
        return ctx is not None and ctx.is_active()

    def clear_session(self, session_id: str) -> None:
        """Clear session from memory.

        Args:
            session_id: Session identifier
        """
        self._contexts.pop(session_id, None)
        self._turn_counters.pop(session_id, None)


# =============================================================================
# Level Progression Helpers
# =============================================================================

def _next_resource_level(current: str) -> str:
    """Get next Resource level.

    R1 → R2 → R3 → R4 → R4
    """
    level_map = {
        "R1": "R2",
        "R2": "R3",
        "R3": "R4",
        "R4": "R4",  # Max
    }
    return level_map.get(current, "R1")


def _next_metacognitive_level(current: str) -> str:
    """Get next Metacognitive level.

    M1 → M2 → M3 → M4 → M5 → M5
    """
    level_map = {
        "M1": "M2",
        "M2": "M3",
        "M3": "M4",
        "M4": "M5",
        "M5": "M5",  # Max
    }
    return level_map.get(current, "M1")
