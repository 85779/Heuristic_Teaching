"""Intervention prompt templates for LLM interactions."""

from app.modules.intervention.prompts.location import location_prompt
from app.modules.intervention.prompts.analysis import analysis_prompt
from app.modules.intervention.prompts.decision import decision_prompt
from app.modules.intervention.prompts.intensity import intensity_prompt
from app.modules.intervention.prompts.hint import hint_prompt

__all__ = [
    "location_prompt",
    "analysis_prompt",
    "decision_prompt",
    "intensity_prompt",
    "hint_prompt",
]