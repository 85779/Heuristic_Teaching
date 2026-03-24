"""Tests for StateManager and SessionState."""
import pytest
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.state.state_manager import StateManager, SessionState


class TestSessionState:
    def test_get_global_state_empty(self):
        state = SessionState('s1')
        assert state.get_global_state() == {}

    def test_set_global_state(self):
        state = SessionState('s1')
        state.set_global_state({'key': 'value'})
        assert state.get_global_state() == {'key': 'value'}

    def test_get_module_state_empty(self):
        state = SessionState('s1')
        assert state.get_module_state('modA') == {}

    def test_set_module_state(self):
        state = SessionState('s1')
        state.set_module_state('modA', {'score': 10})
        assert state.get_module_state('modA') == {'score': 10}

    def test_module_state_isolation(self):
        state = SessionState('s1')
        state.set_module_state('modA', {'a': 1})
        state.set_module_state('modB', {'b': 2})
        assert state.get_module_state('modA') == {'a': 1}
        assert state.get_module_state('modB') == {'b': 2}

    def test_checkpoint_save_restore(self):
        state = SessionState('s1')
        state.set_global_state({'count': 1})
        state.checkpoint('snap1')
        state.set_global_state({'count': 999})
        state.restore_checkpoint('snap1')
        assert state.get_global_state() == {'count': 1}

    def test_restore_checkpoint_unknown_raises(self):
        state = SessionState('s1')
        with pytest.raises(KeyError):
            state.restore_checkpoint('nonexistent')

    def test_list_checkpoints(self):
        state = SessionState('s1')
        state.checkpoint('a')
        state.checkpoint('b')
        cps = state.list_checkpoints()
        assert 'a' in cps
        assert 'b' in cps

    def test_updated_at_changes(self):
        state = SessionState('s1')
        old = state.updated_at
        state.set_global_state({'x': 1})
        assert state.updated_at >= old


class TestStateManager:
    def test_instantiate(self):
        sm = StateManager()
        assert sm is not None

    def test_create_session(self):
        sm = StateManager()
        sess = sm.create_session('s1')
        assert sess.session_id == 's1'
        assert 's1' in sm.list_sessions()

    def test_get_session(self):
        sm = StateManager()
        sm.create_session('s1')
        sess = sm.get_session('s1')
        assert sess is not None
        assert sess.session_id == 's1'

    def test_get_session_missing(self):
        sm = StateManager()
        assert sm.get_session('nonexistent') is None

    def test_delete_session(self):
        sm = StateManager()
        sm.create_session('s1')
        sm.delete_session('s1')
        assert sm.get_session('s1') is None

    def test_set_and_get_module_state(self):
        sm = StateManager()
        sm.create_session('s1')
        sm.set_module_state('s1', 'modA', {'score': 42})
        result = sm.get_module_state('s1', 'modA')
        assert result == {'score': 42}

    def test_get_global_state(self):
        sm = StateManager()
        sess = sm.create_session('s1')
        sess.set_global_state({'g': 1})
        result = sm.get_global_state('s1')
        assert result == {'g': 1}

    def test_cleanup_old_sessions(self):
        sm = StateManager()
        sess = sm.create_session('s1')
        sess.created_at = datetime.utcnow() - timedelta(hours=48)
        count = sm.cleanup_old_sessions(max_age_hours=24)
        assert count >= 1
        assert sm.get_session('s1') is None
