"""E2E tests for SubTypeDecider (Node 2b)."""

import pytest
from unittest.mock import AsyncMock, patch
from app.modules.intervention.decider.sub_type_decider import SubTypeDecider
from app.modules.intervention.models import (
    DimensionEnum,
    PromptLevelEnum,
    SubTypeResult,
    EscalationAction,
    InterventionRecord,
    StudentResponseEnum,
)


@pytest.fixture
def sub_type_decider():
    """Fresh SubTypeDecider instance with mocked LLM."""
    decider = SubTypeDecider()
    return decider


@pytest.fixture
def mock_resource_response():
    """Mock LLM response for Resource side."""
    return """```json
{
    "sub_type": "R2",
    "confidence": 0.75,
    "reasoning": "需要给出具体定理提示",
    "hint_direction": "考虑使用数学归纳法",
    "escalation_decision": {
        "action": "maintain",
        "from_level": "R2",
        "to_level": null,
        "reasoning": "当前级别合适"
    }
}
```"""


class TestSubTypeDecider:
    """Test Node 2b: Sub-type Decider (level decision + escalation)."""

    @pytest.mark.asyncio
    async def test_decide_resource_level_r2(
        self,
        sub_type_decider,
        mock_resource_response,
    ):
        """Test deciding R2 level for Resource dimension."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_resource_response

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.RESOURCE,
                student_input="我令 a_0 = 1",
                expected_step="设 a_0 = 1，则 a_1 = gcd(a_0, a_1)",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert isinstance(result, SubTypeResult)
        assert result.sub_type == PromptLevelEnum.R2
        assert result.confidence == 0.75
        assert "数学归纳法" in result.hint_direction

    @pytest.mark.asyncio
    async def test_decide_metacognitive_level_m2(
        self,
        sub_type_decider,
    ):
        """Test deciding M2 level for Metacognitive dimension."""
        mock_response = """```json
{
    "sub_type": "M2",
    "confidence": 0.8,
    "reasoning": "需要给出方向指引",
    "hint_direction": "从已知条件出发思考",
    "escalation_decision": {
        "action": "escalate",
        "from_level": "M1",
        "to_level": "M2",
        "reasoning": "升级到M2"
    }
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.METACOGNITIVE,
                student_input="我不知道该不该继续",
                expected_step="设 a_0 = 1",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.sub_type == PromptLevelEnum.M2
        assert result.escalation_decision.action == EscalationAction.ESCALATE
        assert result.escalation_decision.to_level == "M2"

    @pytest.mark.asyncio
    async def test_decide_with_memory(
        self,
        sub_type_decider,
    ):
        """Test deciding with intervention memory."""
        mock_response = """```json
{
    "sub_type": "R3",
    "confidence": 0.7,
    "reasoning": "R2无效，升级到R3",
    "hint_direction": "给出第一步的理论形式",
    "escalation_decision": {
        "action": "escalate",
        "from_level": "R2",
        "to_level": "R3",
        "reasoning": "升级"
    }
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        memory = [
            InterventionRecord(
                turn=1,
                qa_history={"student_q": "学生问题", "system_a": "提示"},
                prompt_level="R1",
                prompt_content="R1 prompt",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
            InterventionRecord(
                turn=2,
                qa_history={"student_q": "还是不懂", "system_a": "提示2"},
                prompt_level="R2",
                prompt_content="R2 prompt",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
        ]

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.RESOURCE,
                student_input="学生继续提问",
                expected_step="设 a_0 = 1",
                intervention_memory=memory,
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.sub_type == PromptLevelEnum.R3

    @pytest.mark.asyncio
    async def test_decide_frontend_escalate_signal(
        self,
        sub_type_decider,
    ):
        """Test deciding with frontend ESCALATE signal."""
        mock_response = """```json
{
    "sub_type": "R3",
    "confidence": 0.9,
    "reasoning": "前端要求升级",
    "hint_direction": "强制升级",
    "escalation_decision": {
        "action": "escalate",
        "from_level": "R2",
        "to_level": "R3",
        "reasoning": "响应前端ESCALATE"
    }
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.RESOURCE,
                student_input="学生要求更多帮助",
                expected_step="设 a_0 = 1",
                current_level="R2",
                frontend_signal="ESCALATE",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        # Should include frontend signal in prompt (checked via assertion in mock)
        mock_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_decide_fallback_on_parse_error(
        self,
        sub_type_decider,
    ):
        """Test fallback to R1 on JSON parse error."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Invalid JSON"

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.RESOURCE,
                student_input="学生输入",
                expected_step="期望步骤",
                problem_context="题目",
            )

        # Should default to R1 for Resource dimension
        assert result.sub_type == PromptLevelEnum.R1
        assert result.confidence == 0.0


class TestSubTypeDeciderEscalation:
    """Test escalation logic in SubTypeDecider."""

    @pytest.mark.asyncio
    async def test_switch_to_resource_decision(
        self,
        sub_type_decider,
    ):
        """Test SWITCH_TO_RESOURCE escalation decision (M-side failure)."""
        mock_response = """```json
{
    "sub_type": "R1",
    "confidence": 0.6,
    "reasoning": "M-side failed, switch to R",
    "hint_direction": "从R1开始",
    "escalation_decision": {
        "action": "switch_to_resource",
        "from_level": "M3",
        "to_level": "R1",
        "reasoning": "M-side failure"
    }
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.METACOGNITIVE,
                student_input="完全不懂",
                expected_step="设 a_0 = 1",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.sub_type == PromptLevelEnum.R1
        assert result.escalation_decision.action == EscalationAction.SWITCH_TO_RESOURCE

    @pytest.mark.asyncio
    async def test_max_level_reached_decision(
        self,
        sub_type_decider,
    ):
        """Test MAX_LEVEL_REACHED escalation decision (R4 max)."""
        mock_response = """```json
{
    "sub_type": "R4",
    "confidence": 0.95,
    "reasoning": "已达最高级别",
    "hint_direction": "给出完整第一步",
    "escalation_decision": {
        "action": "max_level_reached",
        "from_level": "R4",
        "to_level": null,
        "reasoning": "R4是Resource侧最高级"
    }
}
```"""

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(sub_type_decider, '_get_llm_client', return_value=mock_client):
            result = await sub_type_decider.decide(
                dimension=DimensionEnum.RESOURCE,
                student_input="还是不懂",
                expected_step="设 a_0 = 1",
                current_level="R4",
                problem_context="设 a_0, a_1, ... 是正整数序列...",
            )

        assert result.sub_type == PromptLevelEnum.R4
        assert result.escalation_decision.action == EscalationAction.MAX_LEVEL_REACHED


class TestMemorySummary:
    """Test memory summary building in SubTypeDecider."""

    def test_build_memory_summary_empty(self, sub_type_decider):
        """Test building memory summary with no history."""
        summary = sub_type_decider._build_memory_summary([])

        assert summary == "无历史干预记录"

    def test_build_memory_summary_recent_turns(self, sub_type_decider):
        """Test building memory summary with recent turns."""
        memory = [
            InterventionRecord(
                turn=1,
                qa_history={"student_q": "问题1", "system_a": "回答1"},
                prompt_level="R1",
                prompt_content="prompt1",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
            InterventionRecord(
                turn=2,
                qa_history={"student_q": "问题2", "system_a": "回答2"},
                prompt_level="R2",
                prompt_content="prompt2",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
        ]

        summary = sub_type_decider._build_memory_summary(memory)

        assert "近2轮" in summary
        assert "R1" in summary
        assert "R2" in summary

    def test_build_memory_summary_with_older_turns(self, sub_type_decider):
        """Test building memory summary with older turns."""
        memory = [
            InterventionRecord(
                turn=1,
                qa_history={"student_q": "早期问题", "system_a": "早期回答"},
                prompt_level="R1",
                prompt_content="prompt",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
            InterventionRecord(
                turn=2,
                qa_history={"student_q": "问题2", "system_a": "回答2"},
                prompt_level="R2",
                prompt_content="prompt2",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            ),
            InterventionRecord(
                turn=3,
                qa_history={"student_q": "问题3", "system_a": "回答3"},
                prompt_level="R3",
                prompt_content="prompt3",
                student_response="not_progressed",
            ),
        ]

        summary = sub_type_decider._build_memory_summary(memory, max_turns=2)

        assert "近2轮" in summary
        assert "早期1轮" in summary
        assert "尝试了 R1" in summary
