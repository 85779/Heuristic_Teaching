"""
Event system for module communication.

This package provides:
- Event bus for publish/subscribe messaging
- Event type definitions
- Event persistence and replay
"""

from .event_bus import EventBus, Event
from .event_types import EventType
from .event_store import EventStore

__all__ = ['EventBus', 'EventType', 'Event', 'EventStore']