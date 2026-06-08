"""Problem validator for quality control of generated problems."""

import json
import re
from typing import Optional, List
from app.modules.recommendation.models import ValidationResult, GeneratedProblem


class ProblemValidator:
    """Validator for generated math problems.
    
    Checks quality and safety of LLM-generated problems before
    returning them to the student.
    """

    FORBIDDEN_PHRASES = [
        "显然",
        "易知",
        "不难发现",
        "显然可知",
        "易得",
        "显然成立",
        "易见",
        "trivial",
        "obviously",
    ]

    def validate(self, raw_output: str, expected_fields: Optional[List[str]] = None) -> ValidationResult:
        """Validate a raw LLM output string.
        
        Args:
            raw_output: Raw string output from LLM.
            expected_fields: List of required JSON fields.
            
        Returns:
            ValidationResult with passed status and error list.
        """
        if expected_fields is None:
            expected_fields = [
                "problem_text", "answer", "solution_hint",
                "difficulty_rating", "related_kps", "method_used",
                "why_recommended", "generation_reasoning",
            ]

        errors = []

        # 1. Try to extract JSON
        json_str = self._extract_json(raw_output)
        if not json_str:
            errors.append("无法从输出中提取有效的JSON")
            return ValidationResult(passed=False, errors=errors)

        # 2. Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            errors.append(f"JSON解析失败: {str(e)}")
            return ValidationResult(passed=False, errors=errors)

        # 3. Check required fields
        missing = [f for f in expected_fields if f not in data]
        if missing:
            errors.append(f"缺少必填字段: {', '.join(missing)}")

        # 4. Check problem text quality
        problem_text = data.get("problem_text", "")
        if len(problem_text) < 10:
            errors.append("题目文本过短，内容不完整")
        if any(phrase in problem_text for phrase in self.FORBIDDEN_PHRASES):
            errors.append("题目包含过于简略的表述（如'显然'、'易知'）")

        # 5. Check LaTeX formatting
        if "$" not in problem_text and "\\(" not in problem_text:
            # LaTeX is recommended but not strictly required for all problems
            pass

        # 6. Check answer
        answer = data.get("answer", "")
        if not answer or len(answer.strip()) == 0:
            errors.append("答案为空")

        # 7. Check difficulty rating
        diff = data.get("difficulty_rating")
        if diff is not None:
            if not isinstance(diff, int) or diff < 1 or diff > 5:
                errors.append(f"难度值无效: {diff}，应为1-5的整数")

        # 8. Check related_kps
        related_kps = data.get("related_kps", [])
        if not isinstance(related_kps, list):
            errors.append("related_kps 应为列表")
        elif len(related_kps) == 0:
            errors.append("related_kps 不能为空")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
        )

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from LLM output (handles markdown code blocks).
        
        Args:
            text: Raw LLM output text.
            
        Returns:
            Extracted JSON string or None.
        """
        text = text.strip()
        
        # Try direct parse first
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        patterns = [
            r"```(?:json)?\s*(\{.*?\})\s*```",
            r"```(\{.*?\})```",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue

        # Try to find first { to last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = text[first_brace:last_brace + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        return None