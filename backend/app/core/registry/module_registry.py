"""
Module Registry for module discovery, registration, and lifecycle management.

The ModuleRegistry is responsible for:
- Module discovery and registration
- Dependency relationship resolution
- Lifecycle management (initialize/shutdown)
- Module access control
"""

from typing import Dict, List, Optional
import logging

from app.core.interfaces.module import IModule
from app.core.context import ModuleContext
from app.core.registry.dependency_resolver import DependencyResolver

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Central registry for all modules in the system.

    Responsibilities:
    - Module discovery and registration
    - Dependency relationship resolution
    - Lifecycle management (initialize/shutdown in dependency order)
    - Module access and lookup
    """

    def __init__(self, event_bus=None):
        """Initialize the module registry."""
        self._modules: Dict[str, IModule] = {}
        self._initialized = False
        self._event_bus = event_bus
        self._dependency_resolver = DependencyResolver()
        self.logger = logging.getLogger(__name__)

    def register_module(self, module: IModule) -> None:
        """
        Register a module in the registry.

        Args:
            module: Module instance to register

        Raises:
            ValueError: If module with same ID already exists
        """
        self._modules[module.module_id] = module
        self._dependency_resolver.add_module(module.module_id, module.dependencies)
        self.logger.info(f"Registered module: {module.module_id}")

    def get_module(self, module_id: str) -> Optional[IModule]:
        """
        Get a module by its ID.

        Args:
            module_id: Unique module identifier

        Returns:
            Module instance if found, None otherwise
        """
        return self._modules.get(module_id)

    def get_modules_by_capability(self, capability: str) -> List[IModule]:
        """
        Get modules that provide a specific capability.

        Args:
            capability: Capability name to filter by

        Returns:
            List of modules providing the capability
        """
        result = []
        for module in self._modules.values():
            if module.module_id == capability:
                result.append(module)
            elif capability in module.provides_events:
                result.append(module)
        return result

    def get_dependencies(self, module_id: str) -> List[str]:
        """
        Get the dependency list for a module.

        Args:
            module_id: Module identifier

        Returns:
            List of module IDs that this module depends on
        """
        return self._dependency_resolver._dependency_graph.get(module_id, [])

    async def initialize_all(self, context: ModuleContext) -> None:
        """
        Initialize all registered modules in dependency order.

        Args:
            context: Module context to pass to all modules
        """
        order = self._dependency_resolver.resolve_order()
        self.logger.info(f"Initializing modules in order: {order}")
        for module_id in order:
            module = self._modules[module_id]
            await module.initialize(context)
            self.logger.info(f"Initialized module: {module_id}")
        self._initialized = True

    async def shutdown_all(self) -> None:
        """Shutdown all modules in reverse dependency order."""
        if not self._initialized:
            return
        order = self._dependency_resolver.resolve_order()
        reversed_order = list(reversed(order))
        self.logger.info(f"Shutting down modules in order: {reversed_order}")
        for module_id in reversed_order:
            module = self._modules[module_id]
            await module.shutdown()
            self.logger.info(f"Shut down module: {module_id}")
        self._initialized = False

    def list_modules(self) -> List[str]:
        """
        List all registered module IDs.

        Returns:
            List of module identifiers
        """
        return sorted(self._modules.keys())
