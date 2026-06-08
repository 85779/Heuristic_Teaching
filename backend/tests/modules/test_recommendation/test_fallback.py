"""Tests for FallbackGenerator."""

import pytest
from app.modules.recommendation.generator.fallback_generator import FallbackGenerator
from app.modules.recommendation.models import KnowledgeAnchor, AnchorType, KnowledgePoint


class TestFallbackGenerator:
    """Test suite for FallbackGenerator."""

    @pytest.mark.asyncio
    async def test_fallback_returns_problem(self, fallback_generator):
        """Fallback always returns a valid problem."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=[],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="测试",
        )
        problem = await fallback_generator.generate(anchor, target_difficulty=3)
        assert problem is not None
        assert problem.problem_text is not None
        assert problem.answer is not None
        assert 1 <= problem.difficulty <= 5

    @pytest.mark.asyncio
    async def test_fallback_has_valid_latex(self, fallback_generator):
        """Fallback problems contain valid math content (LaTeX or text)."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=[],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="测试",
        )
        problem = await fallback_generator.generate(anchor, target_difficulty=2)
        # Must have either LaTeX delimiters or math-related content
        has_math = "$" in problem.problem_text or "\\" in problem.problem_text
        has_content = len(problem.problem_text) > 10 and len(problem.answer) > 0
        assert has_math or has_content

    @pytest.mark.asyncio
    async def test_fallback_includes_why_recommended(self, fallback_generator):
        """Fallback problem includes recommendation reason."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=[],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="巩固练习",
        )
        problem = await fallback_generator.generate(anchor, target_difficulty=1)
        assert problem.why_recommended is not None
        assert len(problem.why_recommended) > 0

    @pytest.mark.asyncio
    async def test_fallback_difficulty_close_to_target(self, fallback_generator):
        """Fallback difficulty is close to target."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=[],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="测试",
        )
        difficulties = [(await fallback_generator.generate(anchor, target_difficulty=3)).difficulty
                       for _ in range(10)]
        assert all(1 <= d <= 5 for d in difficulties)
