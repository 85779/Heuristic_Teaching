"""
State Manager for managing session and module state.

The StateManager is responsible for:
- Session state management
- Module state isolation
- State snapshots and recovery
- State change notifications
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionState:
    """Represents the complete state for a session."""

    def __init__(self, session_id: str):
        """
        Initialize session state.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.global_state: Dict[str, Any] = {}
        self.module_states: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_global_state(self) -> Dict[str, Any]:
        """Return copy of global_state."""
        return dict(self.global_state)

    def set_global_state(self, state: Dict[str, Any]) -> None:
        """Replace global_state, record history."""
        self.history.append({"type": "global", "before": dict(self.global_state), "timestamp": datetime.utcnow()})
        self.global_state = dict(state)
        self.updated_at = datetime.utcnow()

    def get_module_state(self, module_id: str) -> Dict[str, Any]:
        """Return module-specific state."""
        return dict(self.module_states.get(module_id, {}))

    def set_module_state(self, module_id: str, state: Dict[str, Any]) -> None:
        """Set module state, record history."""
        self.history.append({
            "type": "module",
            "module_id": module_id,
            "before": dict(self.module_states.get(module_id, {})),
            "timestamp": datetime.utcnow()
        })
        self.module_states[module_id] = dict(state)
        self.updated_at = datetime.utcnow()

    def checkpoint(self, checkpoint_id: str) -> None:
        """Save snapshot of current state."""
        self.checkpoints[checkpoint_id] = {
            "global_state": dict(self.global_state),
            "module_states": {k: dict(v) for k, v in self.module_states.items()},
            "timestamp": datetime.utcnow()
        }

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """Restore from checkpoint."""
        if checkpoint_id not in self.checkpoints:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")
        cp = self.checkpoints[checkpoint_id]
        self.global_state = dict(cp["global_state"])
        self.module_states = {k: dict(v) for k, v in cp["module_states"].items()}
        self.updated_at = datetime.utcnow()

    def list_checkpoints(self) -> List[str]:
        """Return sorted list of checkpoint IDs."""
        return sorted(self.checkpoints.keys())


class StateManager:
    """
    Central manager for all session and module state.

    Responsibilities:
    - Create and manage session states
    - Isolate module states within sessions
    - Support state snapshots and recovery
    - Track state change history
    """

    def __init__(self):
        """Initialize the state manager."""
        self._sessions: Dict[str, SessionState] = {}
        self.logger = logging.getLogger(__name__)

    def create_session(self, session_id: str) -> SessionState:
        """Create new session state."""
        state = SessionState(session_id)
        self._sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_global_state(self, session_id: str) -> Dict[str, Any]:
        sess = self.get_session(session_id)
        if sess is None:
            return {}
        return sess.get_global_state()

    def get_module_state(self, session_id: str, module_id: str) -> Dict[str, Any]:
        sess = self.get_session(session_id)
        if sess is None:
            return {}
        return sess.get_module_state(module_id)

    def set_module_state(self, session_id: str, module_id: str, state: Dict[str, Any]) -> None:
        sess = self.get_session(session_id)
        if sess is None:
            sess = self.create_session(session_id)
        sess.set_module_state(module_id, state)

    def list_sessions(self) -> List[str]:
        return sorted(self._sessions.keys())

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Remove sessions older than max_age_hours. Returns count deleted."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_delete = [sid for sid, s in self._sessions.items() if s.created_at < cutoff]
        for sid in to_delete:
            del self._sessions[sid]
        return len(to_delete)