"""Tests for LLMOrchestrator."""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.orchestrator.llm_orchestrator import LLMOrchestrator


class MockLLMClient:
    async def chat(self, messages, model, max_tokens, temperature):
        return "Mock response"


class TestLLMOrchestrator:
    def test_instantiate(self):
        orch = LLMOrchestrator()
        assert orch._prompt_engine is not None
        assert orch._output_parser is not None

    def test_register_template(self):
        orch = LLMOrchestrator()
        orch.register_template('test', 'Hello ${who}')
        assert orch._prompt_engine.get_template('test') == 'Hello ${who}'

    def test_render_template_delegates(self):
        orch = LLMOrchestrator()
        orch.register_template('test', 'Hello ${who}')
        result = orch.render_template('test', {'who': 'World'})
        assert result == 'Hello World'

    def test_list_templates(self):
        orch = LLMOrchestrator()
        orch.register_template('a', 'A')
        orch.register_template('b', 'B')
        templates = orch.list_templates()
        assert 'a' in templates
        assert 'b' in templates

    def test_parse_output_json(self):
        orch = LLMOrchestrator()
        result = orch.parse_output('{"key": "val"}', None)
        assert result == {'key': 'val'}

    @pytest.mark.asyncio
    async def test_call_llm_requires_client(self):
        orch = LLMOrchestrator()
        with pytest.raises(RuntimeError, match='LLM client not set'):
            await orch.call_llm('hello')

    @pytest.mark.asyncio
    async def test_call_llm_with_mock_client(self):
        orch = LLMOrchestrator()
        orch.set_llm_client(MockLLMClient())
        result = await orch.call_llm('hello')
        assert result['content'] == 'Mock response'
        assert result['model'] == 'gpt-4'
