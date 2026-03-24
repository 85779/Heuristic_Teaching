"""Hint generator for intervention module."""

import os
import json
import importlib.util
from typing import Optional, TYPE_CHECKING
from .models import GeneratedHint
from .prompts import build_hint_prompt

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient
    from app.modules.intervention.analyzer.models import BreakpointAnalysis

Message = None  # Will be imported lazily to avoid circular dependency


def _get_breakpoint_analysis_class():
    """Lazy import to avoid circular dependency via direct file load."""
    # Use importlib to directly load the module file, bypassing __init__.py
    # which has problematic circular imports
    spec = importlib.util.spec_from_file_location(
        "analyzer_models",
        "app/modules/intervention/analyzer/models.py"
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.BreakpointAnalysis
    raise ImportError("Could not load BreakpointAnalysis")


class HintGenerator:
    """Generates intervention hints based on breakpoint analysis and intensity."""

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

    def _determine_level(self, intensity: float) -> str:
        """Determine hint level based on intensity."""
        if intensity < 0.4:
            return "surface"
        elif intensity < 0.7:
            return "middle"
        else:
            return "deep"

    async def generate(
        self,
        analysis: "BreakpointAnalysis",
        problem: str,
        intensity: float,
    ) -> GeneratedHint:
        """
        Generate a hint based on breakpoint analysis.
        
        1. Determine hint level from intensity (surface/middle/deep)
        2. Build prompt using build_hint_prompt()
        3. Call LLM with the prompt
        4. Parse response into GeneratedHint
        
        The LLM returns a JSON:
        {
          "content": "hint text...",
          "approach_used": "path description..."
        }
        
        Returns:
            GeneratedHint with content, level, approach_used, original_intensity
        """
        # Step 1: Determine hint level
        level = self._determine_level(intensity)
        
        # Step 2: Build prompt
        analysis_dict = {
            "required_knowledge": analysis.required_knowledge,
            "required_connection": analysis.required_connection,
            "possible_approaches": analysis.possible_approaches,
            "difficulty_level": analysis.difficulty_level,
        }
        prompt = build_hint_prompt(
            analysis=analysis_dict,
            problem=problem,
            level=level,
            intensity=intensity,
        )
        
        # Step 3: Call LLM
        llm_client = self._get_llm_client()
        from app.infrastructure.llm.base_client import Message
        
        response = await llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
        )
        
        # Step 4: Parse response
        try:
            parsed = json.loads(response)
            content = parsed.get("content", "")
            approach_used = parsed.get("approach_used", "")
        except json.JSONDecodeError:
            content = response
            approach_used = ""
        
        return GeneratedHint(
            content=content,
            level=level,
            approach_used=approach_used,
            original_intensity=intensity,
        )
