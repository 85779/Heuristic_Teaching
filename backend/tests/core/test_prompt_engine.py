"""Tests for PromptEngine."""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.orchestrator.prompt_engine import PromptEngine


class TestPromptEngine:
    def test_instantiate(self):
        pe = PromptEngine()
        assert pe is not None

    def test_register_and_get_template(self):
        pe = PromptEngine()
        pe.register_template('t1', 'Hello')
        assert pe.get_template('t1') == 'Hello'

    def test_get_template_missing(self):
        pe = PromptEngine()
        assert pe.get_template('nonexistent') is None

    def test_render_template_dollar(self):
        pe = PromptEngine()
        pe.register_template('greet', 'Hello ${name}!')
        result = pe.render_template('greet', {'name': 'Alice'})
        assert result == 'Hello Alice!'

    def test_render_template_double_brace(self):
        pe = PromptEngine()
        pe.register_template('greet', 'Hello {{name}}!')
        result = pe.render_template('greet', {'name': 'Bob'})
        assert result == 'Hello Bob!'

    def test_render_template_multiple_vars(self):
        pe = PromptEngine()
        pe.register_template('full', '${greeting} ${name}!')
        result = pe.render_template('full', {'greeting': 'Hi', 'name': 'Cat'})
        assert result == 'Hi Cat!'

    def test_render_template_missing_var_leaves_placeholder(self):
        pe = PromptEngine()
        pe.register_template('t', 'Hello ${name}')
        result = pe.render_template('t', {})
        assert result == 'Hello ${name}'

    def test_list_templates(self):
        pe = PromptEngine()
        pe.register_template('a', 'A')
        pe.register_template('b', 'B')
        templates = pe.list_templates()
        assert 'a' in templates
        assert 'b' in templates
        assert len(templates) == 2

    def test_validate_template_present(self):
        pe = PromptEngine()
        pe.register_template('t', '${a} ${b}')
        assert pe.validate_template('t', {'a': '1', 'b': '2'}) == True

    def test_validate_template_missing(self):
        pe = PromptEngine()
        pe.register_template('t', '${a} ${b}')
        assert pe.validate_template('t', {'a': '1'}) == False
