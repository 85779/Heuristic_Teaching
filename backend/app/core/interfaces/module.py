"""Module interface - Base class for all modules."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from ..context import ModuleContext


class IModule(ABC):
    """Module base interface.

    All business modules must implement this interface to be registered
    and managed by the ModuleRegistry.
    """

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Unique module identifier.

        Returns:
            str: Unique module ID (e.g., "solving", "intervention")
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Module display name.

        Returns:
            str: Human-readable module name (e.g., "Solving Module")
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        """Module version.

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        raise NotImplementedError

    @property
    def dependencies(self) -> list[str]:
        """List of module IDs this module depends on.

        Returns:
            list[str]: List of dependency module IDs
        """
        return []

    @property
    def provides_events(self) -> list[str]:
        """List of event types this module publishes.

        Returns:
            list[str]: List of event type names
        """
        return []

    @property
    def subscribes_events(self) -> list[str]:
        """List of event types this module subscribes to.

        Returns:
            list[str]: List of event type names
        """
        return []

    @abstractmethod
    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the module.

        Called during application startup after dependency resolution.

        Args:
            context: Module execution context providing core capabilities
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the module gracefully.

        Called during application shutdown.

        Returns:
            None
        """
        raise NotImplementedError

    def register_routes(self, router: "APIRouter") -> None:
        """Register API routes for this module.

        Called during router setup. Modules may override this to add routes.

        Args:
            router: FastAPI APIRouter to register routes with
        """
        pass