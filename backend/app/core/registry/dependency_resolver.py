"""
Dependency resolver for managing module dependency relationships.

The DependencyResolver handles:
- Topological sorting of modules based on dependencies
- Circular dependency detection
- Initialization order calculation
"""

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected in module graph."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


class DependencyResolver:
    """
    Resolves and manages module dependency relationships.

    Responsibilities:
    - Parse and validate dependency graphs
    - Detect circular dependencies
    - Calculate proper initialization order
    """

    def __init__(self):
        """Initialize the dependency resolver."""
        self._dependency_graph: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)

    def add_module(self, module_id: str, dependencies: List[str]) -> None:
        """
        Add a module and its dependencies to the graph.

        Args:
            module_id: Unique module identifier
            dependencies: List of module IDs this module depends on

        Raises:
            ValueError: If module already exists
        """
        self._dependency_graph[module_id] = dependencies

    def resolve_order(self) -> List[str]:
        """
        Resolve the proper initialization order using topological sort.

        Returns:
            List of module IDs in initialization order

        Raises:
            ValueError: If circular dependency detected
        """
        # in_degree[module] = number of dependencies this module has
        in_degree: Dict[str, int] = {
            m: len(deps) for m, deps in self._dependency_graph.items()
        }

        # Start with modules that have no dependencies (in_degree 0)
        queue = [m for m, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            module = queue.pop(0)
            result.append(module)

            # For each module that depends on this one, decrement its in_degree
            for other_module, deps in self._dependency_graph.items():
                if module in deps:
                    in_degree[other_module] -= 1
                    if in_degree[other_module] == 0:
                        queue.append(other_module)

        # If we couldn't process all modules, there's a cycle
        if len(result) != len(self._dependency_graph):
            cycles = self.detect_circular_dependencies()
            if cycles:
                raise CircularDependencyError(cycles[0])
            raise CircularDependencyError(["Unknown cycle"])

        return result

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph using DFS.

        Returns:
            List of circular dependency chains found
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(module: str) -> None:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for dep in self._dependency_graph.get(module, []):
                if dep not in visited:
                    dfs(dep)
                elif dep in rec_stack:
                    # Found a cycle - extract it from the path
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(module)

        for module in self._dependency_graph:
            if module not in visited:
                dfs(module)

        return cycles

    def get_initialization_order(self) -> List[str]:
        """
        Get the calculated initialization order.

        Returns:
            List of module IDs in order to initialize
        """
        return self.resolve_order()

    def validate_dependencies(self, available_modules: Set[str]) -> Dict[str, bool]:
        """
        Validate that all dependencies can be satisfied.

        Args:
            available_modules: Set of available module IDs

        Returns:
            Dictionary mapping module IDs to validity status
        """
        result = {}
        for module_id in self._dependency_graph:
            deps = self._dependency_graph[module_id]
            result[module_id] = all(dep in available_modules for dep in deps)
        return result