"""
Event Store for event persistence and replay.

The EventStore is responsible for:
- Event persistence to storage
- Event replay and reconstruction
- Event history and querying
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class StoredEvent:
    """Represents a persisted event."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str],
        source_module: Optional[str],
        timestamp: datetime,
        stored_at: datetime
    ):
        """
        Initialize a stored event.

        Args:
            event_id: Unique event identifier
            event_type: Event type
            data: Event payload
            session_id: Associated session ID
            source_module: Module that published
            timestamp: Event timestamp
            stored_at: When event was stored
        """
        self.event_id = event_id
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
        self.source_module = source_module
        self.timestamp = timestamp
        self.stored_at = stored_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize stored event to dict."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "session_id": self.session_id,
            "source_module": self.source_module,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "stored_at": self.stored_at.isoformat() if self.stored_at else None,
        }


class EventStore:
    """
    Persistent storage for events.

    Responsibilities:
    - Store events for later retrieval
    - Query events by various criteria
    - Replay events for state reconstruction
    - Manage event retention
    """

    def __init__(self):
        """Initialize the event store."""
        self._events: Dict[str, StoredEvent] = {}
        self.logger = logging.getLogger(__name__)

    async def store_event(self, event: Any) -> StoredEvent:
        """
        Store a single event, return StoredEvent with generated event_id.

        Args:
            event: Event to store

        Returns:
            StoredEvent instance
        """
        event_id = str(uuid.uuid4())
        stored_at = datetime.utcnow()
        stored = StoredEvent(
            event_id=event_id,
            event_type=event.event_type,
            data=event.data,
            session_id=event.session_id,
            source_module=event.source_module,
            timestamp=event.timestamp,
            stored_at=stored_at,
        )
        self._events[event_id] = stored
        return stored

    async def store_batch(self, events: List[Any]) -> List[StoredEvent]:
        """
        Store multiple events.

        Args:
            events: List of events to store

        Returns:
            List of StoredEvent instances
        """
        return [await self.store_event(e) for e in events]

    async def get_event(self, event_id: str) -> Optional[StoredEvent]:
        """
        Get single event by ID.

        Args:
            event_id: Event identifier

        Returns:
            StoredEvent if found, None otherwise
        """
        return self._events.get(event_id)

    async def get_events_by_session(
        self,
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
    ) -> List[StoredEvent]:
        """
        Filter events by session_id, optional time range and type filter.

        Args:
            session_id: Session identifier
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            event_types: Event type filter (optional)

        Returns:
            List of StoredEvent instances
        """
        results = [e for e in self._events.values() if e.session_id == session_id]
        if start_time:
            results = [e for e in results if e.timestamp and e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp and e.timestamp <= end_time]
        if event_types:
            results = [e for e in results if e.event_type in event_types]
        return sorted(results, key=lambda e: e.timestamp or datetime.min)

    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
    ) -> List[StoredEvent]:
        """
        Get events by type, with limit.

        Args:
            event_type: Event type to query
            limit: Maximum number of events

        Returns:
            List of StoredEvent instances
        """
        results = [e for e in self._events.values() if e.event_type == event_type]
        results = sorted(results, key=lambda e: e.timestamp or datetime.min, reverse=True)
        return results[:limit]

    async def get_events_by_module(
        self,
        module_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[StoredEvent]:
        """
        Get events by source module.

        Args:
            module_id: Module identifier
            start_time: Start time filter (optional)
            end_time: End time filter (optional)

        Returns:
            List of StoredEvent instances
        """
        results = [e for e in self._events.values() if e.source_module == module_id]
        if start_time:
            results = [e for e in results if e.timestamp and e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp and e.timestamp <= end_time]
        return sorted(results, key=lambda e: e.timestamp or datetime.min)

    async def replay_session(
        self,
        session_id: str,
        from_time: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Replay all events for a session.

        Args:
            session_id: Session identifier
            from_time: Start replay from this time (optional)

        Returns:
            List of replayed events
        """
        events = await self.get_events_by_session(session_id, start_time=from_time)
        return [e for e in events]

    async def delete_events(
        self,
        session_id: Optional[str] = None,
        older_than: Optional[datetime] = None,
    ) -> int:
        """
        Delete events by session_id and/or age. Return count deleted.

        Args:
            session_id: Delete events for specific session (optional)
            older_than: Delete events older than this time (optional)

        Returns:
            Number of events deleted
        """
        to_delete = []
        for e in self._events.values():
            if session_id and e.session_id != session_id:
                continue
            if older_than and e.timestamp and e.timestamp > older_than:
                continue
            to_delete.append(e.event_id)
        for eid in to_delete:
            del self._events[eid]
        return len(to_delete)

    async def get_event_stats(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get event statistics.

        Args:
            session_id: Filter by session (optional)
            start_time: Start time filter (optional)
            end_time: End time filter (optional)

        Returns:
            Dictionary with total and by_type
        """
        events = list(self._events.values())
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        if start_time:
            events = [e for e in events if e.timestamp and e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp and e.timestamp <= end_time]
        by_type: Dict[str, int] = {}
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        return {"total": len(events), "by_type": by_type}