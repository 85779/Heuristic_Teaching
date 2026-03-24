"""
Prompt Engine for managing prompt templates and rendering.

The PromptEngine handles:
- Prompt template storage and retrieval
- Variable substitution and rendering
- Template versioning
"""

from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Engine for managing prompt templates.

    Responsibilities:
    - Store and retrieve prompt templates
    - Render templates with variable substitution
    - Manage template versions
    - Validate template variables
    """

    def __init__(self):
        """Initialize the prompt engine."""
        self._templates: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def register_template(self, template_id: str, template: Any) -> None:
        """
        Register a template in the engine.

        Args:
            template_id: Unique template identifier
            template: Template content (string or other)
        """
        self._templates[template_id] = template

    def get_template(self, template_id: str) -> Optional[Any]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template content if found, None otherwise
        """
        return self._templates.get(template_id)

    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Render a template with provided variables.

        Args:
            template_id: Template identifier
            variables: Variable values to substitute

        Returns:
            Rendered template string

        Raises:
            KeyError: If template not found
        """
        template = self.get_template(template_id)
        if template is None:
            raise KeyError(f"Template '{template_id}' not found")
        if isinstance(template, str):
            result = template
            for key, value in variables.items():
                result = result.replace(f"${{{key}}}", str(value))
                result = result.replace(f"{{{{{key}}}}}", str(value))
            return result
        return str(template)

    def list_templates(self) -> List[str]:
        """
        List all registered template IDs.

        Returns:
            Sorted list of template IDs
        """
        return sorted(self._templates.keys())

    def validate_template(self, template_id: str, variables: Dict[str, Any]) -> bool:
        """
        Validate that all required variables are provided for a template.

        Args:
            template_id: Template identifier
            variables: Variables to validate

        Returns:
            True if all required variables present, False if template not found or validation fails
        """
        template = self.get_template(template_id)
        if template is None:
            return False
        if isinstance(template, str):
            vars_needed = set(re.findall(r'\$\{(\w+)\}', template))
            vars_needed.update(set(re.findall(r'\{\{(\w+)\}\}', template)))
            return vars_needed.issubset(set(variables.keys()))
        return True
