"""
State management for session and module state.

This package provides:
- Session state management
- Module state isolation
- State snapshots and recovery
"""

from .state_manager import StateManager
from .session_manager import SessionManager

__all__ = ['StateManager', 'SessionManager']