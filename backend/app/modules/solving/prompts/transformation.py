"""Transformation phase prompt template.

This prompt guides the LLM through the transformation phase where students
apply solution strategies and develop approaches to solve the problem.
"""


class TransformationPrompt:
    """Prompt template for the transformation phase."""

    def __init__(self):
        """Initialize the transformation prompt."""
        raise NotImplementedError

    def get_prompt(
        self, problem: str, orientation: str, reconstruction: str, context: dict
    ) -> str:
        """Get the transformation prompt.

        Args:
            problem: The problem statement
            orientation: Results from the orientation phase
            reconstruction: Results from the reconstruction phase
            context: Additional context information

        Returns:
            str: The formatted prompt

        Raises:
            NotImplementedError
        """
        raise NotImplementedError