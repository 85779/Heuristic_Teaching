"""Pytest fixtures for recommendation module tests."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Stub motor before imports
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')

# Stub app.infrastructure.database
stub_db = type(sys)('app.infrastructure.database')
stub_db.MongoDBConnection = type('MongoDBConnection', (), {})
sys.modules['app.infrastructure.database'] = stub_db

stub_db_mongo = type(sys)('app.infrastructure.database.mongodb')
sys.modules['app.infrastructure.database.mongodb'] = stub_db_mongo

# Stub app.infrastructure.llm
stub_llm = type(sys)('app.infrastructure.llm')
sys.modules['app.infrastructure.llm'] = stub_llm

stub_llm_base = type(sys)('app.infrastructure.llm.base_client')

class StubMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    def to_dict(self):
        return {"role": self.role, "content": self.content}

stub_llm_base.BaseLLMClient = type('BaseLLMClient', (), {'Message': StubMessage})
stub_llm_base.Message = StubMessage
sys.modules['app.infrastructure.llm.base_client'] = stub_llm_base

# Stub DashScopeClient with working chat() method
class StubDashScopeClient:
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('model', 'qwen-turbo')

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, response_format=None):
        # Return a mock JSON response for testing
        return '{"problem_text": "计算 $\\\\lim_{x \\\\to 0} \\\\frac{\\\\sin 2x}{x}$", "answer": "2", "solution_hint": "利用重要极限", "difficulty_rating": 2, "related_kps": ["KP_3_01"], "method_used": "等价无穷小替换", "why_recommended": "巩固极限计算", "generation_reasoning": "基于前置知识点生成"}'


stub_dashscope = type(sys)('app.infrastructure.llm.dashscope_client')
stub_dashscope.DashScopeClient = StubDashScopeClient
sys.modules['app.infrastructure.llm.dashscope_client'] = stub_dashscope


@pytest.fixture
def kb_api():
    """Fresh KnowledgeBaseAPI instance with real data."""
    from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI
    return KnowledgeBaseAPI(kb_dir="data/knowledge_ontology")


@pytest.fixture
def anchor_retriever(kb_api):
    """Fresh KnowledgeAnchorRetriever instance."""
    from app.modules.recommendation.retriever.knowledge_anchor_retriever import KnowledgeAnchorRetriever
    return KnowledgeAnchorRetriever(kb_api=kb_api)


@pytest.fixture
def prompt_templates():
    """Fresh ProblemPromptTemplates instance."""
    from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates
    return ProblemPromptTemplates()


@pytest.fixture
def problem_validator():
    """Fresh ProblemValidator instance."""
    from app.modules.recommendation.generator.problem_validator import ProblemValidator
    return ProblemValidator()


@pytest.fixture
def fallback_generator():
    """Fresh FallbackGenerator instance."""
    from app.modules.recommendation.generator.fallback_generator import FallbackGenerator
    return FallbackGenerator()


@pytest.fixture
def difficulty_scorer():
    """Fresh DifficultyScorer instance."""
    from app.modules.recommendation.scorer.difficulty_scorer import DifficultyScorer
    return DifficultyScorer()


@pytest.fixture
def llm_client():
    """Mock DashScopeClient that returns valid JSON."""
    return StubDashScopeClient()


@pytest.fixture
def problem_generator(llm_client, prompt_templates, problem_validator):
    """Fresh ProblemGenerator instance with mocked LLM."""
    from app.modules.recommendation.generator.problem_generator import ProblemGenerator
    return ProblemGenerator(
        llm_client=llm_client,
        prompt_templates=prompt_templates,
        validator=problem_validator,
        model="qwen-turbo",
    )