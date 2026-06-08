"""Tests for ProblemValidator."""

import pytest
from app.modules.recommendation.generator.problem_validator import ProblemValidator


class TestProblemValidator:
    """Test suite for ProblemValidator."""

    def test_valid_json_passes(self, problem_validator):
        """Valid JSON with all required fields passes."""
        raw = '{"problem_text": "求 $\\\\lim_{x \\\\to 0} \\\\frac{\\\\sin x}{x}$", "answer": "1", "solution_hint": "使用重要极限", "difficulty_rating": 2, "related_kps": ["KP_3_01"], "method_used": "等价替换", "why_recommended": "巩固练习", "generation_reasoning": "基于知识点"}'
        result = problem_validator.validate(raw)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_missing_fields_fails(self, problem_validator):
        """Missing required fields fails validation."""
        raw = '{"problem_text": "题目"}'  # missing answer, difficulty, etc.
        result = problem_validator.validate(raw)
        assert result.passed is False
        assert len(result.errors) > 0

    def test_invalid_difficulty_fails(self, problem_validator):
        """Invalid difficulty rating fails."""
        raw = '{"problem_text": "题目内容", "answer": "答案", "solution_hint": "提示", "difficulty_rating": 10, "related_kps": ["KP_1"], "method_used": "方法", "why_recommended": "理由", "generation_reasoning": "推理"}'
        result = problem_validator.validate(raw)
        assert result.passed is False
        assert any("难度" in e for e in result.errors)

    def test_empty_problem_text_fails(self, problem_validator):
        """Empty problem text fails."""
        raw = '{"problem_text": "", "answer": "A", "solution_hint": "H", "difficulty_rating": 2, "related_kps": ["KP_1"], "method_used": "M", "why_recommended": "R", "generation_reasoning": "G"}'
        result = problem_validator.validate(raw)
        assert result.passed is False

    def test_forbidden_phrase_fails(self, problem_validator):
        """Text with '显然' fails."""
        raw = '{"problem_text": "显然，答案为1", "answer": "1", "solution_hint": "提示", "difficulty_rating": 2, "related_kps": ["KP_1"], "method_used": "M", "why_recommended": "R", "generation_reasoning": "G"}'
        result = problem_validator.validate(raw)
        assert result.passed is False

    def test_extract_json_from_markdown(self, problem_validator):
        """JSON inside markdown code block is extracted."""
        raw = """下面是题目：
```json
{"problem_text": "test", "answer": "A", "solution_hint": "H", "difficulty_rating": 1, "related_kps": ["KP_1"], "method_used": "M", "why_recommended": "R", "generation_reasoning": "G"}
```
以上是JSON"""
        json_str = problem_validator._extract_json(raw)
        assert json_str is not None
        import json
        data = json.loads(json_str)
        assert data["problem_text"] == "test"

    def test_invalid_json_returns_error(self, problem_validator):
        """Invalid JSON string fails validation."""
        raw = "这不是有效的JSON"
        result = problem_validator.validate(raw)
        assert result.passed is False
        assert any("JSON" in e for e in result.errors)