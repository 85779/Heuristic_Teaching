"""Tests for EventStore."""
import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.events.event_store import EventStore
from app.core.events.event_bus import Event


class TestEventStore:
    @pytest.fixture
    def store(self):
        return EventStore()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, store):
        event = Event('test.a', {'k': 'v'}, 'sess1', 'mod1')
        stored = await store.store_event(event)
        assert stored.event_id is not None
        assert stored.event_type == 'test.a'
        retrieved = await store.get_event(stored.event_id)
        assert retrieved.event_type == 'test.a'

    @pytest.mark.asyncio
    async def test_store_batch(self, store):
        e1 = Event('A', {}, 'sess1', None)
        e2 = Event('B', {}, 'sess1', None)
        stored = await store.store_batch([e1, e2])
        assert len(stored) == 2

    @pytest.mark.asyncio
    async def test_get_events_by_session(self, store):
        e1 = Event('A', {}, 'sess1', None)
        e2 = Event('B', {}, 'sess2', None)
        await store.store_batch([e1, e2])
        results = await store.get_events_by_session('sess1')
        assert len(results) == 1
        assert results[0].event_type == 'A'

    @pytest.mark.asyncio
    async def test_get_events_by_session_time_filter(self, store):
        e1 = Event('A', {}, 'sess1', None)
        await store.store_event(e1)
        old_time = datetime.utcnow() - timedelta(days=1)
        results = await store.get_events_by_session('sess1', start_time=old_time)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, store):
        e1 = Event('T1', {}, 's1', None)
        e2 = Event('T1', {}, 's2', None)
        e3 = Event('T2', {}, 's3', None)
        await store.store_batch([e1, e2, e3])
        results = await store.get_events_by_type('T1')
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_events_by_type_limit(self, store):
        for i in range(5):
            await store.store_event(Event('T', {}, f's{i}', None))
        results = await store.get_events_by_type('T', limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_events_by_module(self, store):
        e1 = Event('A', {}, 'sess1', 'mod1')
        e2 = Event('B', {}, 'sess2', 'mod2')
        await store.store_batch([e1, e2])
        results = await store.get_events_by_module('mod1')
        assert len(results) == 1
        assert results[0].source_module == 'mod1'

    @pytest.mark.asyncio
    async def test_delete_events_by_session(self, store):
        e1 = Event('A', {}, 'sess1', None)
        e2 = Event('B', {}, 'sess1', None)
        await store.store_batch([e1, e2])
        count = await store.delete_events(session_id='sess1')
        assert count == 2
        remaining = await store.get_events_by_session('sess1')
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_delete_events_by_age(self, store):
        e1 = Event('A', {}, 'sess1', None)
        await store.store_event(e1)
        # Use a future cutoff - events created before now will be "older" than this
        future = datetime.utcnow() + timedelta(days=1)
        count = await store.delete_events(older_than=future)
        assert count >= 1

    @pytest.mark.asyncio
    async def test_get_event_stats(self, store):
        await store.store_batch([
            Event('A', {}, 's1', None),
            Event('A', {}, 's2', None),
            Event('B', {}, 's3', None),
        ])
        stats = await store.get_event_stats()
        assert stats['total'] == 3
        assert stats['by_type']['A'] == 2
        assert stats['by_type']['B'] == 1

    @pytest.mark.asyncio
    async def test_replay_session(self, store):
        e1 = Event('A', {}, 'sess_replay', None)
        e2 = Event('B', {}, 'sess_replay', None)
        await store.store_batch([e1, e2])
        replayed = await store.replay_session('sess_replay')
        assert len(replayed) == 2
