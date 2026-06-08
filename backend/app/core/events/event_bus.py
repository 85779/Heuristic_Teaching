"""
Event Bus for decoupled module communication.

The EventBus is responsible for:
- Module-to-module communication via events
- Event publishing and subscription
- Event filtering and routing
"""

from typing import Callable, Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime

from app.core.events.event_types import EventType

logger = logging.getLogger(__name__)


class Event:
    """Represents an event in the system."""

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        source_module: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize an event.

        Args:
            event_type: Type identifier for the event
            data: Event payload data
            session_id: Associated session ID (optional)
            source_module: Module that published the event
            timestamp: Event timestamp (defaults to now)
        """
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
        self.source_module = source_module
        self.timestamp = timestamp or datetime.utcnow()
        self.event_id = f"{self.timestamp.timestamp()}_{event_type}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dict."""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "session_id": self.session_id,
            "source_module": self.source_module,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_id": self.event_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Reconstruct event from dict."""
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            event_type=data["event_type"],
            data=data.get("data", {}),
            session_id=data.get("session_id"),
            source_module=data.get("source_module"),
            timestamp=timestamp,
        )


class EventBus:
    """
    Central event bus for module communication.

    Responsibilities:
    - Event publishing to subscribers
    - Event subscription management
    - Event filtering and routing
    - Async event handling
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable) -> None:
        """Subscribe to all events."""
        self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
        self._wildcard_subscribers = [
            h for h in self._wildcard_subscribers if h != handler
        ]

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                asyncio.create_task(handler(event))
            else:
                asyncio.get_event_loop().run_in_executor(None, handler, event)
        for handler in self._wildcard_subscribers:
            if asyncio.iscoroutinefunction(handler):
                asyncio.create_task(handler(event))
            else:
                asyncio.get_event_loop().run_in_executor(None, handler, event)

    async def publish_batch(self, events: List[Event]) -> None:
        """Publish multiple events in batch."""
        for event in events:
            await self.publish(event)

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))

    def list_event_types(self) -> List[str]:
        """List all event types with subscribers."""
        return sorted(self._subscribers.keys())

    def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """Clear subscribers for an event type or all events."""
        if event_type is None:
            self._subscribers.clear()
            self._wildcard_subscribers.clear()
        elif event_type in self._subscribers:
            del self._subscribers[event_type]