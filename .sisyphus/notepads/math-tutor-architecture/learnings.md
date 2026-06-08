# Learnings - Math Tutor Architecture Implementation

## Core Layer Interface Definitions (2026-03-22)

### Files Created

1. `backend/app/core/__init__.py` - Core package initialization
2. `backend/app/core/interfaces/__init__.py` - Interfaces package initialization
3. `backend/app/core/interfaces/module.py` - IModule abstract base class
4. `backend/app/core/interfaces/pipeline.py` - IPipeline abstract base class
5. `backend/app/core/interfaces/repository.py` - IRepository abstract base class
6. `backend/app/core/interfaces/llm_client.py` - ILLMClient abstract base class
7. `backend/app/core/context.py` - ModuleContext dataclass

### Key Design Decisions

1. **Using `raise NotImplementedError`**: All abstract methods use this pattern to enforce implementation by subclasses while providing clear error messages.

2. **Type Hints**: Comprehensive use of Python type hints throughout:
   - Return types (`-> str`, `-> list[str]`, etc.)
   - Parameter types (`module_id: str`)
   - Optional types with `| None` syntax (Python 3.10+)
   - `TYPE_CHECKING` for forward references to avoid circular imports

3. **Async Support**: All methods that may involve I/O (database, LLM calls) are defined as `async` to support non-blocking operations.

4. **Generic Repository**: Using `Generic[T]` for `IRepository` allows type-safe implementations for different model types.

5. **ModuleContext Design**: Used `dataclass` for clean attribute definition with proper type annotations. Helper methods `get_module()`, `publish_event()`, and `get_config()` provide convenient access patterns.

6. **Interface-First Approach**: All core capabilities are defined as interfaces first, following the Dependency Inversion Principle. Concrete implementations can be created in the `infrastructure/` layer.

### Python Patterns Used

1. **ABC with `@abstractmethod`**: Standard Python pattern for defining abstract base classes.
2. **Optional Methods**: Some properties (`dependencies`, `provides_events`, `subscribes_events`) return default values, making them optional for modules to override.
3. **Forward References**: Used `TYPE_CHECKING` and string quotes (`"ModuleContext"`) to handle circular dependencies between modules and context.
4. **TypeVar**: Used `T = TypeVar("T")` in `IRepository` for generic type parameter.

### File Organization

```
backend/app/core/
├── __init__.py              # Exports ModuleContext
├── context.py               # ModuleContext dataclass
└── interfaces/
    ├── __init__.py          # Exports all interfaces
    ├── module.py            # IModule
    ├── pipeline.py          # IPipeline
    ├── repository.py        # IRepository
    └── llm_client.py        # ILLMClient
```

### What's Next

These interfaces provide the foundation for:

- Module implementations in `modules/` directory
- Core component implementations in `core/registry/`, `core/orchestrator/`, etc.
- Infrastructure implementations in `infrastructure/` directory

### Clean Code Observations

- All interfaces follow consistent docstring format with Args/Returns sections
- Clear separation between required abstract methods and optional overrideable methods
- Proper use of `raise NotImplementedError` vs `pass` for placeholders
- No third-party dependencies in interface definitions (only `typing`, `abc`, `dataclasses`)
