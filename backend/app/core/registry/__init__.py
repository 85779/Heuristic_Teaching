"""
Core module registry and module management.

This package provides module registration, discovery, and lifecycle management.
"""

from .module_registry import ModuleRegistry
from .dependency_resolver import DependencyResolver

__all__ = ['ModuleRegistry', 'DependencyResolver']