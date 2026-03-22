"""Verification phase prompt template.

This prompt guides the LLM through the verification phase where students
validate their solution, check for errors, and ensure correctness.
"""


class VerificationPrompt:
    """Prompt template for the verification phase."""

    def __init__(self):
        """Initialize the verification prompt."""
        raise NotImplementedError

    def get_prompt(
        self, problem: str, orientation: str, reconstruction: str, transformation: str, context: dict
    ) -> str:
        """Get the verification prompt.

        Args:
            problem: The problem statement
            orientation: Results from the orientation phase
            reconstruction: Results from the reconstruction phase
            transformation: Results from the transformation phase
            context: Additional context information

        Returns:
            str: The formatted prompt

        Raises:
            NotImplementedError
        """
        raise NotImplementedError