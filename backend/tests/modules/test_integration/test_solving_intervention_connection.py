"""Integration tests for Solving + Intervention module connection.

Tests the SessionState-based data flow:
1. Solving module stores solution_steps in SessionState
2. Intervention module reads from SessionState to generate hints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.solving.models import TeachingStep, ReferenceSolution
from app.modules.intervention.service import InterventionService


@pytest.fixture
def mock_state_manager():
    """StateManager with pre-populated solving state."""
    from app.core.state.state_manager import StateManager
    from app.core.context import ModuleContext
    
    state_manager = StateManager()
    
    # Pre-populate solving state for session "sess_001"
    solving_state = {
        "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。",
        "student_work": "解：设 a_0 = 1。",
        "student_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求：我们需要构造一个正整数序列，使得每个正整数都恰好出现一次。"}
        ],
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求：我们需要构造一个正整数序列，使得每个正整数都恰好出现一次。"},
            {"step_id": "s2", "step_name": "构造初始", "content": "设 a_0 = 1，则 b_0 = gcd(a_0, a_1)。令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。"},
            {"step_id": "s3", "step_name": "归纳假设", "content": "假设已经覆盖了 1, 2, ..., n 这些正整数一次。"},
            {"step_id": "s4", "step_name": "构造新项", "content": "为了覆盖 n+1，选择 a_{n+1} = (n+1) * p，其中 p 是质数。"},
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
    """InterventionService with mocked LLM and mock state_manager."""
    service = InterventionService(context=mock_state_manager)
    
    # Mock the locator (BreakpointLocator - synchronous call)
    from app.modules.intervention.locator.models import BreakpointLocation, BreakpointType
    mock_locator = MagicMock()
    mock_locator.locate.return_value = BreakpointLocation(
        breakpoint_position=1,
        breakpoint_type=BreakpointType.MISSING_STEP,
        expected_step_content="构造新项",
        gap_description="学生在构造新项时遇到困难",
        student_last_step="理解问题",
    )
    service._locator = mock_locator
    
    # Mock the analyzer (BreakpointAnalyzer - LLM call)
    from app.modules.intervention.analyzer.models import BreakpointAnalysis
    mock_analyzer = AsyncMock()
    mock_analyzer.analyze.return_value = BreakpointAnalysis(
        required_knowledge=["gcd的性质", "归纳法"],
        required_connection="需要理解如何通过选择a_{n+1}来控制gcd的值",
        possible_approaches=["从具体例子观察gcd规律", "构造归纳假设"],
        difficulty_level=0.4,
    )
    service._analyzer = mock_analyzer
    
    # Mock the generator (HintGenerator - LLM call)
    from app.modules.intervention.generator.models import GeneratedHint
    mock_generator = AsyncMock()
    mock_generator.generate.return_value = GeneratedHint(
        content="提示：从 a_0 = 1 出发，尝试选择 a_1 使得 b_0 = gcd(a_0, a_1) = 1",
        level="surface",
        approach_used="构造性思考",
        original_intensity=0.5,
    )
    service._generator = mock_generator
    
    return service


class TestSessionStateConnection:
    """Test SessionState-based connection between Solving and Intervention."""

    @pytest.mark.asyncio
    async def test_generate_reads_from_session_state(self, intervention_service):
        """InterventionService.generate() reads solving state from SessionState."""
        result = await intervention_service.generate(
            session_id="sess_001",
            intensity=0.5,
            student_id="student_001",
        )
        
        # Should return an Intervention
        assert result is not None
        assert result.session_id == "sess_001"
        assert result.student_id == "student_001"
        assert result.intensity == 0.5
        
        # Should have hint content from mock generator
        assert "提示" in result.content

    @pytest.mark.asyncio
    async def test_generate_with_student_work_override(self, intervention_service):
        """student_work parameter overrides SessionState value."""
        result = await intervention_service.generate(
            session_id="sess_001",
            student_work="我设 a_0 = 2...",  # Override
            intensity=0.3,
        )
        
        assert result is not None
        # The analyzer was called with the overridden student_work
        intervention_service._analyzer.analyze.assert_called_once()
        call_kwargs = intervention_service._analyzer.analyze.call_args
        # The student_work passed should be the override
        assert "我设 a_0 = 2..." in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_generate_raises_on_missing_session(self, intervention_service):
        """Raises ValueError if no solving state found for session."""
        with pytest.raises(ValueError, match="No solving state found"):
            await intervention_service.generate(
                session_id="nonexistent_session",
                intensity=0.5,
            )

    @pytest.mark.asyncio
    async def test_generate_calls_locator_first(self, intervention_service):
        """Verify the flow: locator → analyzer → generator."""
        await intervention_service.generate(
            session_id="sess_001",
            intensity=0.5,
        )
        
        # locator was called
        intervention_service._locator.locate.assert_called_once()
        
        # Then analyzer was called
        intervention_service._analyzer.analyze.assert_called_once()
        
        # Then generator was called
        intervention_service._generator.generate.assert_called_once()


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
