"""
Output Parser for parsing and validating LLM outputs.

The OutputParser handles:
- Structured output parsing (JSON, YAML, etc.)
- Output validation against schemas
- Error handling and fallback strategies
"""

from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class OutputParser:
    """
    Parser for structured LLM outputs.

    Responsibilities:
    - Parse raw LLM output into structured data
    - Validate output against schemas
    - Handle parsing errors gracefully
    - Support multiple output formats
    """

    def __init__(self):
        """Initialize the output parser."""
        self.logger = logging.getLogger(__name__)

    def parse_json(self, output: str) -> Dict[str, Any]:
        """
        Parse raw output as JSON.

        Args:
            output: Raw string output from LLM

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON parsing fails
        """
        import json
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def parse_yaml(self, output: str) -> Dict[str, Any]:
        """
        Parse raw output as YAML.

        Args:
            output: Raw string output from LLM

        Returns:
            Parsed YAML as dictionary

        Raises:
            ValueError: If YAML parsing fails
        """
        import yaml
        return yaml.safe_load(output) or {}

    def parse_markdown(self, output: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse raw output as Markdown with structured sections.

        Args:
            output: Raw string output from LLM
            schema: Optional schema for validation

        Returns:
            Parsed structured content
        """
        import re
        result: Dict[str, Any] = {"raw": output}
        code_blocks = self.extract_json_blocks(output)
        if code_blocks:
            result["code_blocks"] = code_blocks
        return result

    def validate_schema(self, data: Any, schema: Dict) -> bool:
        """
        Validate data against a schema.

        Args:
            data: Data to validate
            schema: Schema definition

        Returns:
            True if validation passes
        """
        if not isinstance(data, dict):
            return False
        required = schema.get("required", [])
        return all(k in data for k in required)

    def extract_json_blocks(self, output: str) -> List[str]:
        """
        Extract JSON blocks from markdown code fences.

        Args:
            output: Raw string output

        Returns:
            List of extracted JSON strings
        """
        import re
        pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(pattern, output, re.DOTALL)
        return [m.strip() for m in matches]

    def extract_sections(self, output: str, section_names: List[str]) -> Dict[str, str]:
        """
        Extract named sections from raw output.

        Args:
            output: Raw string output
            section_names: List of section names to extract

        Returns:
            Dictionary mapping section names to their content
        """
        import re
        result = {}
        for name in section_names:
            pattern = rf'##?\s*{re.escape(name)}\s*\n(.*?)(?=##?\s|\Z)'
            match = re.search(pattern, output, re.DOTALL)
            if match:
                result[name] = match.group(1).strip()
        return result

    def parse_with_fallback(
        self,
        output: str,
        parsers: List[str],
        schema: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Try multiple parsers in order until one succeeds.

        Args:
            output: Raw string output
            parsers: List of parser names to try (json, yaml, markdown)
            schema: Optional schema for validation

        Returns:
            Parsed output from first successful parser
        """
        for parser_name in parsers:
            try:
                result = self.parse(output, parser_name, schema)
                if schema is None or self.validate_schema(result, schema):
                    return result
            except ValueError:
                continue
        raise ValueError("All parsers failed")

    def clean_output(self, output: str) -> str:
        """
        Clean raw output by removing common artifacts.

        Args:
            output: Raw string output

        Returns:
            Cleaned output string
        """
        import re
        output = re.sub(r'```[\w]*\n.*?\n```', '', output, flags=re.DOTALL)
        output = re.sub(r'#{1,6}\s+', '', output)
        return output.strip()

    def parse(self, output: str, format: str, schema: Optional[Dict] = None) -> Any:
        """
        Parse output using the specified format.

        Args:
            output: Raw string output
            format: Format to parse (json, yaml, markdown)
            schema: Optional schema for validation

        Returns:
            Parsed output

        Raises:
            ValueError: If format is unknown or parsing fails
        """
        if format == "json":
            return self.parse_json(output)
        elif format == "yaml":
            return self.parse_yaml(output)
        elif format == "markdown":
            return self.parse_markdown(output, schema)
        else:
            raise ValueError(f"Unknown format: {format}")