"""Tests for HintGenerator."""
import pytest
from app.modules.intervention.generator.generator import HintGenerator
from app.modules.intervention.generator.models import GeneratedHint
from app.modules.intervention.analyzer.models import BreakpointAnalysis


def test_determine_level_surface():
    """Intensity < 0.4 → surface."""
    gen = HintGenerator()
    assert gen._determine_level(0.3) == "surface"
    assert gen._determine_level(0.1) == "surface"


def test_determine_level_middle():
    """0.4 <= intensity < 0.7 → middle."""
    gen = HintGenerator()
    assert gen._determine_level(0.4) == "middle"
    assert gen._determine_level(0.5) == "middle"
    assert gen._determine_level(0.69) == "middle"


def test_determine_level_deep():
    """intensity >= 0.7 → deep."""
    gen = HintGenerator()
    assert gen._determine_level(0.7) == "deep"
    assert gen._determine_level(0.9) == "deep"


@pytest.mark.asyncio
async def test_generate_returns_correct_structure():
    """Generate returns GeneratedHint with correct fields."""
    gen = HintGenerator()
    
    # Mock the LLM client
    from unittest.mock import AsyncMock, MagicMock
    gen._llm_client = MagicMock()
    gen._llm_client.chat = AsyncMock(return_value='{"content": "hint text", "approach_used": "method"}')
    
    analysis = BreakpointAnalysis(
        required_knowledge=["知识A"],
        required_connection="联系",
        possible_approaches=["方法A"],
        difficulty_level=0.5,
    )
    
    result = await gen.generate(analysis, "题目", 0.5)
    
    assert isinstance(result, GeneratedHint)
    assert result.level == "middle"
    assert result.original_intensity == 0.5
