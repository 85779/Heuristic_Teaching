"""
Session Manager for managing user sessions and lifecycle.

The SessionManager is responsible for:
- Session creation and lifecycle management
- Session authentication and authorization
- Session persistence
- Session cleanup and expiration
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class Session:
    """Represents a user session."""

    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a session.

        Args:
            session_id: Unique session identifier
            user_id: User identifier (optional)
            metadata: Additional session metadata
        """
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def update_activity(self) -> None:
        """Update last_activity and extend expires_at by 1 hour."""
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)

    def extend(self, hours: int = 1) -> None:
        """
        Extend session expiration.

        Args:
            hours: Number of hours to extend
        """
        self.expires_at = self.expires_at + timedelta(hours=hours)


class SessionManager:
    """
    Manager for user session lifecycle.

    Responsibilities:
    - Create and manage user sessions
    - Handle session authentication
    - Track session activity and expiration
    - Cleanup inactive sessions
    """

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(__name__)

    def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: User identifier (optional)
            metadata: Additional session metadata

        Returns:
            New Session instance
        """
        session_id = str(uuid.uuid4())
        session = Session(session_id, user_id, metadata)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get an existing session.

        Args:
            session_id: Session identifier

        Returns:
            Session if found and active, None otherwise
        """
        return self._sessions.get(session_id)

    def validate_session(self, session_id: str) -> bool:
        """
        Validate that a session is active and not expired.

        Args:
            session_id: Session identifier

        Returns:
            True if session is valid
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False
        return not session.is_expired()

    def end_session(self, session_id: str) -> None:
        """
        End a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

    def update_activity(self, session_id: str) -> None:
        """
        Update session activity timestamp.

        Args:
            session_id: Session identifier
        """
        session = self._sessions.get(session_id)
        if session:
            session.update_activity()

    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """
        List sessions, optionally filtered by user.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of Session objects
        """
        if user_id is None:
            return list(self._sessions.values())
        return [s for s in self._sessions.values() if s.user_id == user_id]

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        to_delete = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in to_delete:
            del self._sessions[sid]
        return len(to_delete)

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of session statistics
        """
        session = self._sessions.get(session_id)
        if session is None:
            return {}
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_expired": session.is_expired()
        }
