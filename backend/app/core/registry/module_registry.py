"""
Module Registry for module discovery, registration, and lifecycle management.

The ModuleRegistry is responsible for:
- Module discovery and registration
- Dependency relationship resolution
- Lifecycle management (initialize/shutdown)
- Module access control
"""

from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class IModule(ABC):
    """Base interface for all modules."""

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Unique module identifier."""
        pass

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Module display name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Module version."""
        pass

    @property
    def dependencies(self) -> List[str]:
        """List of module IDs this module depends on."""
        return []

    @property
    def provides_events(self) -> List[str]:
        """List of event types this module publishes."""
        return []

    @property
    def subscribes_events(self) -> List[str]:
        """List of event types this module subscribes to."""
        return []

    @abstractmethod
    async def initialize(self, context: 'ModuleContext') -> None:
        """Initialize the module with provided context."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the module and cleanup resources."""
        pass

    def register_routes(self, router) -> None:
        """Register API routes for this module (optional)."""
        pass


class ModuleContext:
    """Context provided to modules during initialization."""

    def __init__(
        self,
        registry: 'ModuleRegistry',
        orchestrator: 'LLMOrchestrator',
        state_manager: 'StateManager',
        event_bus: 'EventBus',
        config: dict,
        session_manager: 'SessionManager',
        repository,
        logger: logging.Logger
    ):
        self.registry = registry
        self.orchestrator = orchestrator
        self.state_manager = state_manager
        self.event_bus = event_bus
        self.config = config
        self.session_manager = session_manager
        self.repository = repository
        self.logger = logger


class ModuleRegistry:
    """
    Central registry for all modules in the system.

    Responsibilities:
    - Module discovery and registration
    - Dependency relationship resolution
    - Lifecycle management (initialize/shutdown in dependency order)
    - Module access and lookup
    """

    def __init__(self):
        """Initialize the module registry."""
        self._modules: Dict[str, IModule] = {}
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def register_module(self, module: IModule) -> None:
        """
        Register a module in the registry.

        Args:
            module: Module instance to register

        Raises:
            ValueError: If module with same ID already exists
        """
        raise NotImplementedError("Module registration not implemented")

    def get_module(self, module_id: str) -> Optional[IModule]:
        """
        Get a module by its ID.

        Args:
            module_id: Unique module identifier

        Returns:
            Module instance if found, None otherwise
        """
        raise NotImplementedError("Module lookup not implemented")

    def get_modules_by_capability(self, capability: str) -> List[IModule]:
        """
        Get modules that provide a specific capability.

        Args:
            capability: Capability name to filter by

        Returns:
            List of modules providing the capability
        """
        raise NotImplementedError("Capability lookup not implemented")

    def get_dependencies(self, module_id: str) -> List[str]:
        """
        Get the dependency list for a module.

        Args:
            module_id: Module identifier

        Returns:
            List of module IDs that this module depends on
        """
        raise NotImplementedError("Dependency lookup not implemented")

    async def initialize_all(self, context: ModuleContext) -> None:
        """
        Initialize all registered modules in dependency order.

        Args:
            context: Module context to pass to all modules
        """
        raise NotImplementedError("Module initialization not implemented")

    async def shutdown_all(self) -> None:
        """Shutdown all modules in reverse dependency order."""
        raise NotImplementedError("Module shutdown not implemented")

    def list_modules(self) -> List[str]:
        """
        List all registered module IDs.

        Returns:
            List of module identifiers
        """
        raise NotImplementedError("Module listing not implemented")