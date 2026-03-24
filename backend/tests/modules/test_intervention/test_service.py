"""Tests for InterventionService."""
import pytest
from unittest.mock import patch, AsyncMock
from app.modules.intervention.service import InterventionService
from app.modules.intervention.models import InterventionType, InterventionStatus, Intervention


@pytest.mark.asyncio
async def test_generate_returns_intervention():
    """service.generate() returns an Intervention object from SessionState."""
    from unittest.mock import MagicMock, patch
    from app.modules.intervention.locator.models import BreakpointLocation, BreakpointType
    from app.modules.intervention.analyzer.models import BreakpointAnalysis
    from app.modules.intervention.generator.models import GeneratedHint
    from app.core.state.state_manager import StateManager

    # Setup state manager with solving state
    state_manager = StateManager()
    state_manager.set_module_state("sess_1", "solving", {
        "problem": "题目",
        "student_work": "学生作答",
        "student_steps": [{"step_id": "s1", "step_name": "Step 1", "content": "content"}],
        "solution_steps": [
            {"step_id": "s1", "step_name": "Step 1", "content": "content"},
            {"step_id": "s2", "step_name": "Step 2", "content": "next content"},
        ],
    })

    # Create service with mocked context
    mock_context = MagicMock()
    mock_context.state_manager = state_manager
    mock_context.logger = MagicMock()

    # Create service — patches prevent real LLM calls during __init__
    with patch('app.modules.intervention.service.BreakpointLocator') as MockLocator, \
         patch('app.modules.intervention.service.BreakpointAnalyzer') as MockAnalyzer, \
         patch('app.modules.intervention.service.HintGenerator') as MockGenerator:

        service = InterventionService(context=mock_context)

        # Now replace sub-modules with direct mocks (bypass complex patch chain)
        mock_locator = MagicMock()
        mock_locator.locate.return_value = BreakpointLocation(
            breakpoint_position=1,
            breakpoint_type=BreakpointType.MISSING_STEP,
            expected_step_content="next step",
            gap_description="第2步缺失",
            student_last_step="step 1",
        )
        mock_analyzer = AsyncMock(return_value=BreakpointAnalysis(
            required_knowledge=["知识"],
            required_connection="联系",
            possible_approaches=["方法"],
            difficulty_level=0.5,
        ))
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=GeneratedHint(
            content="hint content",
            level="surface",
            approach_used="method",
            original_intensity=0.3,
        ))

        service._locator = mock_locator
        service._analyzer = mock_analyzer
        service._generator = mock_generator

        result = await service.generate(
            session_id="sess_1",
            intensity=0.3,
            student_id="student_1",
        )

        assert result is not None
        assert result.intervention_type == InterventionType.HINT
        assert result.status == InterventionStatus.SUGGESTED
        assert result.content == "hint content"
        assert result.session_id == "sess_1"
        assert result.student_id == "student_1"


@pytest.mark.asyncio
async def test_deliver_intervention():
    """deliver_intervention updates status to DELIVERED."""
    service = InterventionService()
    
    # Manually add an intervention
    from app.modules.intervention.models import Intervention
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
