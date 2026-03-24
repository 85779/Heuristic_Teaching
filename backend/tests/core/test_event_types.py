"""Tests for EventType and EventValidator."""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.events.event_types import EventType, EventValidator, EventCategory


class TestEventType:
    def test_is_valid_type_valid(self):
        assert EventType.is_valid_type('solving.started') == True
        assert EventType.is_valid_type('solving.completed') == True
        assert EventType.is_valid_type('solving.step_completed') == True

    def test_is_valid_type_invalid(self):
        assert EventType.is_valid_type('invalid.event') == False
        assert EventType.is_valid_type('foo.bar.baz') == False

    def test_get_category_solving(self):
        cat = EventType.get_category('solving.started')
        assert cat == EventCategory.SOLVING

    def test_get_category_intervention(self):
        cat = EventType.get_category('intervention.breakpoint_detected')
        assert cat == EventCategory.INTERVENTION

    def test_get_category_unknown(self):
        cat = EventType.get_category('unknown.type')
        assert cat is None

    def test_list_by_category(self):
        solving_events = EventType.list_by_category(EventCategory.SOLVING)
        assert len(solving_events) > 0
        assert all('solving.' in e for e in solving_events)

    def test_list_by_category_empty(self):
        # Use a category unlikely to have events
        from app.core.events.event_types import EventCategory
        events = EventType.list_by_category(EventCategory.RECOMMENDATION)
        assert isinstance(events, list)


class TestEventValidator:
    def test_validate_event_valid(self):
        v = EventValidator()
        data = {'problem_id': 'p1', 'session_id': 's1'}
        assert v.validate_event('solving.started', data) == True

    def test_validate_event_missing_required(self):
        v = EventValidator()
        data = {'problem_id': 'p1'}  # missing session_id
        assert v.validate_event('solving.started', data) == False

    def test_validate_event_unknown_type(self):
        v = EventValidator()
        result = v.validate_event('unknown.type', {})
        assert result == False

    def test_get_validation_errors_missing_fields(self):
        v = EventValidator()
        errors = v.get_validation_errors('solving.started', {})
        assert len(errors) > 0
        assert any('session_id' in e or 'problem_id' in e for e in errors)

    def test_get_validation_errors_valid(self):
        v = EventValidator()
        data = {'problem_id': 'p1', 'session_id': 's1'}
        errors = v.get_validation_errors('solving.started', data)
        assert len(errors) == 0

    def test_validate_required_fields(self):
        v = EventValidator()
        errors = v.validate_required_fields({'a': 1, 'b': 2}, ['a', 'b', 'c'])
        assert 'c' in errors
        assert 'a' not in errors
        assert 'b' not in errors

    def test_validate_required_fields_all_present(self):
        v = EventValidator()
        errors = v.validate_required_fields({'a': 1}, ['a'])
        assert len(errors) == 0
