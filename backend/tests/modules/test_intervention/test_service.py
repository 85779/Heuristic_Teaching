"""Tests for InterventionService v2."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.modules.intervention.service import InterventionService
from app.modules.intervention.models import (
    InterventionType,
    InterventionStatus,
    Intervention,
    InterventionRequest,
    InterventionResponse,
    BreakpointLocation,
    DimensionResult,
    SubTypeResult,
    PromptLevelEnum,
    EscalationDecision,
    EscalationAction,
    DimensionEnum,
)


@pytest.fixture
def mock_service():
    """InterventionService with fully mocked dependencies."""
    service = InterventionService(context=None)

    # Mock the ContextManager
    service._context_manager = MagicMock()

    # Mock the BreakpointLocator
    service._locator = MagicMock()
    service._locator.locate = MagicMock(return_value=BreakpointLocation(
        breakpoint_position=1,
        breakpoint_type="MISSING_STEP",
        expected_step_content="next step",
        gap_description="第2步缺失",
        student_last_step="step 1",
    ))

    # Mock the DimensionRouter
    service._router = MagicMock()
    service._router.route = AsyncMock(return_value=DimensionResult(
        dimension=DimensionEnum.RESOURCE,
        confidence=0.85,
        reasoning="学生缺少知识点",
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


@pytest.mark.asyncio
async def test_generate_returns_intervention(mock_service):
    """service.generate() returns an Intervention object from SessionState."""
    from app.modules.solving.models import TeachingStep

    # Setup state manager with solving state
    from app.core.state.state_manager import StateManager
    state_manager = StateManager()
    state_manager.set_module_state("sess_1", "solving", {
        "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列...",
        "student_work": "我令 a_0 = 1",
        "student_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
        ],
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
            {"step_id": "s2", "step_name": "设定", "content": "设 a_0 = 1"},
        ],
    })

    # Mock context
    mock_context = MagicMock()
    mock_context.state_manager = state_manager
    mock_context.logger = MagicMock()

    service = mock_service
    service._context = mock_context

    # Mock context_manager to return a proper context
    service._context_manager.get_or_create_context = MagicMock(return_value=MagicMock(
        session_id="sess_1",
        student_id="student_1",
        problem_context="设 $a_0, a_1, \\ldots$ 是正整数序列...",
        student_input="我令 a_0 = 1",
        solution_steps=[
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"},
            {"step_id": "s2", "step_name": "设定", "content": "设 a_0 = 1"},
        ],
        student_steps=[{"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求"}],
        breakpoint_location=None,
        dimension_result=None,
        sub_type_result=None,
        intervention_memory=[],
        current_level="",
        status=InterventionStatus.ACTIVE,
        is_active=MagicMock(return_value=True),
        is_terminated=MagicMock(return_value=False),
        is_completed=MagicMock(return_value=False),
    ))
    service._context_manager.get_context = MagicMock(return_value=MagicMock(
        session_id="sess_1",
        student_id="student_1",
        current_level="R2",
        student_input="我令 a_0 = 1",
        dimension_result=DimensionResult(dimension=DimensionEnum.RESOURCE, confidence=0.8, reasoning="test"),
        intervention_memory=[],
        status=InterventionStatus.ACTIVE,
    ))
    service._context_manager.get_turn_count = MagicMock(return_value=1)
    service._context_manager.record_intervention = MagicMock(return_value=MagicMock())
    service._context_manager.apply_escalation = MagicMock(return_value="R2")

    # Call generate (legacy wrapper)
    result = await service.generate(
        session_id="sess_1",
        intensity=0.3,
        student_id="student_1",
    )

    assert result is not None
    assert result.intervention_type == InterventionType.HINT
    assert result.status == InterventionStatus.SUGGESTED
    assert result.content == "提示内容：考虑使用数学归纳法"
    assert result.session_id == "sess_1"
    assert result.student_id == "student_1"


@pytest.mark.asyncio
async def test_deliver_intervention():
    """deliver_intervention updates status to DELIVERED."""
    service = InterventionService()

    intervention = Intervention(
        id="int_test",
        student_id="student_1",
        session_id="sess_1",
        intervention_type=InterventionType.HINT,
        status=InterventionStatus.SUGGESTED,
        content="test",
        intensity=0.5,
    )
    service._interventions["int_test"] = intervention

    result = await service.deliver_intervention("int_test", "sess_1")

    assert result["delivered"] is True
    assert service._interventions["int_test"].status == InterventionStatus.DELIVERED


@pytest.mark.asyncio
async def test_record_outcome_accepted():
    """record_intervention_outcome updates status."""
    service = InterventionService()

    intervention = Intervention(
        id="int_test",
        student_id="student_1",
        session_id="sess_1",
        intervention_type=InterventionType.HINT,
        status=InterventionStatus.DELIVERED,
        content="test",
        intensity=0.5,
    )
    service._interventions["int_test"] = intervention

    await service.record_intervention_outcome("int_test", "accepted")

    assert service._interventions["int_test"].status == InterventionStatus.ACCEPTED
