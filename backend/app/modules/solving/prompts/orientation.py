"""Orientation phase prompt template.

This prompt guides the LLM through the orientation phase where students
understand the problem space, identify key concepts, and set goals.
"""


class OrientationPrompt:
    """Prompt template for the orientation phase."""

    def __init__(self):
        """Initialize the orientation prompt."""
        raise NotImplementedError

    def get_prompt(self, problem: str, context: dict) -> str:
        """Get the orientation prompt.

        Args:
            problem: The problem statement
            context: Additional context information

        Returns:
            str: The formatted prompt

        Raises:
            NotImplementedError
        """
        raise NotImplementedError