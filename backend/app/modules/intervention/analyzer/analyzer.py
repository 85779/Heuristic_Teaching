import os
import json
from typing import List, Optional, TYPE_CHECKING
from ..locator.models import BreakpointLocation
from .models import BreakpointAnalysis
from .prompts import build_analysis_prompt
from app.infrastructure.llm.base_client import Message

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient


class BreakpointAnalyzer:
    """Analyzes what is needed to cross a breakpoint using LLM."""

    def __init__(self, llm_client: Optional["DashScopeClient"] = None):
        self._llm_client = llm_client

    def _get_llm_client(self) -> "DashScopeClient":
        if self._llm_client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY not set")
            from app.infrastructure.llm.dashscope_client import DashScopeClient
            self._llm_client = DashScopeClient(api_key=api_key, model="qwen-turbo")
        return self._llm_client

    async def analyze(
        self,
        breakpoint_location: BreakpointLocation,
        problem: str,
        student_work: str,
        solution_steps: List[str],
    ) -> BreakpointAnalysis:
        """
        Analyze what is needed to cross the breakpoint.
        
        1. Build prompt using build_analysis_prompt()
        2. Call LLM with the prompt
        3. Parse LLM JSON output into BreakpointAnalysis
        
        Returns:
            BreakpointAnalysis with required_knowledge, required_connection, 
            possible_approaches, difficulty_level
        """
        # Build prompt
        prompt = build_analysis_prompt(
            problem=problem,
            student_work=student_work,
            solution_steps=solution_steps,
            breakpoint_location=breakpoint_location.gap_description,
            expected_step=breakpoint_location.expected_step_content,
        )

        # Call LLM
        llm_client = self._get_llm_client()
        response = await llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
        )

        # Parse JSON response
        try:
            analysis_data = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, return a default analysis
            return BreakpointAnalysis(
                required_knowledge=[],
                required_connection="解析失败",
                possible_approaches=[],
                difficulty_level=0.5,
            )

        # Map to BreakpointAnalysis
        return BreakpointAnalysis(
            required_knowledge=analysis_data.get("required_knowledge", []),
            required_connection=analysis_data.get("required_connection", ""),
            possible_approaches=analysis_data.get("possible_approaches", []),
            difficulty_level=float(analysis_data.get("difficulty_level", 0.5)),
        )
