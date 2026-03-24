"""Pytest fixtures for core infrastructure tests."""
import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Stub motor before imports
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object


@pytest.fixture
def dependency_resolver():
    """Fresh DependencyResolver instance."""
    from app.core.registry.dependency_resolver import DependencyResolver
    return DependencyResolver()


@pytest.fixture
def event_bus():
    """Fresh EventBus instance."""
    from app.core.events.event_bus import EventBus
    return EventBus()


@pytest.fixture
async def event_store():
    """Fresh EventStore instance (async fixture)."""
    from app.core.events.event_store import EventStore
    return EventStore()


@pytest.fixture
def state_manager():
    """Fresh StateManager instance."""
    from app.core.state.state_manager import StateManager
    return StateManager()


@pytest.fixture
def session_manager():
    """Fresh SessionManager instance."""
    from app.core.state.session_manager import SessionManager
    return SessionManager()


@pytest.fixture
def module_registry(event_bus):
    """Fresh ModuleRegistry instance."""
    from app.core.registry.module_registry import ModuleRegistry
    return ModuleRegistry(event_bus)
