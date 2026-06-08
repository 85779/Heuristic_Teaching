"""Tests for ProblemGenerator with mocked LLM."""

import pytest
from unittest.mock import AsyncMock
from app.modules.recommendation.generator.problem_generator import ProblemGenerator
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates
from app.modules.recommendation.generator.problem_validator import ProblemValidator
from app.modules.recommendation.models import KnowledgeAnchor, AnchorType, KnowledgePoint


class TestProblemGenerator:
    """Test suite for ProblemGenerator."""

    @pytest.mark.asyncio
    async def test_generate_with_mock_llm(self, problem_generator, llm_client):
        """Generator returns valid problem with mocked LLM."""
        kp = KnowledgePoint(
            kp_id="KP_3_01",
            name="极限计算",
            chapter="3",
            chapter_name="极限",
            type="计算",
            content="极限定义",
            related_types=["函数极限"],
            prerequisites=[],
            methods=["等价替换"],
        )
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=[kp],
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="练习",
        )
        result = await problem_generator.generate(anchor, target_difficulty=2, max_retries=0)
        assert result.success is True
        assert result.problem is not None
        assert result.problem.problem_text is not None
        assert result.problem.answer is not None
        assert 1 <= result.problem.difficulty <= 5

    @pytest.mark.asyncio
    async def test_generate_empty_anchor_fails(self, problem_generator):
        """Generator fails gracefully with empty anchor."""
        anchor = KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=[],  # Empty
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="",
        )
        result = await problem_generator.generate(anchor, target_difficulty=1)
        assert result.success is False
        assert result.error is not None

    def test_generator_has_retry_logic(self, prompt_templates, problem_validator):
        """Generator's generate method accepts max_retries parameter."""
        from app.modules.recommendation.generator.problem_generator import ProblemGenerator
        from unittest.mock import MagicMock
        import inspect
        
        mock_llm = MagicMock()
        gen = ProblemGenerator(
            llm_client=mock_llm,
            prompt_templates=prompt_templates,
            validator=problem_validator,
        )
        # Check that generate method has max_retries parameter
        sig = inspect.signature(gen.generate)
        assert 'max_retries' in sig.parameters
        # Should not raise
        assert gen._llm is not None