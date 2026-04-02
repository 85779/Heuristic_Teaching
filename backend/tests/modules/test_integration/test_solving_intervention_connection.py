"""Integration tests for Solving + Intervention module connection (v2).

Tests the SessionState-based data flow:
1. Solving module stores solution_steps in SessionState
2. Intervention module reads from SessionState to generate hints
3. v2 flow: locator → router → decider → generator → guardrail
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.intervention.service import InterventionService


@pytest.fixture
def mock_state_manager():
    """StateManager with pre-populated solving state."""
    from app.core.state.state_manager import StateManager

    state_manager = StateManager()

    # Pre-populate solving state for session "sess_001"
    solving_state = {
        "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。",
        "student_work": "解：设 a_0 = 1。",
        "student_steps": [
            {
                "step_id": "s1",
                "step_name": "理解问题",
                "content": "理解题目要求：我们需要构造一个正整数序列，使得每个正整数都恰好出现一次。",
            }
        ],
        "solution_steps": [
            {
                "step_id": "s1",
                "step_name": "理解问题",
                "content": "理解题目要求：我们需要构造一个正整数序列，使得每个正整数都恰好出现一次。",
            },
            {
                "step_id": "s2",
                "step_name": "构造初始",
                "content": "设 a_0 = 1，则 b_0 = gcd(a_0, a_1)。令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。",
            },
            {
                "step_id": "s3",
                "step_name": "归纳假设",
                "content": "假设已经覆盖了 1, 2, ..., n 这些正整数一次。",
            },
            {
                "step_id": "s4",
                "step_name": "构造新项",
                "content": "为了覆盖 n+1，选择 a_{n+1} = (n+1) * p，其中 p 是质数。",
            },
        ],
    }
    state_manager.set_module_state("sess_001", "solving", solving_state)

    # Create mock context with state_manager
    context = MagicMock()
    context.state_manager = state_manager
    context.logger = MagicMock()

    return context


@pytest.fixture
def intervention_service(mock_state_manager):
    """InterventionService with mocked LLM and mock state_manager (v2)."""
    service = InterventionService(context=mock_state_manager)

    # Mock the locator (BreakpointLocator - synchronous call)
    from app.modules.intervention.locator.models import BreakpointLocation, BreakpointType

    mock_locator = MagicMock()
    mock_locator.locate.return_value = BreakpointLocation(
        breakpoint_position=1,
        breakpoint_type=BreakpointType.MISSING_STEP,
        expected_step_content="构造新项",
        gap_description="学生在构造新项时缺失",
        student_last_step="理解问题",
    )
    service._locator = mock_locator

    # Mock the router (DimensionRouter - LLM call)
    from app.modules.intervention.models import DimensionResult, DimensionEnum

    mock_router = AsyncMock()
    mock_router.route.return_value = DimensionResult(
        dimension=DimensionEnum.RESOURCE,
        confidence=0.9,
        reasoning="Mocked dimension result",
    )
    service._router = mock_router

    # Mock the decider (SubTypeDecider - LLM call)
    from app.modules.intervention.models import (
        SubTypeResult,
        PromptLevelEnum,
        EscalationDecision,
        EscalationAction,
    )

    mock_decider = AsyncMock()
    mock_decider.decide.return_value = SubTypeResult(
        sub_type=PromptLevelEnum.R2,
        reasoning="Mocked sub-type result",
        hint_direction="请学生尝试从具体例子入手",
        escalation_decision=EscalationDecision(
            action=EscalationAction.MAINTAIN,
            from_level="R1",
            to_level="R2",
            reasoning="mock",
        ),
    )
    service._decider = mock_decider

    # Mock the generator (HintGeneratorV2 - LLM call, returns str)
    mock_generator = AsyncMock()
    mock_generator.generate.return_value = "提示：从 a_0 = 1 出发，尝试选择 a_1 使得 b_0 = gcd(a_0, a_1) = 1"
    service._generator = mock_generator

    # Mock the guardrail (OutputGuardrail - sync call)
    from app.modules.intervention.guardrail.guardrail import GuardrailResult

    mock_guardrail = AsyncMock()
    mock_guardrail.check.return_value = GuardrailResult(
        passed=True,
        reason="Mocked guardrail passed",
        violations=[],
    )
    service._guardrail = mock_guardrail

    # Mock context_manager to avoid MongoDB dependency
    mock_cm = MagicMock()
    mock_cm.get_or_create_context.return_value = MagicMock(
        intervention_memory=[],
        current_level=PromptLevelEnum.R1,
        status="active",
    )
    mock_cm.get_turn_count.return_value = 1
    mock_cm.update_breakpoint_location.return_value = None
    mock_cm.update_dimension_result.return_value = None
    mock_cm.update_sub_type_result.return_value = None
    mock_cm.record_intervention.return_value = None
    mock_cm.apply_escalation.return_value = None
    service._context_manager = mock_cm

    return service


class TestSessionStateConnectionV2:
    """Test SessionState-based connection between Solving and Intervention (v2)."""

    @pytest.mark.asyncio
    async def test_create_intervention_reads_from_session_state(
        self, intervention_service
    ):
        """InterventionService.create_intervention() reads solving state from SessionState."""
        from app.modules.intervention.models import InterventionRequest

        request = InterventionRequest(
            student_id="student_001",
            session_id="sess_001",
            student_input="",
            frontend_signal=None,
            intervention_type="hint",
        )
        response = await intervention_service.create_intervention(request)

        assert response.success is True
        assert response.intervention is not None
        assert response.intervention.session_id == "sess_001"
        assert response.intervention.student_id == "student_001"

    @pytest.mark.asyncio
    async def test_create_intervention_calls_locator_first(
        self, intervention_service
    ):
        """Verify v2 flow: locator → router → decider → generator → guardrail."""
        from app.modules.intervention.models import InterventionRequest

        request = InterventionRequest(
            student_id="student_001",
            session_id="sess_001",
            student_input="",
            frontend_signal=None,
            intervention_type="hint",
        )
        await intervention_service.create_intervention(request)

        # locator was called
        intervention_service._locator.locate.assert_called_once()

        # router was called
        intervention_service._router.route.assert_called_once()

        # decider was called
        intervention_service._decider.decide.assert_called_once()

        # generator was called
        intervention_service._generator.generate.assert_called_once()

        # guardrail was called
        intervention_service._guardrail.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_intervention_raises_on_missing_session(
        self, intervention_service
    ):
        """Returns failure response if no solving state found for session."""
        from app.modules.intervention.models import InterventionRequest

        request = InterventionRequest(
            student_id="student_001",
            session_id="nonexistent_session",
            student_input="",
            frontend_signal=None,
            intervention_type="hint",
        )
        response = await intervention_service.create_intervention(request)

        assert response.success is False
        assert "No solving state found" in response.message

    @pytest.mark.asyncio
    async def test_router_passes_correct_params(self, intervention_service):
        """Router receives correct student_input and breakpoint info."""
        from app.modules.intervention.models import InterventionRequest

        request = InterventionRequest(
            student_id="student_001",
            session_id="sess_001",
            student_input="我卡在构造步骤",
            frontend_signal=None,
            intervention_type="hint",
        )
        await intervention_service.create_intervention(request)

        # Router was called with student input
        intervention_service._router.route.assert_called_once()
        call_kwargs = intervention_service._router.route.call_args
        assert "我卡在构造步骤" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_guardrail_receives_hint_content(self, intervention_service):
        """Guardrail receives the generated hint content for safety check."""
        from app.modules.intervention.models import InterventionRequest

        request = InterventionRequest(
            student_id="student_001",
            session_id="sess_001",
            student_input="",
            frontend_signal=None,
            intervention_type="hint",
        )
        await intervention_service.create_intervention(request)

        # Guardrail was called with hint content
        intervention_service._guardrail.check.assert_called_once()
        call_kwargs = intervention_service._guardrail.check.call_args
        # First arg should be the hint string
        call_args = call_kwargs[0] if call_kwargs[0] else ()
        call_kwargs_dict = call_kwargs[1] if len(call_kwargs) > 1 else {}
        all_args = call_args + tuple(call_kwargs_dict.values())
        hint_found = any(
            "a_0" in str(arg) for arg in all_args
        )
        assert hint_found, "Hint content should be passed to guardrail"


class TestStateManagerSolvingStorage:
    """Test that StateManager correctly stores and retrieves solving state."""

    def test_set_and_get_module_state(self):
        """StateManager can store and retrieve solving state."""
        from app.core.state.state_manager import StateManager

        sm = StateManager()
        test_state = {"problem": "test", "solution_steps": []}

        sm.set_module_state("sess_1", "solving", test_state)

        retrieved = sm.get_module_state("sess_1", "solving")
        assert retrieved == test_state

    def test_get_module_state_returns_empty_dict_for_unknown_session(self):
        """Returns empty dict if session doesn't exist."""
        from app.core.state.state_manager import StateManager

        sm = StateManager()
        result = sm.get_module_state("nonexistent", "solving")
        assert result == {}
