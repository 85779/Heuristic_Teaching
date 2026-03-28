"""E2E tests for DimensionRouter (Node 2a)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.modules.intervention.router.dimension_router import DimensionRouter
from app.modules.intervention.models import (
    DimensionEnum,
    DimensionResult,
    InterventionRecord,
    StudentResponseEnum,
)


@pytest.fixture
def dimension_router():
    """Fresh DimensionRouter instance with mocked LLM."""
    router = DimensionRouter()
    return router


@pytest.fixture
def mock_llm_response_dimension():
    """Mock LLM response for R/M classification."""
    return """```json
{
    "dimension": "Resource",
    "confidence": 0.85,
    "reasoning": "学生缺少具体的数学知识点（需要用余数定理）"
}
```"""


class TestDimensionRouter:
    """Test Node 2a: Dimension Router (R/M classification)."""

    @pytest.mark.asyncio
    async def test_route_resource_dimension(
        self,
        dimension_router,
        mock_llm_response_dimension,
    ):
        """Test routing to Resource dimension."""
        # Mock the LLM client
        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_llm_response_dimension

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            result = await dimension_router.route(
                student_input="我令 a_0 = 1",
                expected_step="设 a_0 = 1，则 a_1 = gcd(a_0, a_1)",
                breakpoint_type="MISSING_STEP",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert isinstance(result, DimensionResult)
        assert result.dimension == DimensionEnum.RESOURCE
        assert result.confidence == 0.85
        assert "知识点" in result.reasoning

    @pytest.mark.asyncio
    async def test_route_metacognitive_dimension(
        self,
        dimension_router,
    ):
        """Test routing to Metacognitive dimension."""
        mock_response = """```json
{
    "dimension": "Metacognitive",
    "confidence": 0.78,
    "reasoning": "学生需要反思当前解题方向是否正确"
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            result = await dimension_router.route(
                student_input="我不知道该不该继续",
                expected_step="设 a_0 = 1",
                breakpoint_type="STUCK",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.dimension == DimensionEnum.METACOGNITIVE
        assert result.confidence == 0.78

    @pytest.mark.asyncio
    async def test_route_with_memory(
        self,
        dimension_router,
    ):
        """Test routing with intervention memory."""
        mock_response = """```json
{
    "dimension": "Metacognitive",
    "confidence": 0.82,
    "reasoning": "多次R-level提示未生效，考虑M-level"
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        memory = [
            InterventionRecord(
                turn=1,
                qa_history={"student_q": "学生问题1", "system_a": "提示1"},
                prompt_level="R1",
                prompt_content="R1 prompt",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
            InterventionRecord(
                turn=2,
                qa_history={"student_q": "学生问题2", "system_a": "提示2"},
                prompt_level="R2",
                prompt_content="R2 prompt",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
        ]

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            result = await dimension_router.route(
                student_input="还是不懂",
                expected_step="设 a_0 = 1",
                breakpoint_type="MISSING_STEP",
                intervention_memory=memory,
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.dimension == DimensionEnum.METACOGNITIVE

    @pytest.mark.asyncio
    async def test_route_fallback_on_parse_error(
        self,
        dimension_router,
    ):
        """Test fallback to Resource on JSON parse error."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Invalid JSON response"

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            result = await dimension_router.route(
                student_input="学生输入",
                expected_step="期望步骤",
                breakpoint_type="MISSING_STEP",
                problem_context="题目",
            )

        # Should default to Resource on parse error
        assert result.dimension == DimensionEnum.RESOURCE
        assert result.confidence == 0.0
        assert "解析失败" in result.reasoning

    @pytest.mark.asyncio
    async def test_route_empty_student_input(
        self,
        dimension_router,
    ):
        """Test routing with empty student input."""
        mock_response = """```json
{
    "dimension": "Resource",
    "confidence": 0.9,
    "reasoning": "学生没有输入，缺少第一步"
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            result = await dimension_router.route(
                student_input="",
                expected_step="设 a_0 = 1",
                breakpoint_type="MISSING_STEP",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.dimension == DimensionEnum.RESOURCE


class TestDimensionRouterPrompt:
    """Test DimensionRouter prompt construction."""

    @pytest.mark.asyncio
    async def test_prompt_includes_breakpoint_type(
        self,
        dimension_router,
    ):
        """Test that prompt includes breakpoint type information."""
        captured_prompt = None

        async def capture_chat(messages, **kwargs):
            nonlocal captured_prompt
            captured_prompt = messages[0].content
            return '{"dimension": "Resource", "confidence": 0.5, "reasoning": "test"}'

        mock_client = AsyncMock()
        mock_client.chat = capture_chat

        with patch.object(dimension_router, '_get_llm_client', return_value=mock_client):
            await dimension_router.route(
                student_input="学生输入",
                expected_step="期望步骤",
                breakpoint_type="WRONG_DIRECTION",
                problem_context="题目内容",
            )

        # Verify prompt contains breakpoint type
        assert "WRONG_DIRECTION" in captured_prompt
        assert "题目内容" in captured_prompt
