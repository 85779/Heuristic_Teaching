"""Reconstruction phase prompt template.

This prompt guides the LLM through the reconstruction phase where students
break down the problem, identify components, and understand relationships.
"""


class ReconstructionPrompt:
    """Prompt template for the reconstruction phase."""

    def __init__(self):
        """Initialize the reconstruction prompt."""
        raise NotImplementedError

    def get_prompt(self, problem: str, orientation: str, context: dict) -> str:
        """Get the reconstruction prompt.

        Args:
            problem: The problem statement
            orientation: Results from the orientation phase
            context: Additional context information

        Returns:
            str: The formatted prompt

        Raises:
            NotImplementedError
        """
        raise NotImplementedError