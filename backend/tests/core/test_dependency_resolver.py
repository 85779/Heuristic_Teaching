"""Tests for DependencyResolver."""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.registry.dependency_resolver import DependencyResolver, CircularDependencyError


class TestDependencyResolver:
    def test_instantiate(self):
        dr = DependencyResolver()
        assert dr is not None

    def test_add_module_single(self):
        dr = DependencyResolver()
        dr.add_module('A', [])
        assert 'A' in dr._dependency_graph
        assert dr._dependency_graph['A'] == []

    def test_add_module_with_deps(self):
        dr = DependencyResolver()
        dr.add_module('B', ['A'])
        assert dr._dependency_graph['B'] == ['A']

    def test_resolve_order_linear(self):
        dr = DependencyResolver()
        dr.add_module('A', [])
        dr.add_module('B', ['A'])
        dr.add_module('C', ['B'])
        order = dr.resolve_order()
        assert order == ['A', 'B', 'C']

    def test_resolve_order_diamond(self):
        dr = DependencyResolver()
        dr.add_module('D', ['B', 'C'])
        dr.add_module('B', ['A'])
        dr.add_module('C', ['A'])
        dr.add_module('A', [])
        order = dr.resolve_order()
        assert order.index('A') < order.index('B')
        assert order.index('A') < order.index('C')
        assert order.index('B') < order.index('D')
        assert order.index('C') < order.index('D')

    def test_resolve_order_circular_raises(self):
        dr = DependencyResolver()
        dr.add_module('A', ['B'])
        dr.add_module('B', ['A'])
        with pytest.raises(CircularDependencyError):
            dr.resolve_order()

    def test_detect_circular_dependencies(self):
        dr = DependencyResolver()
        dr.add_module('A', ['B'])
        dr.add_module('B', ['A'])
        cycles = dr.detect_circular_dependencies()
        assert len(cycles) >= 1

    def test_detect_no_cycles(self):
        dr = DependencyResolver()
        dr.add_module('A', [])
        dr.add_module('B', ['A'])
        cycles = dr.detect_circular_dependencies()
        assert len(cycles) == 0

    def test_validate_dependencies_all_present(self):
        dr = DependencyResolver()
        dr.add_module('A', ['B', 'C'])
        dr.add_module('B', [])
        dr.add_module('C', [])
        result = dr.validate_dependencies({'A', 'B', 'C'})
        assert result['A'] == True
        assert result['B'] == True
        assert result['C'] == True

    def test_validate_dependencies_missing(self):
        dr = DependencyResolver()
        dr.add_module('A', ['B'])
        dr.add_module('B', [])
        # Only B is available, A is missing - but A's dep on B is satisfied
        result = dr.validate_dependencies({'B'})
        assert result['A'] == True  # A's dependency B is available
        assert result['B'] == True

    def test_validate_dependencies_unsatisfied(self):
        dr = DependencyResolver()
        dr.add_module('A', ['B'])
        dr.add_module('B', [])
        # Nothing available - A's dependency on B is NOT satisfied
        result = dr.validate_dependencies(set())
        assert result['A'] == False  # A needs B but B is not available
        assert result['B'] == True   # B has no dependencies

    def test_get_initialization_order_alias(self):
        dr = DependencyResolver()
        dr.add_module('A', [])
        dr.add_module('B', ['A'])
        assert dr.get_initialization_order() == dr.resolve_order()
