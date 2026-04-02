"""Pytest fixtures for integration tests."""
import sys
import os
import pytest

# Set required env vars before any imports
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key-for-integration")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Stub motor
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

# Stub database module
sys.modules['app.infrastructure.database'] = type(sys)('database')
sys.modules['app.infrastructure.database.mongodb'] = type(sys)('mongodb')
sys.modules['app.infrastructure.database.mongodb'].MongoDBConnection = object
sys.modules['app.infrastructure.database.repositories'] = type(sys)('repositories')
sys.modules['app.infrastructure.database.repositories.base_repo'] = type(sys)('base_repo')
sys.modules['app.infrastructure.database.repositories.session_repo'] = type(sys)('session_repo')

# Stub llm module
class _StubMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    def to_dict(self):
        return {"role": self.role, "content": self.content}

class _StubDashScopeClient:
    """Mock DashScopeClient that can be instantiated."""
    def __init__(self, api_key=None, model=None, **kwargs):
        self.api_key = api_key
        self.model = model

    async def chat(self, *args, **kwargs):
        return "mocked response"

    async def health_check(self):
        return True

    async def close(self):
        pass

sys.modules['app.infrastructure.llm'] = type(sys)('llm')
sys.modules['app.infrastructure.llm.base_client'] = type(sys)('base_client')
sys.modules['app.infrastructure.llm.base_client'].BaseLLMClient = object
sys.modules['app.infrastructure.llm.base_client'].Message = _StubMessage
sys.modules['app.infrastructure.llm.openai_client'] = type(sys)('openai_client')
sys.modules['app.infrastructure.llm.anthropic_client'] = type(sys)('anthropic_client')
sys.modules['app.infrastructure.llm.dashscope_client'] = type(sys)('dashscope_client')
sys.modules['app.infrastructure.llm.dashscope_client'].DashScopeClient = _StubDashScopeClient

# Stub cache module
sys.modules['app.infrastructure.cache'] = type(sys)('cache')
sys.modules['app.infrastructure.cache.redis_cache'] = type(sys)('redis_cache')

# Stub logging module
sys.modules['app.infrastructure.logging'] = type(sys)('logging')
sys.modules['app.infrastructure.logging.tracer'] = type(sys)('tracer')
