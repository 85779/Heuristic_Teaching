"""E2E tests for HintGeneratorV2 (Node 4)."""

import pytest
from unittest.mock import AsyncMock, patch
from app.modules.intervention.generator.hints_v2 import (
    HintGeneratorV2,
    build_generator_prompt,
    format_student_steps,
    LEVEL_PROMPTS,
)
from app.modules.intervention.models import PromptLevelEnum


@pytest.fixture
def hint_generator_v2():
    """Fresh HintGeneratorV2 instance with mocked LLM."""
    generator = HintGeneratorV2()
    return generator


@pytest.fixture
def sample_problem_context():
    """Sample math problem context."""
    return "设 $a_0, a_1, \\ldots$ 是正整数序列，满足 $a_{n+1} = \\gcd(a_n, a_{n+1})$。证明：存在正整数 $k$ 使得 $a_k = a_{k+1} = \\cdots$。"


@pytest.fixture
def sample_student_steps():
    """Sample student steps."""
    return [
        {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
        {"step_id": "s2", "step_name": "设定", "content": "令 a_0 = 1"},
    ]


class TestHintGeneratorV2:
    """Test Node 4: Hint Generator V2 (R1-R4 / M1-M5 prompts)."""

    @pytest.mark.asyncio
    async def test_generate_r1_hint(
        self,
        hint_generator_v2,
        sample_problem_context,
        sample_student_steps,
    ):
        """Test generating R1 hint."""
        mock_response = '{"hint_content": "思考题目中已知条件和所求目标之间的关系", "approach_hint": "从条件出发"}'

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(hint_generator_v2, '_get_llm_client', return_value=mock_client):
            result = await hint_generator_v2.generate(
                level=PromptLevelEnum.R1,
                problem_context=sample_problem_context,
                student_input="我令 a_0 = 1",
                expected_step="则 a_1 = gcd(a_0, a_1)",
                student_steps=sample_student_steps,
            )

        assert "关系" in result or "条件" in result

    @pytest.mark.asyncio
    async def test_generate_r2_hint(
        self,
        hint_generator_v2,
        sample_problem_context,
        sample_student_steps,
    ):
        """Test generating R2 hint (theorem knowledge)."""
        mock_response = '{"hint_content": "考虑使用数学归纳法来证明", "knowledge_hint": "数学归纳法"}'

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(hint_generator_v2, '_get_llm_client', return_value=mock_client):
            result = await hint_generator_v2.generate(
                level=PromptLevelEnum.R2,
                problem_context=sample_problem_context,
                student_input="我令 a_0 = 1",
                expected_step="使用数学归纳法",
                student_steps=sample_student_steps,
            )

        assert "归纳法" in result or "定理" in result

    @pytest.mark.asyncio
    async def test_generate_m1_hint(
        self,
        hint_generator_v2,
        sample_problem_context,
        sample_student_steps,
    ):
        """Test generating M1 hint (should continue?)."""
        mock_response = '{"hint_content": "你觉得当前的解题方向是否正确？是否应该尝试其他方法？", "question_to_student": "当前路径是否正确？"}'

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(hint_generator_v2, '_get_llm_client', return_value=mock_client):
            result = await hint_generator_v2.generate(
                level=PromptLevelEnum.M1,
                problem_context=sample_problem_context,
                student_input="我不知道该怎么办",
                expected_step="设 a_0 = 1",
                student_steps=sample_student_steps,
            )

        assert "是否" in result or "方向" in result

    @pytest.mark.asyncio
    async def test_generate_fallback_on_invalid_json(
        self,
        hint_generator_v2,
        sample_problem_context,
    ):
        """Test fallback when LLM returns invalid JSON."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Invalid JSON response"

        with patch.object(hint_generator_v2, '_get_llm_client', return_value=mock_client):
            result = await hint_generator_v2.generate(
                level=PromptLevelEnum.R1,
                problem_context=sample_problem_context,
                student_input="学生输入",
                expected_step="期望步骤",
                student_steps=[],
            )

        # Should return raw response
        assert result == "Invalid JSON response"


class TestPromptTemplates:
    """Test R1-R4 / M1-M5 prompt templates."""

    def test_all_levels_have_prompts(self):
        """Test that all 9 levels have prompt templates."""
        expected_levels = [
            PromptLevelEnum.R1,
            PromptLevelEnum.R2,
            PromptLevelEnum.R3,
            PromptLevelEnum.R4,
            PromptLevelEnum.M1,
            PromptLevelEnum.M2,
            PromptLevelEnum.M3,
            PromptLevelEnum.M4,
            PromptLevelEnum.M5,
        ]

        for level in expected_levels:
            assert level in LEVEL_PROMPTS, f"Missing prompt for {level}"

    def test_build_generator_prompt_r1(self, sample_problem_context):
        """Test building R1 prompt."""
        prompt = build_generator_prompt(
            level=PromptLevelEnum.R1,
            problem_context=sample_problem_context,
            student_input="学生输入",
            expected_step="期望步骤",
            student_steps=[{"step_id": "s1", "content": "第一步"}],
        )

        assert sample_problem_context in prompt
        assert "R1" in prompt
        assert "第一步" in prompt

    def test_build_generator_prompt_m3(self, sample_problem_context):
        """Test building M3 prompt."""
        prompt = build_generator_prompt(
            level=PromptLevelEnum.M3,
            problem_context=sample_problem_context,
            student_input="学生输入",
            expected_step="期望步骤",
            student_steps=[],
        )

        assert "M3" in prompt

    def test_format_student_steps_empty(self):
        """Test formatting empty student steps."""
        result = format_student_steps([])
        assert result == "（无）"

    def test_format_student_steps_with_content(self):
        """Test formatting student steps with content."""
        steps = [
            {"step_id": "s1", "step_name": "理解", "content": "理解题目要求"},
            {"step_id": "s2", "step_name": "设定", "content": "令 a_0 = 1"},
        ]

        result = format_student_steps(steps)

        assert "1." in result
        assert "理解题目要求" in result
        assert "令 a_0 = 1" in result


class TestLevelSpecificPrompts:
    """Test level-specific prompt characteristics."""

    def test_r1_prompt_is_directional(self):
        """Test that R1 prompt is directional (no theorem content)."""
        prompt = LEVEL_PROMPTS[PromptLevelEnum.R1]

        # R1 should NOT mention specific theorems
        assert "定理" not in prompt or "具体" in prompt
        # R1 should focus on direction
        assert "方向" in prompt or "思考" in prompt

    def test_r2_prompt_includes_knowledge(self):
        """Test that R2 prompt includes knowledge/hint."""
        prompt = LEVEL_PROMPTS[PromptLevelEnum.R2]

        assert "定理" in prompt or "知识" in prompt

    def test_r4_prompt_includes_computation(self):
        """Test that R4 prompt includes computation."""
        prompt = LEVEL_PROMPTS[PromptLevelEnum.R4]

        assert "计算" in prompt or "具体" in prompt

    def test_m1_prompt_is_question(self):
        """Test that M1 prompt asks a question."""
        prompt = LEVEL_PROMPTS[PromptLevelEnum.M1]

        assert "问题" in prompt or "question" in prompt.lower()

    def test_m3_prompt_includes_method(self):
        """Test that M3 prompt includes method hint."""
        prompt = LEVEL_PROMPTS[PromptLevelEnum.M3]

        assert "方法" in prompt
