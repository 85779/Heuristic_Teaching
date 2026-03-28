"""Pytest fixtures for intervention module tests."""
import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Stub motor before imports
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

# Stub any other problematic imports - create proper module hierarchy
# Stub app.infrastructure.database
stub_db = type(sys)('app.infrastructure.database')
stub_db.MongoDBConnection = type('MongoDBConnection', (), {})
sys.modules['app.infrastructure.database'] = stub_db

stub_db_mongodb = type(sys)('app.infrastructure.database.mongodb')
sys.modules['app.infrastructure.database.mongodb'] = stub_db_mongodb

# Stub app.infrastructure.llm and its submodules
stub_llm = type(sys)('app.infrastructure.llm')

class StubMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    def to_dict(self):
        return {"role": self.role, "content": self.content}

stub_llm.BaseLLMClient = type('BaseLLMClient', (), {'Message': StubMessage})
stub_llm.OpenAIClient = type('OpenAIClient', (), {})
stub_llm.AnthropicClient = type('AnthropicClient', (), {})
stub_llm.DashScopeClient = type('DashScopeClient', (), {})
sys.modules['app.infrastructure.llm'] = stub_llm

stub_llm_base = type(sys)('app.infrastructure.llm.base_client')
stub_llm_base.BaseLLMClient = type('BaseLLMClient', (), {})
stub_llm_base.Message = StubMessage
sys.modules['app.infrastructure.llm.base_client'] = stub_llm_base

# Stub dashscope_client
stub_dashscope = type(sys)('app.infrastructure.llm.dashscope_client')
stub_dashscope.DashScopeClient = type('DashScopeClient', (), {})
sys.modules['app.infrastructure.llm.dashscope_client'] = stub_dashscope

# Stub app.infrastructure.cache
stub_cache = type(sys)('app.infrastructure.cache')
stub_cache.RedisCache = type('RedisCache', (), {})
sys.modules['app.infrastructure.cache'] = stub_cache

# Stub app.infrastructure.logging
stub_logging = type(sys)('app.infrastructure.logging')
stub_logging.Tracer = type('Tracer', (), {})
sys.modules['app.infrastructure.logging'] = stub_logging

# Stub app.infrastructure (top level with all exports)
stub_infra = type(sys)('app.infrastructure')
stub_infra.MongoDBConnection = type('MongoDBConnection', (), {})
stub_infra.BaseLLMClient = type('BaseLLMClient', (), {})
stub_infra.RedisCache = type('RedisCache', (), {})
stub_infra.Tracer = type('Tracer', (), {})
sys.modules['app.infrastructure'] = stub_infra

@pytest.fixture
def breakpoint_locator():
    """Fresh BreakpointLocator instance."""
    from app.modules.intervention.locator.breaker import BreakpointLocator
    return BreakpointLocator()

@pytest.fixture
def mock_breakpoint_analyzer():
    """Mock BreakpointAnalyzer that returns canned analysis."""
    from app.modules.intervention.analyzer.models import BreakpointAnalysis
    from unittest.mock import AsyncMock
    
    analyzer = AsyncMock()
    analyzer.analyze.return_value = BreakpointAnalysis(
        required_knowledge=["知识点A", "知识点B"],
        required_connection="需要建立XX和YY的联系",
        possible_approaches=["方法一", "方法二"],
        difficulty_level=0.6,
    )
    return analyzer

@pytest.fixture
def mock_hint_generator():
    """Mock HintGenerator that returns canned hint."""
    from app.modules.intervention.generator.models import GeneratedHint
    from unittest.mock import AsyncMock
    
    gen = AsyncMock()
    gen.generate.return_value = GeneratedHint(
        content="这是一个测试提示",
        level="middle",
        approach_used="类比法",
        original_intensity=0.5,
    )
    return gen

@pytest.fixture
def intervention_service():
    """Fresh InterventionService instance with mocked sub-modules."""
    from app.modules.intervention.service import InterventionService
    from unittest.mock import patch
    
    # Create service with mocked sub-modules
    with patch('app.modules.intervention.service.BreakpointLocator') as mock_locator, \
         patch('app.modules.intervention.service.BreakpointAnalyzer') as mock_analyzer, \
         patch('app.modules.intervention.service.HintGenerator') as mock_generator:
        
        # Setup mock returns
        from app.modules.intervention.analyzer.models import BreakpointAnalysis
        from app.modules.intervention.generator.models import GeneratedHint
        
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze = AsyncMock(return_value=BreakpointAnalysis(
            required_knowledge=["知识点A"],
            required_connection="联系",
            possible_approaches=["方法"],
            difficulty_level=0.5,
        ))
        
        mock_generator_instance = mock_generator.return_value
        mock_generator_instance.generate = AsyncMock(return_value=GeneratedHint(
            content="提示内容",
            level="surface",
            approach_used="方法",
            original_intensity=0.3,
        ))
        
        service = InterventionService()
        yield service
