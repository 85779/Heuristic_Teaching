"""Module context - Provides core capabilities to modules."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

    from .interfaces import IRepository


@dataclass
class ModuleContext:
    """Module execution context - Provides access to core capabilities.

    This dataclass is passed to modules during initialization to give
    them access to all core system components.
    """

    registry: Any
    """Module registry for discovering and accessing other modules."""

    orchestrator: Any
    """LLM orchestrator for prompt management and LLM orchestration."""

    state_manager: Any
    """State manager for session and module state management."""

    session_manager: Any
    """Session manager for session lifecycle management."""

    event_bus: Any
    """Event bus for publishing and subscribing to events."""

    config: Any
    """Configuration manager for accessing system and module config."""

    repository: "IRepository[Any]"
    """Repository for data access operations."""

    logger: "Logger"
    """Logger for module-specific logging."""

    def get_module(self, module_id: str):
        """Get a module by ID from the registry.

        Args:
            module_id: ID of the module to retrieve

        Returns:
            Module instance or None if not found
        """
        return self.registry.get_module(module_id)

    def publish_event(
        self,
        event_type: str,
        data: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        """Publish an event to the event bus.

        Args:
            event_type: Type of event to publish
            data: Event payload data
            session_id: Optional session ID for event correlation
        """
        # Will be implemented by EventBus
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)