"""
LLM Orchestrator for managing LLM interactions and pipeline execution.

The LLMOrchestrator is responsible for:
- Prompt template management
- LLM call orchestration
- Output parsing and validation
- Retry and fallback strategies
"""

from typing import Dict, Any, List, Optional
import logging

from app.core.orchestrator.prompt_engine import PromptEngine
from app.core.orchestrator.output_parser import OutputParser

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Central orchestrator for all LLM interactions in the system.

    Responsibilities:
    - Manage prompt templates and rendering
    - Coordinate LLM calls with proper error handling
    - Parse and validate LLM outputs
    - Implement retry and fallback strategies
    - Support multi-step pipelines
    """

    def __init__(self):
        """Initialize the LLM orchestrator."""
        self._templates: Dict[str, Any] = {}
        self._llm_client = None
        self._prompt_engine = PromptEngine()
        self._output_parser = OutputParser()
        self.logger = logging.getLogger(__name__)

    def set_llm_client(self, client: Any) -> None:
        """
        Set the LLM client to use.

        Args:
            client: LLM client instance
        """
        self._llm_client = client

    def register_template(self, template_id: str, template: Any) -> None:
        """
        Register a prompt template.

        Args:
            template_id: Unique template identifier
            template: Template object
        """
        self._prompt_engine.register_template(template_id, template)

    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Render a prompt template with provided variables.

        Args:
            template_id: Template identifier
            variables: Variables to substitute in template

        Returns:
            Rendered prompt string
        """
        return self._prompt_engine.render_template(template_id, variables)

    def list_templates(self) -> List[str]:
        """
        List all registered templates.

        Returns:
            List of template IDs
        """
        return self._prompt_engine.list_templates()

    async def call_llm(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Call the LLM with a prompt.

        Args:
            prompt: Prompt to send to LLM
            model: Model identifier
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            retry_count: Number of retries on failure

        Returns:
            LLM response dictionary
        """
        if self._llm_client is None:
            raise RuntimeError("LLM client not set. Call set_llm_client() first.")
        last_error = None
        for attempt in range(retry_count):
            try:
                response = await self._llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return {
                    "content": response,
                    "model": model,
                    "usage": {}
                }
            except Exception as e:
                last_error = e
                self.logger.warning(f"LLM call attempt {attempt+1} failed: {e}")
        raise RuntimeError(f"LLM call failed after {retry_count} attempts: {last_error}")

    async def run_pipeline(
        self,
        pipeline_id: str,
        context: Dict[str, Any],
        steps: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a multi-step pipeline.

        Args:
            pipeline_id: Pipeline identifier
            context: Shared context across pipeline steps
            steps: List of step names to execute

        Returns:
            Pipeline result with outputs from each step
        """
        results = []
        current_context = dict(context)
        for step in steps:
            template_id = step
            rendered = self.render_template(template_id, current_context)
            llm_result = await self.call_llm(rendered)
            results.append(llm_result)
            current_context[f"{step}_result"] = llm_result
        return {"context": current_context, "results": results}

    def parse_output(self, raw_output: str, schema: Any) -> Any:
        """
        Parse and validate LLM output against a schema.

        Args:
            raw_output: Raw LLM output string
            schema: Schema to validate against

        Returns:
            Parsed and validated output
        """
        import json
        try:
            data = self._output_parser.parse_json(raw_output)
            if schema:
                self._output_parser.validate_schema(data, schema)
            return data
        except ValueError:
            return self._output_parser.parse_markdown(raw_output, schema)