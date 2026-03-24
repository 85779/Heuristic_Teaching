"""Tests for OutputParser."""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.orchestrator.output_parser import OutputParser


class TestOutputParser:
    def test_parse_json_valid(self):
        op = OutputParser()
        result = op.parse_json('{"key": "value"}')
        assert result == {'key': 'value'}

    def test_parse_json_invalid_raises(self):
        op = OutputParser()
        with pytest.raises(ValueError):
            op.parse_json('not json')

    def test_parse_yaml(self):
        op = OutputParser()
        result = op.parse_yaml('key: value')
        assert result == {'key': 'value'}

    def test_extract_json_blocks(self):
        op = OutputParser()
        md = 'text\n```json\n{"a": 1}\n```\nmore'
        blocks = op.extract_json_blocks(md)
        assert len(blocks) == 1
        assert blocks[0] == '{"a": 1}'

    def test_clean_output(self):
        op = OutputParser()
        result = op.clean_output('  hello  ')
        assert result == 'hello'

    def test_clean_output_removes_headers(self):
        op = OutputParser()
        result = op.clean_output('# Header\n\nSome text')
        assert '#' not in result

    def test_validate_schema_present(self):
        op = OutputParser()
        schema = {'required': ['a', 'b']}
        assert op.validate_schema({'a': 1, 'b': 2}, schema) == True

    def test_validate_schema_missing(self):
        op = OutputParser()
        schema = {'required': ['a', 'b']}
        assert op.validate_schema({'a': 1}, schema) == False

    def test_parse_dispatch_json(self):
        op = OutputParser()
        result = op.parse('{"x": 1}', 'json')
        assert result == {'x': 1}

    def test_parse_dispatch_markdown(self):
        op = OutputParser()
        result = op.parse('# Title\n\nSome text', 'markdown')
        assert 'Title' in str(result) or 'text' in str(result)

    def test_parse_unknown_format_raises(self):
        op = OutputParser()
        with pytest.raises(ValueError):
            op.parse('data', 'unknown_format')
