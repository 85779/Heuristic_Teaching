"""Tests for SessionManager and Session."""
import pytest
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.state.session_manager import SessionManager, Session


class TestSession:
    def test_is_expired_false_fresh(self):
        sess = Session('s1', 'u1', {})
        assert sess.is_expired() == False

    def test_is_expired_true_past(self):
        sess = Session('s1', 'u1', {})
        sess.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert sess.is_expired() == True

    def test_update_activity(self):
        sess = Session('s1', 'u1', {})
        old_expires = sess.expires_at
        old_activity = sess.last_activity
        sess.update_activity()
        assert sess.last_activity >= old_activity
        assert sess.expires_at >= old_expires

    def test_extend(self):
        sess = Session('s1', 'u1', {})
        original_expires = sess.expires_at
        sess.extend(hours=5)
        assert sess.expires_at > original_expires + timedelta(hours=4)


class TestSessionManager:
    def test_instantiate(self):
        sm = SessionManager()
        assert sm is not None

    def test_create_session(self):
        sm = SessionManager()
        sess = sm.create_session('u1', {'role': 'student'})
        assert sess.user_id == 'u1'
        assert sess.metadata == {'role': 'student'}
        assert not sess.is_expired()

    def test_get_session(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        retrieved = sm.get_session(sess.session_id)
        assert retrieved is not None
        assert retrieved.user_id == 'u1'

    def test_get_session_missing(self):
        sm = SessionManager()
        assert sm.get_session('nonexistent') is None

    def test_validate_session_valid(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        assert sm.validate_session(sess.session_id) == True

    def test_validate_session_expired(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        sess.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert sm.validate_session(sess.session_id) == False

    def test_validate_session_missing(self):
        sm = SessionManager()
        assert sm.validate_session('nonexistent') == False

    def test_end_session(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        sm.end_session(sess.session_id)
        assert sm.get_session(sess.session_id) is None

    def test_list_sessions(self):
        sm = SessionManager()
        sm.create_session('u1')
        sm.create_session('u2')
        sessions = sm.list_sessions()
        assert len(sessions) == 2

    def test_list_sessions_by_user(self):
        sm = SessionManager()
        sm.create_session('u1')
        sm.create_session('u2')
        u1_sessions = sm.list_sessions(user_id='u1')
        assert len(u1_sessions) == 1
        assert u1_sessions[0].user_id == 'u1'

    def test_update_activity(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        old = sess.last_activity
        sm.update_activity(sess.session_id)
        assert sess.last_activity >= old

    def test_cleanup_expired_sessions(self):
        sm = SessionManager()
        sess = sm.create_session('u1')
        sess.expires_at = datetime.utcnow() - timedelta(hours=1)
        count = sm.cleanup_expired_sessions()
        assert count >= 1
        assert sm.get_session(sess.session_id) is None

    def test_get_session_stats(self):
        sm = SessionManager()
        sess = sm.create_session('u1', {'role': 'admin'})
        stats = sm.get_session_stats(sess.session_id)
        assert stats['user_id'] == 'u1'
        assert stats['is_expired'] == False
        assert 'session_id' in stats
        assert 'created_at' in stats

    def test_get_session_stats_missing(self):
        sm = SessionManager()
        stats = sm.get_session_stats('nonexistent')
        assert stats == {}
