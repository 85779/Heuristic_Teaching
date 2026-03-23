"""Evaluator - Evaluates student work correctness."""

import re
from typing import Optional, Tuple
from .models import (
    EvaluationResult,
    Issue,
    ErrorFeedback,
    DetailLevel,
)


class Evaluator:
    """Evaluator for assessing student solution correctness.
    
    Evaluates whether the student's work is correct and whether
    the solution can continue from the current point.
    """

    def __init__(self, llm_client=None):
        """Initialize the evaluator.
        
        Args:
            llm_client: Optional LLM client for AI-based evaluation.
                       If None, uses rule-based evaluation.
        """
        self._llm_client = llm_client

    async def evaluate_student_work(
        self,
        problem: str,
        student_work: str,
        detail_level: DetailLevel = DetailLevel.SIMPLE,
    ) -> EvaluationResult:
        """Evaluate whether student's work is correct.
        
        Args:
            problem: The problem statement (LaTeX)
            student_work: Student's work so far (LaTeX)
            detail_level: Level of detail for error feedback
            
        Returns:
            EvaluationResult with is_correct, confidence, issues, etc.
        """
        if not student_work or not student_work.strip():
            # No student work = nothing to evaluate = correct (can start from scratch)
            return EvaluationResult(
                is_correct=True,
                confidence=1.0,
                issues=[],
                can_continue=True,
                breakpoint_step=None,
            )
        
        if self._llm_client:
            return await self._evaluate_with_llm(problem, student_work, detail_level)
        
        return self._evaluate_with_rules(problem, student_work)

    def _evaluate_with_rules(
        self,
        problem: str,
        student_work: str,
    ) -> EvaluationResult:
        """Simple rule-based evaluation.
        
        For production, use LLM-based evaluation for better accuracy.
        This is a fallback when no LLM client is available.
        
        Args:
            problem: The problem statement
            student_work: Student's work
            
        Returns:
            EvaluationResult (always correct with low confidence as fallback)
        """
        # Simple heuristic: check for basic LaTeX structure
        has_math = bool(re.search(r"\$|\\frac|\\sum|\\int", student_work))
        has_logical_flow = student_work.count("\n") >= 2
        
        if has_math and has_logical_flow:
            return EvaluationResult(
                is_correct=True,
                confidence=0.5,  # Low confidence without LLM
                issues=[],
                can_continue=True,
                breakpoint_step=None,
            )
        
        # Cannot determine, assume correct but low confidence
        return EvaluationResult(
            is_correct=True,
            confidence=0.3,
            issues=[],
            can_continue=True,
            breakpoint_step=None,
        )

    async def _evaluate_with_llm(
        self,
        problem: str,
        student_work: str,
        detail_level: DetailLevel,
    ) -> EvaluationResult:
        """Evaluate using LLM for better accuracy.
        
        Args:
            problem: The problem statement
            student_work: Student's work
            detail_level: Level of detail
            
        Returns:
            EvaluationResult from LLM assessment
        """
        # This would use the LLM client to evaluate
        # For now, fall back to rule-based
        return self._evaluate_with_rules(problem, student_work)

    def create_error_feedback(
        self,
        evaluation: EvaluationResult,
        detail_level: DetailLevel = DetailLevel.SIMPLE,
    ) -> ErrorFeedback:
        """Create error feedback from evaluation result.
        
        Args:
            evaluation: The evaluation result
            detail_level: Level of detail for feedback
            
        Returns:
            ErrorFeedback with summary and suggestions
        """
        if evaluation.is_correct:
            return ErrorFeedback(
                summary="解答正确",
                issues=[],
                suggestion="",
            )
        
        summary_parts = []
        suggestions = []
        
        for issue in evaluation.issues:
            summary_parts.append(f"第{issue.step}步: {issue.description}" if issue.step else issue.description)
            if issue.severity == "error":
                suggestions.append(f"检查{issue.location}")
        
        summary = "; ".join(summary_parts) if summary_parts else "发现解题错误"
        suggestion = "; ".join(suggestions) if suggestions else "请重新审视解题思路"
        
        return ErrorFeedback(
            summary=summary,
            issues=evaluation.issues,
            suggestion=suggestion,
        )

    def determine_breakpoint(self, student_work: str) -> Optional[int]:
        """Determine the step where student stopped.
        
        Args:
            student_work: Student's work text
            
        Returns:
            Step number where student stopped, or None if cannot determine
        """
        # Look for step patterns like "第1步", "步骤1", etc.
        step_patterns = [
            r"第([一二三四五12345])\s*步",
            r"步骤\s*([1-5])",
            r"step\s*([1-5])",
        ]
        
        last_step = 0
        for pattern in step_patterns:
            matches = re.findall(pattern, student_work, re.IGNORECASE)
            for match in matches:
                try:
                    if match in "一二三四五":
                        step_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
                        step = step_map.get(match, 0)
                    else:
                        step = int(match)
                    last_step = max(last_step, step)
                except (ValueError, KeyError):
                    pass
        
        return last_step if last_step > 0 else None
