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

