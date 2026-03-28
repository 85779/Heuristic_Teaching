"""E2E tests for full v2 intervention flow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.modules.intervention.service import InterventionService
from app.modules.intervention.models import (
    Intervention,
    InterventionRequest,
    InterventionResponse,
    InterventionStatus,
    InterventionType,
    FrontendSignalEnum,
    FeedbackRequest,
    BreakpointLocation,
    DimensionResult,
    SubTypeResult,
    PromptLevelEnum,
    EscalationDecision,
    EscalationAction,
    DimensionEnum,
)


@pytest.fixture
def mock_solving_state():
    """Mock solving state from SessionState."""
    return {
        "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列...",
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解", "content": "理解题目要求"},
            {"step_id": "s2", "step_name": "设定", "content": "设 a_0 = 1"},
            {"step_id": "s3", "step_name": "归纳", "content": "假设 a_k = m"},
        ],
        "student_steps": [
            {"step_id": "s1", "step_name": "理解", "content": "理解题目要求"},
        ],
        "student_work": "我令 a_0 = 1",
    }


@pytest.fixture
def service_with_mocks():
    """InterventionService with fully mocked dependencies."""
    service = InterventionService(context=None)

    # Mock the ContextManager
    service._context_manager = MagicMock()

    # Mock the BreakpointLocator
    service._locator = MagicMock()
    service._locator.locate = MagicMock(return_value=BreakpointLocation(
        breakpoint_position=1,
        breakpoint_type="MISSING_STEP",
        expected_step_content="设 a_0 = 1",
        gap_description="学生在第2步缺失",
        student_last_step="理解题目要求",
    ))

    # Mock the DimensionRouter
    service._router = MagicMock()
    service._router.route = AsyncMock(return_value=DimensionResult(
        dimension=DimensionEnum.RESOURCE,
        confidence=0.85,
        reasoning="学生缺少具体知识点",
    ))

    # Mock the SubTypeDecider
    service._decider = MagicMock()
    service._decider.decide = AsyncMock(return_value=SubTypeResult(
        sub_type=PromptLevelEnum.R2,
        confidence=0.75,
        reasoning="需要给出定理提示",
        hint_direction="考虑使用数学归纳法",
        escalation_decision=EscalationDecision(
            action=EscalationAction.MAINTAIN,
            from_level="R2",
            to_level=None,
            reasoning="维持当前级别",
        ),
    ))

    # Mock the HintGeneratorV2
    service._generator = MagicMock()
    service._generator.generate = AsyncMock(
        return_value="提示内容：考虑使用数学归纳法"
    )

    # Mock the OutputGuardrail
    service._guardrail = MagicMock()
    service._guardrail.check = AsyncMock(return_value=MagicMock(
        passed=True,
        reason="通过检查",
        violations=[],
    ))

    return service


class TestCreateIntervention:
    """Test creating a new intervention (first turn)."""

    @pytest.mark.asyncio
    async def test_create_intervention_success(
        self,
        service_with_mocks,
        mock_solving_state,
    ):
        """Test successful intervention creation."""
        request = InterventionRequest(
            student_id="student_001",
            session_id="session_001",
            student_input="我不知道下一步怎么走",
            frontend_signal=None,
        )

        # Mock loading solving state
        with patch.object(
            service_with_mocks,
            '_load_solving_state',
            return_value=mock_solving_state,
        ):
            response = await service_with_mocks.create_intervention(request)

        assert response.success is True
        assert response.intervention is not None
        assert response.intervention.content == "提示内容：考虑使用数学归纳法"
        assert response.intervention.metadata["prompt_level"] == "R2"
        assert response.intervention.metadata["dimension"] == "Resource"

    @pytest.mark.asyncio
    async def test_create_intervention_no_solving_state(
        self,
        service_with_mocks,
    ):
        """Test intervention creation with no solving state."""
        request = InterventionRequest(
            student_id="student_001",
            session_id="nonexistent_session",
            student_input="学生输入",
        )

        with patch.object(
            service_with_mocks,
            '_load_solving_state',
            return_value=None,
        ):
            response = await service_with_mocks.create_intervention(request)

        assert response.success is False
        assert "No solving state found" in response.message

    @pytest.mark.asyncio
    async def test_create_intervention_no_breakpoint(
        self,
        service_with_mocks,
        mock_solving_state,
    ):
        """Test intervention when student is on track (no breakpoint)."""
        # Set locator to return NO_BREAKPOINT
        service_with_mocks._locator.locate = MagicMock(return_value=BreakpointLocation(
            breakpoint_position=2,
            breakpoint_type="NO_BREAKPOINT",
            expected_step_content="",
            gap_description="学生解题步骤与参考解法一致",
            student_last_step="理解题目要求",
        ))

        request = InterventionRequest(
            student_id="student_001",
            session_id="session_001",
            student_input="学生输入",
        )

        with patch.object(
            service_with_mocks,
            '_load_solving_state',
            return_value=mock_solving_state,
        ):
            response = await service_with_mocks.create_intervention(request)

        assert response.success is True
        assert response.intervention is None
        assert "无断点" in response.message

    @pytest.mark.asyncio
    async def test_create_intervention_with_end_signal(
        self,
        service_with_mocks,
        mock_solving_state,
    ):
        """Test intervention creation with END signal."""
        request = InterventionRequest(
            student_id="student_001",
            session_id="session_001",
            student_input="",
            frontend_signal=FrontendSignalEnum.END,
        )

        with patch.object(
            service_with_mocks,
            '_load_solving_state',
            return_value=mock_solving_state,
        ):
            response = await service_with_mocks.create_intervention(request)

        assert response.success is True
        assert response.intervention is None
        assert "结束" in response.message


class TestProcessFeedback:
    """Test processing student feedback."""

    @pytest.mark.asyncio
    async def test_process_feedback_not_progressed(
        self,
        service_with_mocks,
    ):
        """Test feedback with NOT_PROGRESSED response."""
        # Setup context
        ctx = MagicMock()
        ctx.student_id = "student_001"
        ctx.student_input = "学生原始输入"
        ctx.dimension_result = DimensionResult(
            dimension=DimensionEnum.RESOURCE,
            confidence=0.8,
            reasoning="test",
        )
        ctx.current_level = "R2"
        ctx.intervention_memory = []
        ctx.status = InterventionStatus.ACTIVE

        service_with_mocks._context_manager.get_context.return_value = ctx
        service_with_mocks._context_manager.get_turn_count.return_value = 1
        service_with_mocks._context_manager.record_intervention.return_value = MagicMock()

        # Mock escalation
        service_with_mocks._context_manager.apply_escalation.return_value = "R3"

        request = FeedbackRequest(
            session_id="session_001",
            student_input="学生仍然不懂",
            frontend_signal=None,
        )

        with patch.object(
            service_with_mocks,
            '_load_solving_state',
            return_value={
                "problem": "题目",
                "solution_steps": [],
                "student_steps": [],
                "student_work": "学生输入",
            },
        ), patch.object(
            service_with_mocks,
            '_handle_no_progress',
            wraps=service_with_mocks._handle_no_progress,
        ) as mock_handle:
            response = await service_with_mocks.process_feedback(request)

        # Should call _handle_no_progress
        mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_feedback_with_end_signal(
        self,
        service_with_mocks,
    ):
        """Test feedback with END signal."""
        ctx = MagicMock()
        ctx.status = InterventionStatus.ACTIVE
        service_with_mocks._context_manager.get_context.return_value = ctx

        request = FeedbackRequest(
            session_id="session_001",
            student_input="我知道了",
            frontend_signal=FrontendSignalEnum.END,
        )

        response = await service_with_mocks.process_feedback(request)

        assert response.success is True
        assert "结束" in response.message

    @pytest.mark.asyncio
    async def test_process_feedback_no_session(
        self,
        service_with_mocks,
    ):
        """Test feedback with no existing session."""
        service_with_mocks._context_manager.get_context.return_value = None

        request = FeedbackRequest(
            session_id="nonexistent",
            student_input="学生输入",
        )

        response = await service_with_mocks.process_feedback(request)

        assert response.success is False
        assert "No active intervention" in response.message


class TestEndIntervention:
    """Test ending intervention."""

    @pytest.mark.asyncio
    async def test_end_intervention_success(
        self,
        service_with_mocks,
    ):
        """Test successful intervention end."""
        ctx = MagicMock()
        ctx.status = InterventionStatus.ACTIVE
        service_with_mocks._context_manager.get_context.return_value = ctx

        response = await service_with_mocks.end_intervention(
            session_id="session_001",
            reason="学生主动结束",
        )

        assert response.success is True
        assert "结束" in response.message


class TestEscalateIntervention:
    """Test escalating intervention."""

    @pytest.mark.asyncio
    async def test_escalate_intervention_success(
        self,
        service_with_mocks,
    ):
        """Test successful intervention escalation."""
        ctx = MagicMock()
        ctx.status = InterventionStatus.ACTIVE
        ctx.current_level = "R2"
        ctx.student_input = "学生输入"
        ctx.dimension_result = DimensionResult(
            dimension=DimensionEnum.RESOURCE,
            confidence=0.8,
            reasoning="test",
        )
        ctx.intervention_memory = []
        ctx.student_id = "student_001"

        service_with_mocks._context_manager.get_context.return_value = ctx
        service_with_mocks._context_manager.handle_frontend_signal.return_value = "R3"
        service_with_mocks._context_manager.get_turn_count.return_value = 1

        # Mock _generate_hint_at_current_level
        with patch.object(
            service_with_mocks,
            '_generate_hint_at_current_level',
            wraps=service_with_mocks._generate_hint_at_current_level,
        ) as mock_gen:
            mock_gen.return_value = InterventionResponse(
                success=True,
                intervention=Intervention(
                    id="int_test123",
                    student_id="student_001",
                    session_id="session_001",
                    intervention_type=InterventionType.HINT,
                    status=InterventionStatus.SUGGESTED,
                    content="升级后的提示",
                    intensity=0.5,
                    metadata={"prompt_level": "R3"},
                ),
                message="Generated escalated R3 hint",
            )

            response = await service_with_mocks.escalate_intervention(
                session_id="session_001",
                reason="学生要求更多帮助",
            )

        assert response.success is True

    @pytest.mark.asyncio
    async def test_escalate_at_max_level(
        self,
        service_with_mocks,
    ):
        """Test escalation when at max level (should terminate)."""
        ctx = MagicMock()
        ctx.status = InterventionStatus.ACTIVE
        ctx.current_level = "R4"  # Max level

        service_with_mocks._context_manager.get_context.return_value = ctx
        service_with_mocks._context_manager.handle_frontend_signal.return_value = "TERMINATED"

        response = await service_with_mocks.escalate_intervention(
            session_id="session_001",
        )

        assert response.success is True
        assert "最高" in response.message or "终止" in response.message


class TestHelperMethods:
    """Test service helper methods."""

    def test_location_to_dict(
        self,
        service_with_mocks,
    ):
        """Test BreakpointLocation to dict conversion."""
        location = BreakpointLocation(
            breakpoint_position=1,
            breakpoint_type="MISSING_STEP",
            expected_step_content="设 a_0 = 1",
            gap_description="学生在第2步缺失",
            student_last_step="理解题目要求",
        )

        result = service_with_mocks._location_to_dict(location)

        assert result["breakpoint_position"] == 1
        assert result["breakpoint_type"] == "MISSING_STEP"
        assert result["expected_step_content"] == "设 a_0 = 1"

    def test_determine_student_response_accepted(
        self,
        service_with_mocks,
    ):
        """Test determining ACCEPTED response."""
        from app.modules.intervention.models import StudentResponseEnum

        ctx = MagicMock()
        ctx.student_input = "学生原来的输入"

        result = service_with_mocks._determine_student_response(
            student_input="这是新的学生输入，非常长并且包含了新的解题思路",
            ctx=ctx,
        )

        assert result == StudentResponseEnum.ACCEPTED

    def test_determine_student_response_not_progressed(
        self,
        service_with_mocks,
    ):
        """Test determining NOT_PROGRESSED response."""
        from app.modules.intervention.models import StudentResponseEnum

        ctx = MagicMock()
        ctx.student_input = "学生原来的输入"

        result = service_with_mocks._determine_student_response(
            student_input="",
            ctx=ctx,
        )

        assert result == StudentResponseEnum.NOT_PROGRESSED

    def test_fallback_hint(
        self,
        service_with_mocks,
    ):
        """Test fallback hint generation."""
        from app.modules.intervention.models import PromptLevelEnum

        result = service_with_mocks._fallback_hint(
            level=PromptLevelEnum.R1,
            problem_context="题目",
            expected_step="期望步骤",
        )

        assert result is not None
        assert len(result) > 0
