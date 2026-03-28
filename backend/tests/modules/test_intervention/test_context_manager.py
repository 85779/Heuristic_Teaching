"""E2E tests for ContextManager."""

import pytest
from datetime import datetime
from app.modules.intervention.context_manager import ContextManager
from app.modules.intervention.models import (
    InterventionStatus,
    DimensionEnum,
    PromptLevelEnum,
    StudentResponseEnum,
    FrontendSignalEnum,
    QaHistory,
    InterventionRecord,
    BreakpointLocation,
    DimensionResult,
    SubTypeResult,
    EscalationDecision,
    EscalationAction,
)


@pytest.fixture
def context_manager():
    """Fresh ContextManager instance."""
    return ContextManager()


@pytest.fixture
def sample_context_params():
    """Sample parameters for creating an intervention context."""
    return {
        "session_id": "test_session_001",
        "student_id": "student_001",
        "problem_context": "设 $a_0, a_1, \\ldots$ 是正整数序列...",
        "student_input": "我令 a_0 = 1",
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
            {"step_id": "s2", "step_name": "构造", "content": "设 a_0 = 1"},
        ],
        "student_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
        ],
    }


class TestContextManagerLifecycle:
    """Test context creation, retrieval, and updates."""

    def test_create_new_context(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test creating a new intervention context."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        assert ctx.session_id == "test_session_001"
        assert ctx.student_id == "student_001"
        assert ctx.problem_context == sample_context_params["problem_context"]
        assert ctx.status == InterventionStatus.ACTIVE
        assert len(ctx.intervention_memory) == 0

    def test_get_existing_context(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test retrieving an existing context."""
        # Create first
        ctx1 = context_manager.get_or_create_context(**sample_context_params)

        # Get again
        ctx2 = context_manager.get_or_create_context(**sample_context_params)

        assert ctx1 is ctx2  # Same object

    def test_update_breakpoint_location(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test updating breakpoint location."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        location = BreakpointLocation(
            breakpoint_position=1,
            breakpoint_type="MISSING_STEP",
            expected_step_content="设 a_0 = 1",
            gap_description="学生在第2步缺失",
            student_last_step="理解题目要求",
        )

        context_manager.update_breakpoint_location("test_session_001", location)

        assert ctx.breakpoint_location is not None
        assert ctx.breakpoint_location.breakpoint_position == 1

    def test_update_dimension_result(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test updating dimension routing result."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        result = DimensionResult(
            dimension=DimensionEnum.RESOURCE,
            confidence=0.85,
            reasoning="学生缺少具体知识点",
        )

        context_manager.update_dimension_result("test_session_001", result)

        assert ctx.dimension_result is not None
        assert ctx.dimension_result.dimension == DimensionEnum.RESOURCE

    def test_update_sub_type_result(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test updating sub-type decision result."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        result = SubTypeResult(
            sub_type=PromptLevelEnum.R2,
            confidence=0.7,
            reasoning="需要给出定理提示",
            hint_direction="考虑使用数学归纳法",
        )

        context_manager.update_sub_type_result("test_session_001", result)

        assert ctx.sub_type_result is not None
        assert ctx.current_level == "R2"

    def test_get_turn_count(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test turn counter."""
        context_manager.get_or_create_context(**sample_context_params)

        assert context_manager.get_turn_count("test_session_001") == 0

        # Record some interventions
        context_manager.record_intervention(
            session_id="test_session_001",
            student_q="学生问题1",
            system_a="系统回答1",
            prompt_level="R1",
            prompt_content="prompt1",
            student_response=StudentResponseEnum.NOT_PROGRESSED,
        )

        assert context_manager.get_turn_count("test_session_001") == 1


class TestEscalationLogic:
    """Test escalation and switching logic."""

    def test_maintain_level(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test MAINTAIN escalation action."""
        ctx = context_manager.get_or_create_context(**sample_context_params)
        ctx.current_level = "R2"

        decision = EscalationDecision(
            action=EscalationAction.MAINTAIN,
            from_level="R2",
            to_level=None,
            reasoning="保持当前级别",
        )

        new_level = context_manager.apply_escalation("test_session_001", decision)

        assert new_level == "R2"

    def test_escalate_level(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test ESCALATE action."""
        ctx = context_manager.get_or_create_context(**sample_context_params)
        ctx.current_level = "R1"

        decision = EscalationDecision(
            action=EscalationAction.ESCALATE,
            from_level="R1",
            to_level="R2",
            reasoning="升级到R2",
        )

        new_level = context_manager.apply_escalation("test_session_001", decision)

        assert new_level == "R2"

    def test_switch_to_resource(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test SWITCH_TO_RESOURCE action (M-side failure)."""
        ctx = context_manager.get_or_create_context(**sample_context_params)
        ctx.current_level = "M3"
        ctx.dimension_result = DimensionResult(
            dimension=DimensionEnum.METACOGNITIVE,
            confidence=0.8,
            reasoning="Metacognitive dimension",
        )

        decision = EscalationDecision(
            action=EscalationAction.SWITCH_TO_RESOURCE,
            from_level="M3",
            to_level="R1",
            reasoning="M-side failure, switch to R",
        )

        new_level = context_manager.apply_escalation("test_session_001", decision)

        assert new_level == "R1"
        assert ctx.dimension_result is None  # Cleared

    def test_max_level_reached(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test MAX_LEVEL_REACHED action (R-side R4)."""
        ctx = context_manager.get_or_create_context(**sample_context_params)
        ctx.current_level = "R4"

        decision = EscalationDecision(
            action=EscalationAction.MAX_LEVEL_REACHED,
            from_level="R4",
            to_level=None,
            reasoning="已达到最高级别",
        )

        new_level = context_manager.apply_escalation("test_session_001", decision)

        assert new_level == "TERMINATED"
        assert ctx.status == InterventionStatus.TERMINATED


class TestFrontendSignals:
    """Test frontend signal handling."""

    def test_handle_end_signal(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test END signal terminates intervention."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        result = context_manager.handle_frontend_signal(
            "test_session_001",
            FrontendSignalEnum.END,
        )

        assert result == "TERMINATED"
        assert ctx.status == InterventionStatus.COMPLETED

    def test_handle_escalate_signal(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test ESCALATE signal escalates level."""
        ctx = context_manager.get_or_create_context(**sample_context_params)
        ctx.current_level = "R1"

        result = context_manager.handle_frontend_signal(
            "test_session_001",
            FrontendSignalEnum.ESCALATE,
        )

        assert result == "R2"
        assert ctx.current_level == "R2"


class TestInterventionHistory:
    """Test intervention memory and history."""

    def test_record_intervention(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test recording an intervention turn."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        record = context_manager.record_intervention(
            session_id="test_session_001",
            student_q="学生不知道下一步怎么走",
            system_a="提示：考虑使用数学归纳法",
            prompt_level="R2",
            prompt_content="R2 prompt content",
            student_response=StudentResponseEnum.NOT_PROGRESSED,
        )

        assert record.turn == 1
        assert record.prompt_level == "R2"
        assert record.student_response == StudentResponseEnum.NOT_PROGRESSED
        assert len(ctx.intervention_memory) == 1

    def test_memory_summary_empty(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test memory summary with no history."""
        context_manager.get_or_create_context(**sample_context_params)

        summary = context_manager.get_memory_summary("test_session_001")

        assert "无历史干预记录" in summary

    def test_memory_summary_with_history(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test memory summary with intervention history."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        # Record multiple turns
        for i in range(3):
            context_manager.record_intervention(
                session_id="test_session_001",
                student_q=f"学生问题{i+1}",
                system_a=f"提示{i+1}",
                prompt_level=f"R{i+1}",
                prompt_content=f"prompt{i+1}",
                student_response=StudentResponseEnum.NOT_PROGRESSED,
            )

        summary = context_manager.get_memory_summary("test_session_001")

        assert "近3轮" in summary
        assert "R1" in summary
        assert "R3" in summary


class TestSaveRestore:
    """Test context persistence (serialization)."""

    def test_save_context(
        self,
        context_manager,
        sample_context_params,
    ):
        """Test serializing context for MongoDB storage."""
        ctx = context_manager.get_or_create_context(**sample_context_params)

        # Record an intervention and manually set current_level
        context_manager.record_intervention(
            session_id="test_session_001",
            student_q="学生问题",
            system_a="提示内容",
            prompt_level="R2",
            prompt_content="prompt",
            student_response=StudentResponseEnum.NOT_PROGRESSED,
        )

        # Manually set current_level since it's not set by record_intervention
        ctx.current_level = "R2"

        saved = context_manager.save_context("test_session_001")

        assert saved["session_id"] == "test_session_001"
        assert saved["student_id"] == "student_001"
        assert saved["current_level"] == "R2"
        assert len(saved["intervention_memory"]) == 1

    def test_restore_context(
        self,
        context_manager,
    ):
        """Test restoring context from saved state."""
        # Create and save a context first
        params = {
            "session_id": "restore_test",
            "student_id": "student_002",
            "problem_context": "测试题目",
            "student_input": "学生输入",
            "solution_steps": [{"step_id": "s1", "content": "步骤1"}],
            "student_steps": [],
            "intervention_memory": [
                {
                    "turn": 1,
                    "qa_history": {
                        "student_q": "学生问题",
                        "system_a": "系统回答",
                    },
                    "prompt_level": "R1",
                    "prompt_content": "prompt",
                    "student_response": "not_progressed",
                    "frontend_signal": None,
                    "breakpoint_status": "persistent",
                    "created_at": datetime.utcnow(),
                }
            ],
            "current_level": "R1",
            "status": "active",
        }

        ctx = context_manager.restore_from_session(**params)

        assert ctx.session_id == "restore_test"
        assert ctx.student_id == "student_002"
        assert len(ctx.intervention_memory) == 1
        assert ctx.intervention_memory[0].prompt_level == "R1"
