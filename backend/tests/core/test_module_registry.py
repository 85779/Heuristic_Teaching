"""Tests for ModuleRegistry."""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus
from app.core.context import ModuleContext


class MockModule:
    def __init__(self, mid, deps=None, events=None):
        self.module_id = mid
        self.module_name = mid
        self.version = '1.0'
        self.dependencies = deps or []
        self.provides_events = events or []
        self.subscribes_events = []
        self.initialized = False
        self.shut_down = False

    async def initialize(self, ctx):
        self.initialized = True

    async def shutdown(self):
        self.shut_down = True


class TestModuleRegistry:
    def test_instantiate(self):
        reg = ModuleRegistry(EventBus())
        assert reg is not None

    def test_register_and_get_module(self):
        reg = ModuleRegistry(EventBus())
        mod = MockModule('mod1')
        reg.register_module(mod)
        retrieved = reg.get_module('mod1')
        assert retrieved is mod

    def test_get_module_missing(self):
        reg = ModuleRegistry(EventBus())
        assert reg.get_module('nonexistent') is None

    def test_list_modules(self):
        reg = ModuleRegistry(EventBus())
        reg.register_module(MockModule('A'))
        reg.register_module(MockModule('B'))
        modules = reg.list_modules()
        assert 'A' in modules
        assert 'B' in modules
        assert len(modules) == 2

    def test_get_dependencies(self):
        reg = ModuleRegistry(EventBus())
        reg.register_module(MockModule('A'))
        reg.register_module(MockModule('B', deps=['A']))
        deps = reg.get_dependencies('B')
        assert 'A' in deps

    def test_get_modules_by_capability(self):
        reg = ModuleRegistry(EventBus())
        mod1 = MockModule('mod1', events=['ev1'])
        mod2 = MockModule('mod2')
        reg.register_module(mod1)
        reg.register_module(mod2)
        result = reg.get_modules_by_capability('ev1')
        assert len(result) == 1
        assert result[0].module_id == 'mod1'

    @pytest.mark.asyncio
    async def test_initialize_all(self):
        reg = ModuleRegistry(EventBus())
        ctx = ModuleContext(registry=reg, orchestrator=None, state_manager=None, event_bus=None, config={}, session_manager=None, repository=None, logger=None)
        mod = MockModule('mod1')
        reg.register_module(mod)
        await reg.initialize_all(ctx)
        assert mod.initialized == True

    @pytest.mark.asyncio
    async def test_initialize_order(self):
        reg = ModuleRegistry(EventBus())
        order = []
        class ModA(MockModule):
            async def initialize(self, ctx):
                order.append('A')
        class ModB(MockModule):
            async def initialize(self, ctx):
                order.append('B')
        reg.register_module(ModB('B', deps=['A']))
        reg.register_module(ModA('A'))
        ctx = ModuleContext(registry=reg, orchestrator=None, state_manager=None, event_bus=None, config={}, session_manager=None, repository=None, logger=None)
        await reg.initialize_all(ctx)
        assert order == ['A', 'B']

    @pytest.mark.asyncio
    async def test_shutdown_all(self):
        reg = ModuleRegistry(EventBus())
        mod = MockModule('mod1')
        reg.register_module(mod)
        ctx = ModuleContext(registry=reg, orchestrator=None, state_manager=None, event_bus=None, config={}, session_manager=None, repository=None, logger=None)
        await reg.initialize_all(ctx)
        await reg.shutdown_all()
        assert mod.shut_down == True
