"""Solution Parser - Parses LLM natural language output into structured ReferenceSolution."""

import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .models import (
    ReferenceSolution,
    TeachingStep,
)


class SolutionParser:
    """Parser for converting LLM natural language output into structured ReferenceSolution.

    Handles the new three-part format:
    - "这题怎么看" (opening)
    - "这题怎么想" with numbered steps (body)
    - "这题留下什么方法" (conclusion)
    """

    def __init__(self):
        """Initialize the solution parser."""
        pass

    def parse(self, llm_output: str, problem: str) -> ReferenceSolution:
        """Parse LLM natural language output into ReferenceSolution.

        Args:
            llm_output: Raw LLM output text (three-part format)
            problem: Original problem statement

        Returns:
            ReferenceSolution: Parsed structured solution
        """
        sections = self._split_sections(llm_output)
        steps = self._parse_steps(sections)
        answer = self._extract_answer(sections)

        return ReferenceSolution(
            problem=problem,
            answer=answer,
            generated_at=datetime.now(timezone.utc),
            steps=steps,
        )

    def parse_json(self, json_output: str, problem: str) -> ReferenceSolution:
        """Parse JSON output from LLM into ReferenceSolution.

        Args:
            json_output: JSON string from LLM
            problem: Original problem statement

        Returns:
            ReferenceSolution: Parsed structured solution
        """
        return self.parse(json_output, problem)

    def _split_sections(self, text: str) -> Dict[str, str]:
        """Split text into three sections based on the new format.

        Args:
            text: Raw LLM output

        Returns:
            Dict with keys: opening, body (steps), conclusion
        """
        sections: Dict[str, str] = {}

        # 1. Opening: "这题怎么看"
        opening_pattern = r"这题怎么看[:：]?\s*(.*?)(?=\n这题怎么想|这题留下什么|\n第[一二三四五1-5]步|\Z)"
        match = re.search(opening_pattern, text, re.DOTALL)
        if match:
            sections["opening"] = match.group(1).strip()

        # 2. Body: "这题怎么想" through "这题留下什么方法"
        body_pattern = r"这题怎么想[:：]?\s*(.*?)(?=\n这题留下什么|这题留下什么方法|\Z)"
        match = re.search(body_pattern, text, re.DOTALL)
        if match:
            sections["body"] = match.group(1).strip()

        # 3. Conclusion: "这题留下什么方法"
        conclusion_pattern = r"这题留下什么方法[:：]?\s*(.*)"
        match = re.search(conclusion_pattern, text, re.DOTALL)
        if match:
            sections["conclusion"] = match.group(1).strip()

        return sections

    def _parse_steps(self, sections: Dict[str, str]) -> List[TeachingStep]:
        """Parse solution steps from the body section.

        Looks for numbered steps in various formats:
        - "第一步", "第二步"...
        - "第1步", "第2步"...
        - "1.", "2." at line start

        Args:
            sections: Dict with body section content

        Returns:
            List of TeachingStep objects
        """
        body = sections.get("body", sections.get("opening", ""))

        steps: List[TeachingStep] = []

        # Multi-pattern matching for various step formats
        step_patterns = [
            # "第一步：" etc - handles last step without trailing newline
            r"(?:^|\n)(第[一二三四五1-5]步)[:：]\s*(.*?)(?=\n(?:第[一二三四五1-5]步|这题|$)|$)",
            # "1. " or "1、 " at line start
            r"(?:^|\n)(\d+[.、])\s*(.*?)(?=\n(?:\d+[.、]|这题|$)|$)",
        ]

        for pattern in step_patterns:
            matches = re.findall(pattern, body, re.DOTALL)
            if matches:
                for step_marker, step_content in matches:
                    step_name = step_marker.strip().rstrip(":.、")
                    content = step_content.strip()

                    # Clean up content - remove leading bullet points
                    content = re.sub(r"^[-*]\s*", "", content)
                    # Truncate very long content to reasonable length
                    if len(content) > 500:
                        # Try to end at a sentence boundary
                        cut = content[:500].rfind("。")
                        if cut > 100:
                            content = content[:cut + 1]
                        else:
                            content = content[:500]

                    steps.append(TeachingStep(
                        step_id=f"s{len(steps) + 1}",
                        step_name=step_name,
                        content=content,
                    ))
                break

        # If no numbered steps found, use paragraphs as steps
        if not steps:
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and len(p.strip()) > 10]
            for i, para in enumerate(paragraphs[:5], 1):
                steps.append(TeachingStep(
                    step_id=f"s{i}",
                    step_name=f"步骤{i}",
                    content=para[:500],
                ))

        return steps

    def _extract_answer(self, sections: Dict[str, str]) -> Optional[str]:
        """Extract answer/takeaway from the conclusion section.

        Args:
            sections: Dict with conclusion section

        Returns:
            Extracted answer text or None
        """
        conclusion = sections.get("conclusion", "")

        if not conclusion:
            # Fallback: try opening section
            conclusion = sections.get("opening", "")

        if not conclusion:
            return None

        # Clean up and truncate
        answer = conclusion.strip()
        if len(answer) > 500:
            # Try to end at a sentence boundary
            answer = answer[:500].rsplit("。", 1)[0] + "。"

        return answer if answer else None
