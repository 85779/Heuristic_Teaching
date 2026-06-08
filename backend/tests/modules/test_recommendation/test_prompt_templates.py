"""Tests for ProblemPromptTemplates."""

import pytest
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates
from app.modules.recommendation.models import (
    KnowledgeAnchor, AnchorType, KnowledgePoint, Method
)


class TestProblemPromptTemplates:
    """Test suite for ProblemPromptTemplates."""

    def test_build_prompt_includes_kps(self, prompt_templates):
        """Generated prompt includes knowledge point content."""
        kp = KnowledgePoint(
            kp_id="KP_3_01",
            name="极限计算",
            chapter="第3章",
            chapter_name="极限与连续",
            type="计算",
            content="极限的定义和基本计算",
            formula="$\\lim_{x \\to a} f(x)$",
            related_types=["函数极限"],
            prerequisites=["KP_2_01"],
            methods=["等价无穷小替换"],
        )
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=[kp],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="巩固练习",
        )
        prompt = prompt_templates.build_generation_prompt(anchor, target_difficulty=3)
        assert "极限计算" in prompt
        assert "3" in prompt  # difficulty level

    def test_build_prompt_includes_method(self, prompt_templates):
        """Generated prompt includes method context."""
        method = Method(
            name="配方法",
            description="通过配方将表达式化为完全平方形式",
            applicable_kps=["KP_2_01"],
        )
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.VARIATION,
            target_kps=[],
            target_method=method,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="变式练习",
        )
        prompt = prompt_templates.build_generation_prompt(anchor, target_difficulty=2)
        assert "配方法" in prompt

    def test_build_prompt_excludes_similar(self, prompt_templates):
        """Generated prompt includes exclusion context."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=[],
            target_method=None,
            exclude_methods=[],
            exclude_similar=["类似的求极限题目"],
            generation_goal="综合练习",
        )
        prompt = prompt_templates.build_generation_prompt(anchor, target_difficulty=3)
        assert "排除" in prompt or "出现" in prompt

    def test_format_kps_handles_empty(self, prompt_templates):
        """_format_kps handles empty KP list."""
        result = prompt_templates._format_kps([])
        assert "未指定" in result

    def test_format_kps_limits_to_3(self, prompt_templates):
        """_format_kps only includes first 3 KPs."""
        kps = [
            KnowledgePoint(
                kp_id=f"KP_{i}",
                name=f"KP{i}",
                chapter="C",
                chapter_name="Chapter",
                type="T",
                content="Content",
            )
            for i in range(5)
        ]
        result = prompt_templates._format_kps(kps)
        # Should contain first 3
        assert "KP0" in result
        assert "KP1" in result
        assert "KP2" in result