"""Prompt Builder - Chain-style prompt construction."""

from typing import Optional, Dict, Any, List


class PromptBuilder:
    """Chain-style prompt builder for dynamic prompt construction.
    
    Provides fluent interface for building prompts with optional components.
    """

    def __init__(self):
        """Initialize the prompt builder."""
        self._parts: List[str] = []
        self._system: Optional[str] = None
        self._context: Dict[str, Any] = {}

    def with_system(self, system_prompt: str) -> "PromptBuilder":
        """Add system prompt."""
        self._system = system_prompt
        return self

    def with_context(self, key: str, value: Any) -> "PromptBuilder":
        """Add context variable."""
        self._context[key] = value
        return self

    def with_thinking_tasks(self) -> "PromptBuilder":
        """Add thinking tasks section."""
        from .templates import THINKING_TASKS_PROMPT
        self._parts.append(THINKING_TASKS_PROMPT)
        return self

    def with_actions(self) -> "PromptBuilder":
        """Add actions section."""
        from .templates import ACTIONS_PROMPT
        self._parts.append(ACTIONS_PROMPT)
        return self

    def with_output_format(self) -> "PromptBuilder":
        """Add output format section."""
        from .templates import OUTPUT_FORMAT_PROMPT
        self._parts.append(OUTPUT_FORMAT_PROMPT)
        return self

    def with_prohibitions(self) -> "PromptBuilder":
        """Add prohibitions section."""
        from .templates import PROHIBITIONS_PROMPT
        self._parts.append(PROHIBITIONS_PROMPT)
        return self

    def with_custom(self, text: str) -> "PromptBuilder":
        """Add custom text."""
        self._parts.append(text)
        return self

    def build(self) -> str:
        """Build the final prompt."""
        parts = []
        if self._system:
            parts.append(self._system)
        parts.extend(self._parts)
        return "\n\n".join(parts)

    def reset(self) -> "PromptBuilder":
        """Reset the builder."""
        self._parts = []
        self._system = None
        self._context = {}
        return self
