"""Solving service for problem-solving business logic."""

import os
from typing import TYPE_CHECKING, Optional
from app.modules.solving.models import (
    SolvingRequest,
    SolvingResponse,
    EvaluationResult,
    ReferenceSolution,
    DetailLevel,
)
from app.modules.solving.evaluator import Evaluator
from app.modules.solving.parser import SolutionParser
from app.modules.solving.prompts.director import PromptDirector
from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

if TYPE_CHECKING:
    from app.core.context import ModuleContext


class ReferenceSolutionService:
    """Service for generating reference solutions.
    
    Main entry point for Module 1: generates organized reference solutions
    from problem statements with optional student work for continuation.
    """

    def __init__(self, context: Optional["ModuleContext"] = None):
        """Initialize the solving service.
        
        Args:
            context: Module execution context (optional)
        """
        self._context = context
        self._evaluator = Evaluator()
        self._parser = SolutionParser()
        self._director = PromptDirector()
        self._llm_client: Optional[DashScopeClient] = None

    def _get_llm_client(self) -> DashScopeClient:
        """Get or create LLM client.
        
        Returns:
            DashScopeClient instance
        """
        if self._llm_client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            model = os.getenv("SOLVING_MODEL", "qwen-turbo")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY environment variable not set")
            self._llm_client = DashScopeClient(api_key=api_key, model=model)
        return self._llm_client

    async def generate(
        self,
        request: SolvingRequest,
        session_id: Optional[str] = None,
    ) -> SolvingResponse:
        """Generate reference solution for the given problem.
        
        Args:
            request: SolvingRequest with problem and optional student work
            
        Returns:
            SolvingResponse with evaluation result and solution (if correct)
        """
        try:
            # Step 1: Evaluate student work
            evaluation = await self._evaluator.evaluate_student_work(
                problem=request.problem,
                student_work=request.student_work or "",
                detail_level=DetailLevel.SIMPLE,
            )

            # Step 2: If incorrect, return error feedback
            if not evaluation.is_correct:
                error_feedback = self._evaluator.create_error_feedback(evaluation)
                return SolvingResponse(
                    success=False,
                    evaluation=evaluation,
                    solution=None,
                    error_feedback=error_feedback,
                )

            # Step 3: Build appropriate prompt
            if request.student_work:
                prompt = self._director.build_continuation_prompt(
                    problem=request.problem,
                    student_work=request.student_work,
                )
            else:
                prompt = self._director.build_full_solution_prompt(
                    problem=request.problem,
                )

            # Step 4: Call LLM (text mode - natural language output)
            llm_client = self._get_llm_client()
            enable_thinking = request.enable_thinking if hasattr(request, 'enable_thinking') else False
            response = await llm_client.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=request.temperature,
                max_tokens=request.max_tokens if hasattr(request, 'max_tokens') and request.max_tokens else 8192,
                enable_thinking=enable_thinking,
            )

            # Step 5: Parse natural language output into structured solution
            solution = self._parser.parse(response, request.problem)

            # Store to SessionState if session_id provided
            if session_id and solution and self._context is not None:
                state = {
                    "problem": request.problem,
                    "student_work": request.student_work or "",
                    "student_steps": getattr(request, 'student_steps', []) or [],
                    "solution_steps": [s.dict() for s in solution.steps],
                }
                self._context.state_manager.set_module_state(session_id, "solving", state)

            return SolvingResponse(
                success=True,
                evaluation=evaluation,
                solution=solution,
                error_feedback=None,
            )

        except Exception as e:
            # Return error response
            return SolvingResponse(
                success=False,
                evaluation=EvaluationResult(
                    is_correct=False,
                    confidence=0.0,
                    issues=[],
                    can_continue=False,
                ),
                solution=None,
                error_feedback=None,
            )

    async def close(self) -> None:
        """Close resources."""
        if self._llm_client:
            await self._llm_client.close()


# Keep legacy class for backward compatibility
class SolvingService(ReferenceSolutionService):
    """Legacy service class - now just an alias for ReferenceSolutionService."""
    pass