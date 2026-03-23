"""Prompt templates for the solving module."""
from .system import SYSTEM_PROMPT
from .thinking_tasks import THINKING_TASKS_PROMPT
from .actions import ACTIONS_PROMPT
from .output_format import OUTPUT_FORMAT_PROMPT
from .language_style import LANGUAGE_STYLE_PROMPT
from .prohibitions import PROHIBITIONS_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
    "THINKING_TASKS_PROMPT",
    "ACTIONS_PROMPT",
    "OUTPUT_FORMAT_PROMPT",
    "LANGUAGE_STYLE_PROMPT",
    "PROHIBITIONS_PROMPT",
]
