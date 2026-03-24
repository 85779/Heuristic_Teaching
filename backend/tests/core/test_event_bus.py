"""Tests for EventBus."""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.events.event_bus import EventBus, Event


class TestEvent:
    def test_to_dict(self):
        event = Event('test.type', {'key': 'value'}, 'sess1', 'mod1')
        d = event.to_dict()
        assert d['event_type'] == 'test.type'
        assert d['data'] == {'key': 'value'}
        assert d['session_id'] == 'sess1'
        assert d['source_module'] == 'mod1'
        assert 'event_id' in d

    def test_from_dict(self):
        original = Event('test.type', {'key': 'value'}, 'sess1', 'mod1')
        d = original.to_dict()
        restored = Event.from_dict(d)
        assert restored.event_type == original.event_type
        assert restored.data == original.data
        assert restored.session_id == original.session_id


class TestEventBus:
    def test_instantiate(self):
        bus = EventBus()
        assert bus is not None

    def test_subscribe(self):
        bus = EventBus()
        called = []
        def handler(e): called.append(e)
        bus.subscribe('TEST', handler)
        assert bus.get_subscriber_count('TEST') == 1

    def test_subscribe_all(self):
        bus = EventBus()
        called = []
        def handler(e): called.append(e)
        bus.subscribe_all(handler)
        assert len(bus._wildcard_subscribers) == 1

    def test_unsubscribe(self):
        bus = EventBus()
        def handler(e): pass
        bus.subscribe('TEST', handler)
        bus.unsubscribe('TEST', handler)
        assert bus.get_subscriber_count('TEST') == 0

    @pytest.mark.asyncio
    async def test_publish_single_handler(self):
        bus = EventBus()
        received = []
        async def handler(e): received.append(e)
        bus.subscribe('TEST', handler)
        await bus.publish(Event('TEST', {'key': 'val'}, None, None))
        await asyncio.sleep(0)  # let tasks run
        assert len(received) == 1
        assert received[0].event_type == 'TEST'

    @pytest.mark.asyncio
    async def test_publish_wildcard(self):
        bus = EventBus()
        received = []
        async def handler(e): received.append(e)
        bus.subscribe_all(handler)
        await bus.publish(Event('OTHER', {}, None, None))
        await asyncio.sleep(0)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_publish_batch(self):
        bus = EventBus()
        received = []
        async def handler(e): received.append(e)
        bus.subscribe('A', handler)
        bus.subscribe('B', handler)
        await bus.publish_batch([
            Event('A', {}, None, None),
            Event('B', {}, None, None)
        ])
        await asyncio.sleep(0)
        assert len(received) == 2

    def test_get_subscriber_count(self):
        bus = EventBus()
        def h1(e): pass
        def h2(e): pass
        bus.subscribe('T', h1)
        bus.subscribe('T', h2)
        assert bus.get_subscriber_count('T') == 2

    def test_list_event_types(self):
        bus = EventBus()
        bus.subscribe('A', lambda e: None)
        bus.subscribe('B', lambda e: None)
        types = bus.list_event_types()
        assert 'A' in types
        assert 'B' in types

    def test_clear_subscribers_specific(self):
        bus = EventBus()
        bus.subscribe('T', lambda e: None)
        bus.clear_subscribers('T')
        assert bus.get_subscriber_count('T') == 0

    def test_clear_subscribers_all(self):
        bus = EventBus()
        bus.subscribe('T', lambda e: None)
        bus.subscribe_all(lambda e: None)
        bus.clear_subscribers()
        assert len(bus._subscribers) == 0
        assert len(bus._wildcard_subscribers) == 0
