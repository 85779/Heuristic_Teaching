# Core Infrastructure Build — `app/core/` Stub Implementation

## TL;DR

> **Goal**: Implement all `app/core/` stubs that currently raise `NotImplementedError`, turning 10 stub files into fully functional core components.
>
> **Deliverables**:
> - `DependencyResolver` with topological sort + cycle detection
> - `ModuleRegistry` with module lifecycle management
> - `EventBus` + `Event` + `EventType` + `EventValidator` + `EventStore` — full pub/sub system
> - `StateManager` + `SessionState` — session state management
> - `SessionManager` + `Session` — user session lifecycle
> - `LLMOrchestrator` with `PromptEngine` + `OutputParser` — LLM orchestration
>
> **Estimated Effort**: Large (62 methods across 14 classes)
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: Wave 1 foundations → Wave 2 state → Wave 3 orchestrator → Final verification

- [x] T5. **Implement EventStore (in-memory)**

  EventStore fully implemented with in-memory dict storage (all 9 async methods). Verified via QA scenarios.

---


---

- [x] T13. **Write unit tests for all core components**

  **What to do**:
  - Write comprehensive unit tests for each core component in `tests/core/`:
    - `test_dependency_resolver.py`: Test topological sort, cycle detection, validation
    - `test_event_bus.py`: Test subscribe, publish, unsubscribe, wildcard, batch
    - `test_event_types.py`: Test get_category, is_valid_type, validate_event
    - `test_event_store.py`: Test store, retrieve, filter, delete, stats
    - `test_state_manager.py`: Test session state, checkpoints, cleanup
    - `test_session_manager.py`: Test session lifecycle, expiry, validation
    - `test_module_registry.py`: Test register, get, initialize/shutdown order
    - `test_prompt_engine.py`: Test register, render, validate, missing variables
    - `test_output_parser.py`: Test JSON/YAML/markdown parsing, schema validation
    - `test_llm_orchestrator.py`: Test template delegation, parse delegation (skip live LLM calls)
  - Follow existing test patterns from `tests/modules/test_solving/test_solving.py`
  - Use `pytest.mark.asyncio` for async tests
  - Stub motor via `sys.modules` (already done in conftest.py T6)
  - Mock LLM client for orchestrator tests

  **Must NOT do**:
  - Don't make real API calls (mock the LLM client)
  - Don't test MongoDB (in-memory only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Writing tests for 9 components — significant test writing effort
  - **Skills**: [`python-testing`]
    - `python-testing`: pytest patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES (but tests depend on implementations)
  - **Parallel Group**: Wave 4
  - **Blocks**: T14
  - **Blocked By**: T5, T6, T7, T8, T9, T12 (all implementations done)

  **References**:
  - `backend/tests/modules/test_solving/test_solving.py:1-100` — Existing test patterns
  - `backend/tests/core/conftest.py` — T6 fixtures
  - `backend/pyproject.toml` — pytest config

  **Acceptance Criteria**:
  - [ ] All 9 test files exist and run without collection errors
  - [ ] `python -m pytest tests/core/ -v` shows tests passing (or skipped for API-key-dependent tests)
  - [ ] Each test file has ≥3 test cases

  **QA Scenarios**:

  \`\`\`
  Scenario: All core tests collect without errors
    Tool: Bash
    Preconditions: Test files created
    Steps:
      1. cd backend && python -m pytest tests/core/ --collect-only 2>&1 | grep -c "test_"
    Expected Result: Count > 20 (multiple test functions across files)
    Failure Indicators: Collection errors, ImportError
    Evidence: .sisyphus/evidence/t13-collection.txt

  Scenario: Run dependency resolver tests
    Tool: Bash
    Preconditions: T2 implemented, test file created
    Steps:
      1. cd backend && python -m pytest tests/core/test_dependency_resolver.py -v
    Expected Result: Tests pass (or skip if incomplete)
    Failure Indicators: ImportError, NotImplementedError
    Evidence: .sisyphus/evidence/t13-dep-resolver-tests.txt
  \`\`\`

  **Commit**: YES
  - Message: `test: add unit tests for core infrastructure`
  - Files: `backend/tests/core/test_*.py`
  - Pre-commit: `python -m pytest tests/core/ -v`

---

- [x] T14. **Final verification + import audit**

  **What to do**:
  - Run full import check: `python -c "from app.core.registry import *; from app.core.events import *; from app.core.state import *; from app.core.orchestrator import *; print('All imports OK')"`
  - Run all core tests: `python -m pytest tests/core/ -v`
  - Verify no `NotImplementedError` remains in any core file:
    ```bash
    grep -r "raise NotImplementedError" backend/app/core/
    ```
  - Verify no duplicate class definitions
  - Check that all `__init__.py` files export correct classes
  - Run `python -m mypy app/core/ --ignore-missing-imports` for type hints
  - Create `.sisyphus/evidence/final-import-audit.txt` with audit results

  **Must NOT do**:
  - Don't modify code to suppress errors — fix the root cause

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Verification and audit commands
  - **Skills**: [`python-testing`]
    - `python-testing`: Test execution

  **Parallelization**:
  - **Can Run In Parallel**: NO (final check)
  - **Blocks**: None
  - **Blocked By**: T13

  **References**:
  - `backend/app/core/` — All implemented files

  **Acceptance Criteria**:
  - [ ] All imports succeed
  - [ ] `grep -r "raise NotImplementedError" backend/app/core/` returns 0 results
  - [ ] All core tests pass
  - [ ] Import audit file created

  **QA Scenarios**:

  \`\`\`
  Scenario: No NotImplementedError remains
    Tool: Bash
    Preconditions: All implementations complete
    Steps:
      1. grep -r "raise NotImplementedError" backend/app/core/
    Expected Result: No output (0 matches)
    Failure Indicators: Any matches found
    Evidence: .sisyphus/evidence/t14-no-stubs.txt

  Scenario: All core imports work
    Tool: Bash
    Preconditions: All implementations complete
    Steps:
      1. cd backend && python -c "
from app.core.registry.dependency_resolver import DependencyResolver
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus, Event
from app.core.events.event_types import EventType, EventValidator
from app.core.events.event_store import EventStore
from app.core.state.state_manager import StateManager, SessionState
from app.core.state.session_manager import SessionManager, Session
from app.core.orchestrator.llm_orchestrator import LLMOrchestrator
from app.core.orchestrator.prompt_engine import PromptEngine
from app.core.orchestrator.output_parser import OutputParser
print('All imports OK')
"
    Expected Result: Prints "All imports OK", exit code 0
    Failure Indicators: Any ImportError
    Evidence: .sisyphus/evidence/t14-all-imports.txt
  \`\`\`

  **Commit**: YES (if changes needed, otherwise NO)
  - Message: `chore: final verification of core infrastructure`
  - Files: Any fixes from verification
  - Pre-commit: Full test suite

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle` ✅ APPROVE
  Must Have [5/5] | Must NOT Have [5/5] | Tasks [14/14] | VERDICT: APPROVE

- [x] F2. **Code Quality Review** — `unspecified-high` ✅ APPROVE
  Build [PASS] | Files [10 clean] | VERDICT: APPROVE

- [x] F3. **Real Manual QA** — `unspecified-high` ✅ APPROVE
  Scenarios [12/12 pass] | VERDICT: APPROVE
  (Bug fixed: EventBus.publish() now handles sync handlers via run_in_executor)

- [x] F4. **Scope Fidelity Check** — `unspecified-high` ✅ APPROVE
  Tasks [14/14 compliant] | Contamination [CLEAN] | VERDICT: APPROVE

---

## Commit Strategy

Each component gets its own commit:
```
1. chore: resolve duplicate interfaces in module_registry
2. feat: implement DependencyResolver with topological sort
3. feat: implement Event + EventBus pub/sub
4. feat: implement EventType + EventValidator
5. feat: implement EventStore with in-memory storage
6. test: create core tests conftest.py and test files
7. feat: implement SessionState + StateManager
8. feat: implement Session + SessionManager
9. feat: implement ModuleRegistry with lifecycle management
10. feat: implement PromptEngine
11. feat: implement OutputParser
12. feat: implement LLMOrchestrator
13. test: add unit tests for core infrastructure
14. chore: final verification of core infrastructure
```

**Pre-commit hook**: `python -m pytest tests/core/ -v --tb=short`

---

## Success Criteria

### Verification Commands
```bash
# 1. All imports resolve
python -c "from app.core.registry import *; from app.core.events import *; from app.core.state import *; from app.core.orchestrator import *"

# 2. No stubs remain
grep -r "raise NotImplementedError" backend/app/core/  # expect 0 results

# 3. All core tests pass
python -m pytest tests/core/ -v

# 4. Can instantiate all components
python -c "
from app.core.registry.dependency_resolver import DependencyResolver
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus
from app.core.events.event_store import EventStore
from app.core.state.state_manager import StateManager
from app.core.state.session_manager import SessionManager
from app.core.orchestrator.llm_orchestrator import LLMOrchestrator
print('All instantiable')
"
```

### Final Checklist
- [x] All 62 methods implemented (not raising NotImplementedError)
- [x] All 14 classes instantiable with no arguments
- [x] EventBus subscribe → publish works (sync + async handlers)
- [x] DependencyResolver topological sort works
- [x] ModuleRegistry initializes modules in dependency order
- [x] Session state get/set/checkpoint/restore works
- [x] Session expiry works
- [x] LLMOrchestrator delegates to PromptEngine and OutputParser
- [x] All imports resolve without circular dependencies
- [x] Tests/core/ has test files for all components (122 tests passing)
- [x] No MongoDB dependency in core tests


---

- [x] T10. **Implement PromptEngine**

  **What to do**:
  - Read `backend/app/core/orchestrator/prompt_engine.py` to see current stub status
  - Implement `PromptEngine` methods:
    - `register_template(template_id: str, template: Any) -> None`: Store in `_templates`
    - `get_template(template_id: str) -> Optional[Any]`: Retrieve
    - `render_template(template_id: str, variables: Dict[str, Any]) -> str`: Use template string + variables to produce final prompt
    - `list_templates() -> List[str]`: Return all registered template IDs
    - `validate_template(template_id: str, variables: Dict[str, Any]) -> bool`: Check template exists and all variables provided
  - Template rendering: Support `${variable}` and `{{variable}}` syntax (simple string replace)
  - Use `logging`

  **Must NOT do**:
  - Don't implement complex template engines (Jinja2, etc.)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Template string interpolation
  - **Skills**: [`python-patterns`]
    - `python-patterns`: String manipulation patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T11, T12)
  - **Blocks**: T12 (LLMOrchestrator)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/orchestrator/prompt_engine.py:1-50` — Current stubs
  - `backend/app/modules/solving/prompts/templates.py:1-30` — Existing template strings

  **Acceptance Criteria**:
  - [ ] `PromptEngine()` instantiates
  - [ ] `register_template('test', 'Hello ${name}')` → `render_template('test', {'name': 'World'})` returns `'Hello World'`
  - [ ] `list_templates()` returns all registered IDs

  **QA Scenarios**:

  \`\`\`
  Scenario: Register and render simple template
    Tool: Bash
    Preconditions: PromptEngine implemented
    Steps:
      1. python -c "
from app.core.orchestrator.prompt_engine import PromptEngine
pe = PromptEngine()
pe.register_template('greet', 'Hello \${name}!')
result = pe.render_template('greet', {'name': 'Alice'})
assert result == 'Hello Alice!'
print('PASS')
"
    Expected Result: Template renders correctly
    Failure Indicators: Wrong string, exception
    Evidence: .sisyphus/evidence/t10-simple-render.txt

  Scenario: Template with missing variable raises KeyError
    Tool: Bash
    Preconditions: PromptEngine implemented
    Steps:
      1. python -c "
from app.core.orchestrator.prompt_engine import PromptEngine
pe = PromptEngine()
pe.register_template('greet', 'Hello \${name}!')
try:
    pe.render_template('greet', {})  # missing 'name'
    print('FAIL: should have raised')
except KeyError as e:
    print('PASS: raised KeyError as expected')
"
    Expected Result: KeyError raised for missing variable
    Failure Indicators: No exception or wrong exception
    Evidence: .sisyphus/evidence/t10-missing-var.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement PromptEngine`
  - Files: `backend/app/core/orchestrator/prompt_engine.py`
  - Pre-commit: `python -m pytest tests/core/test_prompt_engine.py -v`

---

- [x] T11. **Implement OutputParser**

  **What to do**:
  - Read `backend/app/core/orchestrator/output_parser.py` to see current stub status
  - Implement `OutputParser` methods:
    - `parse_json(output: str) -> Dict[str, Any]`: Parse JSON string; raise `ValueError` on failure
    - `parse_yaml(output: str) -> Dict[str, Any]`: Parse YAML string (use `yaml.safe_load`)
    - `parse_markdown(output: str, schema: Optional[Dict]) -> Dict[str, Any]`: Extract structured data from markdown (e.g., parse code blocks)
    - `validate_schema(data: Any, schema: Dict) -> bool`: Check data matches schema (simple key presence check)
    - `extract_json_blocks(output: str) -> List[str]`: Find all ` ```json ... ``` ` blocks in markdown
    - `clean_output(output: str) -> str`: Strip markdown formatting, trim whitespace
    - `parse(output: str, format: str, schema: Optional[Dict]) -> Any`: Dispatch to appropriate parser by format
  - Use `json`, `yaml` (PyYAML) for parsing
  - Use `logging`

  **Must NOT do**:
  - Don't implement full JSON Schema validation

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multi-format parsing with error handling
  - **Skills**: [`python-patterns`]
    - `python-patterns`: String parsing patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T10, T12)
  - **Blocks**: T12 (LLMOrchestrator)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/orchestrator/output_parser.py:1-50` — Current stubs
  - `backend/app/modules/solving/parser.py:20-60` — Existing parsing patterns

  **Acceptance Criteria**:
  - [ ] `parse_json('{"key": "value"}')` returns `{'key': 'value'}`
  - [ ] `parse_json('invalid')` raises `ValueError`
  - [ ] `extract_json_blocks('```json\\n{"a":1}\\n```')` returns `['{"a":1}']`
  - [ ] `clean_output('  text  ')` returns `'text'`

  **QA Scenarios**:

  \`\`\`
  Scenario: Parse valid JSON
    Tool: Bash
    Preconditions: OutputParser implemented
    Steps:
      1. python -c "
from app.core.orchestrator.output_parser import OutputParser
op = OutputParser()
result = op.parse_json('{\"key\": \"value\"}')
assert result == {'key': 'value'}
print('PASS')
"
    Expected Result: JSON parsed correctly
    Failure Indicators: Exception, wrong dict
    Evidence: .sisyphus/evidence/t11-parse-json.txt

  Scenario: Parse invalid JSON raises ValueError
    Tool: Bash
    Preconditions: OutputParser implemented
    Steps:
      1. python -c "
from app.core.orchestrator.output_parser import OutputParser
op = OutputParser()
try:
    op.parse_json('not json')
    print('FAIL')
except ValueError:
    print('PASS')
"
    Expected Result: ValueError raised
    Failure Indicators: No exception or different exception
    Evidence: .sisyphus/evidence/t11-invalid-json.txt

  Scenario: Extract JSON blocks from markdown
    Tool: Bash
    Preconditions: OutputParser implemented
    Steps:
      1. python -c "
from app.core.orchestrator.output_parser import OutputParser
op = OutputParser()
md = 'Here is some text\\n\\n```json\\n{\"a\": 1}\\n```\\n\\nMore text'
blocks = op.extract_json_blocks(md)
assert len(blocks) == 1
assert blocks[0] == '{\"a\": 1}'
print('PASS')
"
    Expected Result: One JSON block extracted
    Failure Indicators: Wrong number of blocks or wrong content
    Evidence: .sisyphus/evidence/t11-json-blocks.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement OutputParser`
  - Files: `backend/app/core/orchestrator/output_parser.py`
  - Pre-commit: `python -m pytest tests/core/test_output_parser.py -v`

---

- [x] T12. **Implement LLMOrchestrator**

  **What to do**:
  - Implement `LLMOrchestrator` methods (7 total):
    - `set_llm_client(client: Any) -> None`: Set `_llm_client` ( DashScopeClient or similar)
    - `register_template(template_id: str, template: Any) -> None`: Delegate to `_prompt_engine`
    - `render_template(template_id: str, variables: Dict[str, Any]) -> str`: Delegate to `_prompt_engine`
    - `list_templates() -> List[str]`: Delegate to `_prompt_engine`
    - `call_llm(prompt, model, max_tokens, temperature, retry_count) -> Dict[str, Any]`: Call `_llm_client.chat()` with retry logic (try up to `retry_count` times on failure); return dict with `content`, `model`, `usage`
    - `run_pipeline(pipeline_id, context, steps) -> Dict[str, Any]`: Execute pipeline steps in order; each step renders a template and calls `call_llm`; accumulate results in `context`
    - `parse_output(raw_output: str, schema: Any) -> Any`: Delegate to `_output_parser`
  - Initialize `_prompt_engine = PromptEngine()` and `_output_parser = OutputParser()` in `__init__`
  - Use `logging` for retries and errors
  - Retry logic: `try/except` loop up to `retry_count`

  **Must NOT do**:
  - Don't implement multi-provider routing (single LLM client)
  - Don't implement complex pipeline DAGs

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Orchestration with retry logic — coordinates multiple components
  - **Skills**: [`python-patterns`, `coding-standards`]
    - `python-patterns`: Retry patterns
    - `coding-standards`: Coordinates PromptEngine + OutputParser

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T10, T11)
  - **Blocks**: T13
  - **Blocked By**: T10, T11 (PromptEngine + OutputParser needed)

  **References**:
  - `backend/app/core/orchestrator/llm_orchestrator.py:1-60` — Current stubs
  - `backend/app/infrastructure/llm/dashscope_client.py:20-50` — LLM client interface
  - `backend/app/modules/solving/service.py:40-80` — Retry/error handling pattern

  **Acceptance Criteria**:
  - [ ] `LLMOrchestrator()` instantiates with internal `PromptEngine` and `OutputParser`
  - [ ] `register_template()` + `render_template()` work via internal engine
  - [ ] `call_llm('hello')` calls the LLM client (needs API key for full test)
  - [ ] `run_pipeline()` executes steps in sequence
  - [ ] `parse_output()` delegates to `OutputParser`

  **QA Scenarios**:

  \`\`\`
  Scenario: Template registration delegates to PromptEngine
    Tool: Bash
    Preconditions: LLMOrchestrator + PromptEngine implemented
    Steps:
      1. python -c "
from app.core.orchestrator.llm_orchestrator import LLMOrchestrator
orch = LLMOrchestrator()
orch.register_template('test', 'Hello \${who}')
result = orch.render_template('test', {'who': 'World'})
assert result == 'Hello World'
print('PASS')
"
    Expected Result: Template rendered through orchestrator
    Failure Indicators: Wrong result, exception
    Evidence: .sisyphus/evidence/t12-template-delegation.txt

  Scenario: LLMOrchestrator instantiates with sub-components
    Tool: Bash
    Preconditions: LLMOrchestrator implemented
    Steps:
      1. python -c "
from app.core.orchestrator.llm_orchestrator import LLMOrchestrator
orch = LLMOrchestrator()
assert orch._prompt_engine is not None
assert orch._output_parser is not None
templates = orch.list_templates()
assert isinstance(templates, list)
print('PASS')
"
    Expected Result: Sub-components initialized
    Failure Indicators: None or attribute errors
    Evidence: .sisyphus/evidence/t12-sub-components.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement LLMOrchestrator`
  - Files: `backend/app/core/orchestrator/llm_orchestrator.py`
  - Pre-commit: `python -m pytest tests/core/test_llm_orchestrator.py -v`

---


  **What to do**:
  - Implement all 9 async methods using **in-memory dict storage** (no MongoDB):
    - `store_event(event) -> StoredEvent`: Generate `event_id` (uuid), store in `_events[event_id]`
    - `store_batch(events) -> List[StoredEvent]`: Call `store_event` for each
    - `get_event(event_id) -> Optional[StoredEvent]`: Lookup by id
    - `get_events_by_session(session_id, start_time, end_time, event_types) -> List[StoredEvent]`: Filter by session + time range + types
    - `get_events_by_type(event_type, limit=100) -> List[StoredEvent]`: Filter by type, apply limit
    - `get_events_by_module(module_id, start_time, end_time) -> List[StoredEvent]`: Filter by source_module
    - `replay_session(session_id, from_time) -> List[Any]`: Return stored events for session
    - `delete_events(session_id=None, older_than=None) -> int`: Delete by session or age, return count
    - `get_event_stats(session_id=None, start_time=None, end_time=None) -> Dict[str, Any]`: Return counts by type
  - `StoredEvent.to_dict()`: Return dict with all fields
  - Use `datetime.utcnow()` for timestamps
  - Use `uuid.uuid4()` for event_id
  - Use `logging` for debug/info

  **Must NOT do**:
  - Don't implement MongoDB integration (that's a separate future task)
  - Don't make sync methods async (use `async def` for all)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: In-memory store with filtering logic
  - **Skills**: [`python-patterns`]
    - `python-patterns`: Async storage patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1-T4, T6)
  - **Blocks**: T13 (tests)
  - **Blocked By**: T3, T4 (Event + EventValidator needed for schema)

  **References**:
  - `backend/app/core/events/event_store.py:1-80` — Current stubs
  - `backend/app/modules/solving/models.py:40-80` — Dict-based model patterns

  **Acceptance Criteria**:
  - [ ] `EventStore()` instantiates with no args
  - [ ] `await store_event(event)` returns `StoredEvent` with `event_id`
  - [ ] `await get_events_by_session('sess_1')` returns filtered list
  - [ ] `await delete_events(older_than=...)` removes old events
  - [ ] `await get_event_stats()` returns dict with `total`, `by_type`

  **QA Scenarios**:

  \`\`\`
  Scenario: Store and retrieve single event
    Tool: Bash
    Preconditions: EventStore implemented
    Steps:
      1. python -c "
import asyncio
from app.core.events.event_store import EventStore, StoredEvent
from app.core.events.event_bus import Event

store = EventStore()
event = Event('TEST', {'key': 'value'}, 'sess_1', 'test_module')
stored = asyncio.run(store.store_event(event))
assert stored.event_id is not None
assert stored.event_type == 'TEST'
retrieved = asyncio.run(store.get_event(stored.event_id))
assert retrieved.event_type == 'TEST'
print('PASS')
"
    Expected Result: Event stored and retrieved with same data
    Failure Indicators: None returned, wrong data
    Evidence: .sisyphus/evidence/t5-store-retrieve.txt

  Scenario: Filter events by session
    Tool: Bash
    Preconditions: EventStore implemented
    Steps:
      1. python -c "
import asyncio
from app.core.events.event_store import EventStore
from app.core.events.event_bus import Event

store = EventStore()
e1 = Event('A', {}, 'sess_1', None)
e2 = Event('B', {}, 'sess_2', None)
asyncio.run(store.store_batch([e1, e2]))
results = asyncio.run(store.get_events_by_session('sess_1'))
assert len(results) == 1
assert results[0].event_type == 'A'
print('PASS')
"
    Expected Result: Only sess_1 events returned
    Failure Indicators: Wrong filter results
    Evidence: .sisyphus/evidence/t5-filter-session.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement EventStore with in-memory storage`
  - Files: `backend/app/core/events/event_store.py`
  - Pre-commit: `python -m pytest tests/core/test_event_store.py -v`

---

- [x] T6. **Create tests/core/ conftest.py fixtures**

  **What to do**:
  - Create `backend/tests/core/conftest.py` with pytest fixtures for all core components:
    - `dependency_resolver()` fixture — returns fresh `DependencyResolver()` instance
    - `event_bus()` fixture — returns fresh `EventBus()` instance
    - `event_store()` fixture — returns fresh `EventStore()` instance (async)
    - `state_manager()` fixture — returns fresh `StateManager()` instance
    - `session_manager()` fixture — returns fresh `SessionManager()` instance
    - `module_registry(event_bus)` fixture — returns `ModuleRegistry(event_bus)`
    - Mock MongoDB via `sys.modules` stub (like existing solving tests)
  - Add `tests/core/__init__.py`
  - Add `tests/core/test_dependency_resolver.py`, `tests/core/test_event_bus.py`, etc. (empty test files that will be filled by T13)

  **Must NOT do**:
  - Don't write full tests here (T13 does that)
  - Don't require external services

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple fixture creation, follows existing pattern from solving tests
  - **Skills**: [`python-testing`]
    - `python-testing`: pytest fixture conventions

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1-T5)
  - **Blocks**: T13 (tests)
  - **Blocked By**: None

  **References**:
  - `backend/tests/modules/test_solving/test_solving.py:1-20` — Existing fixture pattern
  - `backend/pyproject.toml` — pytest configuration

  **Acceptance Criteria**:
  - [ ] `conftest.py` created with all fixtures
  - [ ] `python -m pytest tests/core/ --collect-only` finds test files
  - [ ] `python -c "from tests.core.conftest import event_bus"` works

  **QA Scenarios**:

  \`\`\`
  Scenario: conftest fixtures load without errors
    Tool: Bash
    Preconditions: conftest.py created
    Steps:
      1. cd backend && python -c "import sys; sys.path.insert(0, '.'); from tests.core.conftest import dependency_resolver, event_bus; print('fixtures load OK')"
    Expected Result: Exit code 0, prints "fixtures load OK"
    Failure Indicators: ImportError
    Evidence: .sisyphus/evidence/t6-fixtures-load.txt

  Scenario: pytest discovers test files
    Tool: Bash
    Preconditions: conftest.py + test files created
    Steps:
      1. cd backend && python -m pytest tests/core/ --collect-only 2>&1 | head -20
    Expected Result: Shows collected test items (may be 0 if tests not written yet)
    Failure Indicators: Collection errors
    Evidence: .sisyphus/evidence/t6-discover-tests.txt
  \`\`\`

  **Commit**: YES
  - Message: `test: create core tests conftest.py and test files`
  - Files: `backend/tests/core/conftest.py`, `backend/tests/core/__init__.py`
  - Pre-commit: `python -m pytest tests/core/ --collect-only`

---

## Wave 2 — State + Registry

---

- [x] T7. **Implement SessionState + StateManager**

  **What to do**:
  - Implement `SessionState` methods (7 total):
    - `get_global_state() -> Dict[str, Any]`: Return copy of `self.global_state`
    - `set_global_state(state: Dict[str, Any]) -> None`: Replace `self.global_state`, add to history
    - `get_module_state(module_id) -> Dict[str, Any]`: Return `self.module_states[module_id]`
    - `set_module_state(module_id, state) -> None`: Set `self.module_states[module_id]`, add to history
    - `checkpoint(checkpoint_id) -> None`: Save snapshot of `global_state` + `module_states` to `checkpoints`
    - `restore_checkpoint(checkpoint_id) -> None`: Restore from `checkpoints` (raises KeyError if not found)
    - `list_checkpoints() -> List[str]`: Return sorted list of checkpoint IDs
  - Implement `StateManager` methods (6 total):
    - `create_session(session_id) -> SessionState`: Create new SessionState in `_sessions`
    - `get_session(session_id) -> Optional[SessionState]`: Lookup
    - `delete_session(session_id) -> None`: Remove from `_sessions`
    - `get_global_state(session_id) -> Dict[str, Any]`: Delegate to SessionState
    - `get_module_state(session_id, module_id) -> Dict[str, Any]`: Delegate
    - `set_module_state(session_id, module_id, state) -> None`: Delegate
    - `list_sessions() -> List[str]`: Return all session IDs
    - `cleanup_old_sessions(max_age_hours=24) -> int`: Remove sessions older than `max_age_hours`, return count
  - Use in-memory `dict` storage (no MongoDB)
  - Update `updated_at` timestamp on every state change
  - Use `logging`

  **Must NOT do**:
  - Don't implement MongoDB persistence

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: State management with history tracking
  - **Skills**: [`python-patterns`]
    - `python-patterns`: Dict-based state management

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T8, T9)
  - **Blocks**: T13
  - **Blocked By**: None

  **References**:
  - `backend/app/core/state/state_manager.py:1-100` — Current stubs
  - `backend/app/modules/solving/service.py:20-40` — State dict pattern

  **Acceptance Criteria**:
  - [ ] `StateManager()` instantiates
  - [ ] `create_session('s1')` returns `SessionState` with `session_id='s1'`
  - [ ] `set_module_state('s1', 'modA', {'key': 'val'})` → `get_module_state('s1', 'modA')` returns `{'key': 'val'}`
  - [ ] `checkpoint('cp1')` → `list_checkpoints()` includes `'cp1'`
  - [ ] `cleanup_old_sessions(0)` removes expired sessions

  **QA Scenarios**:

  \`\`\`
  Scenario: Create and retrieve session state
    Tool: Bash
    Preconditions: StateManager implemented
    Steps:
      1. python -c "
from app.core.state.state_manager import StateManager
sm = StateManager()
sess = sm.create_session('test_s1')
sess.set_module_state('modA', {'answer': 42})
retrieved = sm.get_module_state('test_s1', 'modA')
assert retrieved == {'answer': 42}
print('PASS')
"
    Expected Result: Session state stored and retrieved
    Failure Indicators: Wrong state returned, exception
    Evidence: .sisyphus/evidence/t7-session-state.txt

  Scenario: Checkpoint save and restore
    Tool: Bash
    Preconditions: StateManager implemented
    Steps:
      1. python -c "
from app.core.state.state_manager import StateManager
sm = StateManager()
sess = sm.create_session('test_s1')
sess.set_global_state({'count': 1})
sess.checkpoint('snap1')
sess.set_global_state({'count': 999})
sess.restore_checkpoint('snap1')
restored = sess.get_global_state()
assert restored == {'count': 1}
print('PASS')
"
    Expected Result: Checkpoint saves and restores correctly
    Failure Indicators: Wrong state after restore
    Evidence: .sisyphus/evidence/t7-checkpoint.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement SessionState + StateManager`
  - Files: `backend/app/core/state/state_manager.py`
  - Pre-commit: `python -m pytest tests/core/test_state_manager.py -v`

---

- [x] T8. **Implement Session + SessionManager**

  **What to do**:
  - Implement `Session` methods (3 total):
    - `is_expired() -> bool`: Compare `datetime.utcnow()` vs `expires_at`
    - `update_activity() -> None`: Set `last_activity = datetime.utcnow()`, extend `expires_at` by standard window
    - `extend(hours=1) -> None`: Add `hours` to `expires_at`
  - Implement `SessionManager` methods (8 total):
    - `create_session(user_id, metadata) -> Session`: Create session with 1-hour default expiry, add to `_sessions`
    - `get_session(session_id) -> Optional[Session]`: Lookup
    - `validate_session(session_id) -> bool`: Check exists AND NOT expired
    - `end_session(session_id) -> None`: Remove from `_sessions`
    - `update_activity(session_id) -> None`: Delegate to Session
    - `list_sessions(user_id=None) -> List[Session]`: Filter by user_id if provided
    - `cleanup_expired_sessions() -> int`: Remove all where `is_expired()`, return count
    - `get_session_stats(session_id) -> Dict[str, Any]`: Return dict with `session_id`, `user_id`, `created_at`, `last_activity`, `expires_at`, `is_expired`
  - Use `datetime.utcnow()` for all timestamps
  - Use `timedelta(hours=1)` for default session window
  - Use `logging`

  **Must NOT do**:
  - Don't implement persistent storage

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Session lifecycle management
  - **Skills**: [`python-patterns`]
    - `python-patterns`: Datetime/delta handling

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T7, T9)
  - **Blocks**: T13
  - **Blocked By**: T7 (StateManager for context)

  **References**:
  - `backend/app/core/state/session_manager.py:1-80` — Current stubs
  - `backend/app/modules/solving/models.py:20-40` — Datetime handling

  **Acceptance Criteria**:
  - [ ] `SessionManager()` instantiates
  - [ ] `create_session('user_1', {})` returns `Session` with `expires_at` ~1 hour in future
  - [ ] `is_expired()` returns `False` for fresh session, `True` after expiry
  - [ ] `extend(2)` pushes expiry 2 hours forward
  - [ ] `validate_session()` returns `True` for valid, `False` for expired/missing

  **QA Scenarios**:

  \`\`\`
  Scenario: Session not expired immediately after creation
    Tool: Bash
    Preconditions: SessionManager implemented
    Steps:
      1. python -c "
from app.core.state.session_manager import SessionManager
sm = SessionManager()
sess = sm.create_session('user_1', {})
assert sess.is_expired() == False
print('PASS')
"
    Expected Result: Fresh session not expired
    Failure Indicators: Exception, wrong bool
    Evidence: .sisyphus/evidence/t8-not-expired.txt

  Scenario: Session expired after manual expiry
    Tool: Bash
    Preconditions: SessionManager implemented
    Steps:
      1. python -c "
from app.core.state.session_manager import SessionManager
from datetime import datetime, timedelta
sm = SessionManager()
sess = sm.create_session('user_1', {})
sess.expires_at = datetime.utcnow() - timedelta(hours=1)
assert sess.is_expired() == True
print('PASS')
"
    Expected Result: Session with past expiry is_expired=True
    Failure Indicators: Wrong bool
    Evidence: .sisyphus/evidence/t8-expired.txt

  Scenario: validate_session returns correct status
    Tool: Bash
    Preconditions: SessionManager implemented
    Steps:
      1. python -c "
from app.core.state.session_manager import SessionManager
sm = SessionManager()
sess = sm.create_session('user_1', {})
sid = sess.session_id
assert sm.validate_session(sid) == True
sm.end_session(sid)
assert sm.validate_session(sid) == False
print('PASS')
"
    Expected Result: validate_session True after create, False after end
    Failure Indicators: Wrong bool
    Evidence: .sisyphus/evidence/t8-validate.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement Session + SessionManager`
  - Files: `backend/app/core/state/session_manager.py`
  - Pre-commit: `python -m pytest tests/core/test_session_manager.py -v`

---

- [x] T9. **Implement ModuleRegistry**

  **What to do**:
  - Implement `ModuleRegistry` methods (7 total):
    - `register_module(module: IModule) -> None`: Add to `_modules`, call `dependency_resolver.add_module()`
    - `get_module(module_id: str) -> Optional[IModule]`: Lookup in `_modules`
    - `get_modules_by_capability(capability: str) -> List[IModule]`: Return modules where `module_id` matches or `provides_events` contains capability
    - `get_dependencies(module_id: str) -> List[str]`: Delegate to `dependency_resolver`
    - `initialize_all(context: ModuleContext) -> None`: Resolve order via `dependency_resolver`, call `await module.initialize(context)` for each in order
    - `shutdown_all() -> None`: Call `await module.shutdown()` for each in reverse order
    - `list_modules() -> List[str]`: Return sorted list of registered module IDs
  - `_initialized` flag — `initialize_all` sets True; prevent double-init
  - Use `logging` for lifecycle events (info on init, warn on duplicate registration)
  - Import `IModule` from `app.core.interfaces.module` and `ModuleContext` from `app.core.context`

  **Must NOT do**:
  - Don't implement module discovery (manual registration only)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Lifecycle orchestration with dependency ordering — complex coordination
  - **Skills**: [`python-patterns`, `coding-standards`]
    - `python-patterns`: Async orchestration
    - `coding-standards`: Interface compliance

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T7, T8)
  - **Blocks**: T13
  - **Blocked By**: T1 (duplicate fix), T2 (DependencyResolver)

  **References**:
  - `backend/app/core/registry/module_registry.py:1-150` — After T1 fixes (no duplicates)
  - `backend/app/core/registry/dependency_resolver.py` — T2 implementation
  - `backend/app/modules/solving/module.py:20-50` — Module lifecycle pattern

  **Acceptance Criteria**:
  - [ ] `ModuleRegistry(event_bus)` instantiates
  - [ ] `register_module(mock_module)` → `get_module(mock_module.module_id)` returns it
  - [ ] `initialize_all(context)` calls `initialize` on all registered modules in dependency order
  - [ ] `shutdown_all()` calls `shutdown` in reverse order
  - [ ] `list_modules()` returns sorted module IDs

  **QA Scenarios**:

  \`\`\`
  Scenario: Register and retrieve module
    Tool: Bash
    Preconditions: ModuleRegistry + DependencyResolver implemented
    Steps:
      1. python -c "
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus

class MockModule:
    module_id = 'test_mod'
    module_name = 'Test'
    version = '1.0'
    dependencies = []
    provides_events = []
    subscribes_events = []
    async def initialize(self, ctx): pass
    async def shutdown(self): pass

reg = ModuleRegistry(EventBus())
mod = MockModule()
reg.register_module(mod)
retrieved = reg.get_module('test_mod')
assert retrieved is mod
print('PASS')
"
    Expected Result: Module registered and retrieved
    Failure Indicators: None returned, exception
    Evidence: .sisyphus/evidence/t9-register-retrieve.txt

  Scenario: Modules initialize in dependency order
    Tool: Bash
    Preconditions: ModuleRegistry + DependencyResolver implemented
    Steps:
      1. python -c "
import asyncio
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus
from app.core.context import ModuleContext

order = []
class ModA:
    module_id = 'A'; module_name = 'A'; version = '1.0'
    dependencies = []
    provides_events = []; subscribes_events = []
    async def initialize(self, ctx): order.append('A')
    async def shutdown(self): pass

class ModB:
    module_id = 'B'; module_name = 'B'; version = '1.0'
    dependencies = ['A']
    provides_events = []; subscribes_events = []
    async def initialize(self, ctx): order.append('B')
    async def shutdown(self): pass

reg = ModuleRegistry(EventBus())
ctx = ModuleContext(registry=reg, orchestrator=None, state_manager=None, event_bus=None, config={}, session_manager=None, repository=None, logger=None)
reg.register_module(ModA())
reg.register_module(ModB())
asyncio.run(reg.initialize_all(ctx))
assert order == ['A', 'B'], f'Expected [A,B], got {order}'
print('PASS')
"
    Expected Result: A initializes before B
    Failure Indicators: Wrong order
    Evidence: .sisyphus/evidence/t9-init-order.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement ModuleRegistry with lifecycle management`
  - Files: `backend/app/core/registry/module_registry.py`
  - Pre-commit: `python -m pytest tests/core/test_module_registry.py -v`

---


### Original Request

User has an architecture plan (`math-tutor-architecture.md`) defining a modular plugin system. The `app/core/` layer contains 10 stub files that need full implementation. Two files (`interfaces/module.py`, `context.py`) are already fully implemented.

### What We Discussed

- User wants to build infrastructure before continuing Module 2-5
- The solving module (Module 1) is complete and e2e-verified
- Existing patterns: Pydantic v2 + BaseModel, async/await everywhere, pytest-asyncio

### Research Findings

- **Type style**: Pydantic `BaseModel` + `Field()` for data models; `dataclass` for `ModuleContext`
- **Async**: All services/managers use `async def`; `await` for I/O
- **Error handling**: `try/except` in services returns failed response; stubs `raise NotImplementedError`
- **Testing**: pytest + pytest-asyncio with `asyncio_mode = "auto"`; motor stubbed via `sys.modules`
- **Imports**: `TYPE_CHECKING` block for forward refs; absolute imports from `app` root

### Metis Review

**Identified Gaps (addressed below as defaults):**
1. Duplicate `IModule`/`ModuleContext` in `module_registry.py` → **Auto-resolved**: Remove duplicates, import from `interfaces/` and `context.py`
2. Storage backend unknown (MongoDB stub) → **Auto-resolved**: Use in-memory `dict` storage initially; MongoDB integration as separate future task
3. `ConfigManager` unknown → **Auto-resolved**: `ModuleContext.config` is `Any` — pass `dict` from `app.config.settings`

---

## Work Objectives

### Core Objective

Implement all `NotImplementedError` stubs in `app/core/` so components are instantiable, testable, and functional with in-memory storage.

### Concrete Deliverables

| File | Class(es) | Methods | Status |
|------|-----------|---------|--------|
| `registry/dependency_resolver.py` | `DependencyResolver` | 5 | STUB → IMPLEMENTED |
| `registry/module_registry.py` | `ModuleRegistry` | 9 | STUB → IMPLEMENTED |
| `events/event_bus.py` | `Event`, `EventBus` | 11 | STUB → IMPLEMENTED |
| `events/event_types.py` | `EventType`, `EventValidator` | 6 | STUB → IMPLEMENTED |
| `events/event_store.py` | `EventStore`, `StoredEvent` | 10 | STUB → IMPLEMENTED |
| `state/state_manager.py` | `StateManager`, `SessionState` | 12 | STUB → IMPLEMENTED |
| `state/session_manager.py` | `Session`, `SessionManager` | 11 | STUB → IMPLEMENTED |
| `orchestrator/llm_orchestrator.py` | `LLMOrchestrator` | 7 | STUB → IMPLEMENTED |
| `orchestrator/prompt_engine.py` | `PromptEngine` | 6 | NEEDS REVIEW → IMPLEMENTED |
| `orchestrator/output_parser.py` | `OutputParser` | 7 | NEEDS REVIEW → IMPLEMENTED |

### Definition of Done

- [ ] All 62 methods return real values (not `NotImplementedError`)
- [ ] `python -m pytest tests/core/ -v` passes (or skips if API key required)
- [ ] All imports resolve without circular dependency errors
- [ ] No `as any` / `@ts-ignore` introduced
- [ ] Each class instantiates with no arguments

### Must Have

- All classes implement their defined interfaces (from `interfaces/`)
- Async methods use `async def` / `await` correctly
- EventBus supports `subscribe` → `publish` → handler call
- DependencyResolver produces valid topological order
- In-memory storage for EventStore and StateManager (no MongoDB dependency)

### Must NOT Have

- ❌ No MongoDB implementation (it's a separate stub)
- ❌ No FastAPI routes (routes are in module files)
- ❌ No changes to `interfaces/module.py` or `context.py`
- ❌ No changes to existing module implementations
- ❌ No external API calls in unit tests

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest + pytest-asyncio)
- **Automated tests**: YES (Tests-after — implement first, then test)
- **Framework**: `pytest` + `pytest-asyncio`
- **Storage for tests**: In-memory `dict` (no MongoDB)

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/`.

**Verification Commands**:
```bash
# Import check
python -c "from app.core.registry.dependency_resolver import DependencyResolver; dr = DependencyResolver(); print('OK')"

# Run core tests
python -m pytest tests/core/ -v --ignore=tests/e2e

# Type check
python -m mypy app/core/ --ignore-missing-import
```

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — no inter-file dependencies):
├── T1:  Resolve duplicate interfaces in module_registry.py
├── T2:  Implement DependencyResolver
├── T3:  Implement Event + EventBus
├── T4:  Implement EventType + EventValidator
├── T5:  Implement EventStore
└── T6:  Create tests/core/ fixtures (conftest.py)

Wave 2 (State + Registry):
├── T7:  Implement SessionState + StateManager
├── T8:  Implement Session + SessionManager
└── T9:  Implement ModuleRegistry (uses DependencyResolver)

Wave 3 (Orchestrator):
├── T10: Implement PromptEngine
├── T11: Implement OutputParser
└── T12: Implement LLMOrchestrator

Wave 4 (Integration):
├── T13: Write unit tests for all components
└── T14: Final verification + import audit

Critical Path: T1 → T2 → T9 → T12 → T13 → T14
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

| Task | Blocks | Blocked By |
|------|--------|------------|
| T1 (duplicate fix) | T9 | None |
| T2 (DepResolver) | T9 | None |
| T3 (Event+Bus) | T5 | None |
| T4 (EventTypes) | T3, T5 | None |
| T5 (EventStore) | T13 | T3, T4 |
| T6 (conftest) | T13 | None |
| T7 (StateManager) | T13 | None |
| T8 (SessionManager) | T13 | T7 |
| T9 (ModuleRegistry) | T13 | T1, T2 |
| T10 (PromptEngine) | T12 | None |
| T11 (OutputParser) | T12 | None |
| T12 (LLMOrchestrator) | T13 | T10, T11 |
| T13 (tests) | T14 | T5, T6, T7, T8, T9, T12 |
| T14 (final) | — | T13 |

---

## TODOs

- [x] T1. **Resolve duplicate interfaces in module_registry.py**

  **What to do**:
  - Remove the duplicate `IModule` abstract class definition from `module_registry.py` (lines ~18-91)
  - Remove the duplicate `ModuleContext` class definition from `module_registry.py`
  - Add imports at top of `module_registry.py`:
    ```python
    from app.core.interfaces.module import IModule
    from app.core.context import ModuleContext
    ```
  - Keep only `ModuleRegistry` class in this file
  - Verify: `from app.core.registry.module_registry import ModuleRegistry` works without errors

  **Must NOT do**:
  - Don't modify `interfaces/module.py` or `context.py`
  - Don't change the IModule interface contract

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple refactor (remove duplicate code, add imports)
  - **Skills**: [`coding-standards`]
    - `coding-standards`: Confirms import/export conventions

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T2-T6)
  - **Blocks**: T9 (ModuleRegistry)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/interfaces/module.py:1-60` — Original IModule to keep
  - `backend/app/core/context.py:1-30` — Original ModuleContext to keep
  - `backend/app/core/registry/module_registry.py:18-91` — Duplicate definitions to REMOVE

  **Acceptance Criteria**:
  - [ ] `python -c "from app.core.registry.module_registry import ModuleRegistry"` succeeds
  - [ ] `python -c "from app.core.interfaces.module import IModule"` succeeds
  - [ ] `python -c "from app.core.context import ModuleContext"` succeeds
  - [ ] No duplicate class definitions remain in module_registry.py

  **QA Scenarios**:

  \`\`\`
  Scenario: Import ModuleRegistry without errors
    Tool: Bash
    Preconditions: Clean Python environment
    Steps:
      1. python -c "from app.core.registry.module_registry import ModuleRegistry; print(ModuleRegistry.__name__)"
    Expected Result: Prints "ModuleRegistry" with exit code 0
    Failure Indicators: ImportError, AttributeError
    Evidence: .sisyphus/evidence/t1-import-success.txt

  Scenario: Verify no duplicate IModule class
    Tool: Bash
    Preconditions: File modified
    Steps:
      1. grep -c "^class IModule" backend/app/core/registry/module_registry.py
    Expected Result: 0 occurrences (class was removed)
    Failure Indicators: Count > 0
    Evidence: .sisyphus/evidence/t1-no-duplicate.txt
  \`\`\`

  **Commit**: YES
  - Message: `chore: remove duplicate IModule/ModuleContext from module_registry`
  - Files: `backend/app/core/registry/module_registry.py`
  - Pre-commit: `python -c "from app.core.registry.module_registry import ModuleRegistry"`

---

- [x] T2. **Implement DependencyResolver**

  **What to do**:
  - Implement all 5 methods in `DependencyResolver` class:
    - `add_module(module_id, dependencies)`: Build `_dependency_graph` dict
    - `resolve_order() -> List[str]`: Kahn's algorithm topological sort; raises `CircularDependencyError` if cycle detected
    - `detect_circular_dependencies() -> List[List[str]]`: Return list of cycle paths (e.g. `[['A','B','C','A']]`)
    - `get_initialization_order() -> List[str]`: Alias for `resolve_order()`
    - `validate_dependencies(available_modules) -> Dict[str, bool]`: Return `{module_id: True/False}` for each registered module
  - Add custom exception `CircularDependencyError(Exception)` for cycle detection
  - Use `logging` for debug/info messages
  - Follow typing: `List`, `Dict`, `Set` from `typing`

  **Must NOT do**:
  - Don't use external libraries (implement sort manually)
  - Don't modify the class signature (keep `module_id: str`, `dependencies: List[str]`)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Graph algorithm (topological sort) — requires careful implementation
  - **Skills**: [`python-patterns`]
    - `python-patterns`: Confirms Pythonic algorithm implementation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T3-T6)
  - **Blocks**: T9 (ModuleRegistry uses it)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/registry/dependency_resolver.py:1-50` — Current stub (lines to replace)
  - `backend/app/modules/solving/evaluator.py:20-40` — Error handling pattern (custom exceptions)

  **Acceptance Criteria**:
  - [ ] `DependencyResolver()` instantiates with no args
  - [ ] `dr.add_module('A', [])` then `dr.add_module('B', ['A'])` → `dr.resolve_order()` returns `['A', 'B']`
  - [ ] Circular `A→B→C→A` → `detect_circular_dependencies()` returns `[['A','B','C','A']]`
  - [ ] `validate_dependencies({'A'})` returns `{'A': True, 'B': False}`

  **QA Scenarios**:

  \`\`\`
  Scenario: Linear dependency resolves in correct order
    Tool: Bash
    Preconditions: DependencyResolver implemented
    Steps:
      1. python -c "
from app.core.registry.dependency_resolver import DependencyResolver
dr = DependencyResolver()
dr.add_module('A', [])
dr.add_module('B', ['A'])
dr.add_module('C', ['B'])
order = dr.resolve_order()
print(order)
assert order == ['A', 'B', 'C'], f'Expected [A,B,C], got {order}'
print('PASS')
"
    Expected Result: Prints ['A', 'B', 'C'] and 'PASS'
    Failure Indicators: Wrong order, exception raised
    Evidence: .sisyphus/evidence/t2-linear-order.txt

  Scenario: Circular dependency detected
    Tool: Bash
    Preconditions: DependencyResolver implemented
    Steps:
      1. python -c "
from app.core.registry.dependency_resolver import DependencyResolver
dr = DependencyResolver()
dr.add_module('A', ['B'])
dr.add_module('B', ['A'])
cycles = dr.detect_circular_dependencies()
print(cycles)
assert len(cycles) == 1, f'Expected 1 cycle, got {len(cycles)}'
print('PASS')
"
    Expected Result: Cycle detected and printed
    Failure Indicators: No cycle detected, crash
    Evidence: .sisyphus/evidence/t2-circular-detected.txt

  Scenario: Diamond dependency resolves correctly
    Tool: Bash
    Preconditions: DependencyResolver implemented
    Steps:
      1. python -c "
from app.core.registry.dependency_resolver import DependencyResolver
dr = DependencyResolver()
dr.add_module('D', ['B', 'C'])
dr.add_module('B', ['A'])
dr.add_module('C', ['A'])
dr.add_module('A', [])
order = dr.resolve_order()
print(order)
assert order.index('A') < order.index('B')
assert order.index('A') < order.index('C')
assert order.index('B') < order.index('D')
assert order.index('C') < order.index('D')
print('PASS')
"
    Expected Result: Valid topological order for diamond graph
    Failure Indicators: Incorrect relative ordering
    Evidence: .sisyphus/evidence/t2-diamond-order.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement DependencyResolver with topological sort`
  - Files: `backend/app/core/registry/dependency_resolver.py`
  - Pre-commit: `python -m pytest tests/core/test_dependency_resolver.py -v`

---

- [x] T3. **Implement Event + EventBus**

  **What to do**:
  - Implement `Event.to_dict()`: Return dict with `event_type`, `data`, `session_id`, `source_module`, `timestamp`, `event_id`
  - Implement `Event.from_dict(cls, data)`: Classmethod reconstructs Event from dict
  - Implement `EventBus` methods:
    - `subscribe(event_type, handler)`: Add handler to `_subscribers[event_type]` list
    - `subscribe_all(handler)`: Add to `_wildcard_subscribers` list
    - `unsubscribe(event_type, handler)`: Remove handler from lists
    - `publish(event) -> None`: Call all matching handlers via `asyncio.create_task()`
    - `publish_batch(events) -> None`: Call `publish()` for each
    - `get_subscriber_count(event_type) -> int`
    - `list_event_types() -> List[str]`
    - `clear_subscribers(event_type=None)`: Clear specific or all
  - Event class already has `__init__` — only add `to_dict` and `from_dict`

  **Must NOT do**:
  - Don't use a real event bus library — implement from scratch
  - Don't make `publish` synchronous (must be async)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Pub/sub implementation with async handling
  - **Skills**: [`python-patterns`]
    - `python-patterns`: Async patterns and dict serialization

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T4-T6)
  - **Blocks**: T5 (EventStore)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/events/event_bus.py:1-120` — Current stubs
  - `backend/app/modules/solving/service.py:40-60` — Async error handling pattern

  **Acceptance Criteria**:
  - [ ] `Event.to_dict()` returns serializable dict with all fields
  - [ ] `Event.from_dict(d)` reconstructs equivalent Event
  - [ ] `subscribe('TEST', handler)` + `publish(Event('TEST', {}, None, None))` → handler called
  - [ ] `subscribe_all(handler)` → handler called on ALL events
  - [ ] `publish_batch([e1, e2])` processes both events

  **QA Scenarios**:

  \`\`\`
  Scenario: Subscribe then publish delivers event to handler
    Tool: Bash
    Preconditions: EventBus implemented
    Steps:
      1. python -c "
import asyncio
from app.core.events.event_bus import Event, EventBus

received = []
async def handler(event):
    received.append(event)

bus = EventBus()
bus.subscribe('TEST_EVENT', handler)
asyncio.run(bus.publish(Event('TEST_EVENT', {'key': 'value'}, None, None)))
assert len(received) == 1
assert received[0].event_type == 'TEST_EVENT'
print('PASS')
"
    Expected Result: Handler called with correct event, exit code 0
    Failure Indicators: Handler not called, AttributeError
    Evidence: .sisyphus/evidence/t3-subscribe-publish.txt

  Scenario: Wildcard subscriber receives all events
    Tool: Bash
    Preconditions: EventBus implemented
    Steps:
      1. python -c "
import asyncio
from app.core.events.event_bus import Event, EventBus

received = []
def wildcard_handler(event):
    received.append(event)

bus = EventBus()
bus.subscribe_all(wildcard_handler)
asyncio.run(bus.publish(Event('EVENT_A', {}, None, None)))
asyncio.run(bus.publish(Event('EVENT_B', {}, None, None)))
assert len(received) == 2
print('PASS')
"
    Expected Result: Wildcard handler called twice
    Failure Indicators: Handler not called or called wrong number of times
    Evidence: .sisyphus/evidence/t3-wildcard-subscriber.txt

  Scenario: Unsubscribe stops delivery
    Tool: Bash
    Preconditions: EventBus implemented
    Steps:
      1. python -c "
import asyncio
from app.core.events.event_bus import Event, EventBus

received = []
def handler(event):
    received.append(event)

bus = EventBus()
bus.subscribe('TEST', handler)
bus.unsubscribe('TEST', handler)
asyncio.run(bus.publish(Event('TEST', {}, None, None)))
assert len(received) == 0
print('PASS')
"
    Expected Result: No events delivered after unsubscribe
    Failure Indicators: Event delivered after unsubscribe
    Evidence: .sisyphus/evidence/t3-unsubscribe.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement Event + EventBus pub/sub`
  - Files: `backend/app/core/events/event_bus.py`
  - Pre-commit: `python -m pytest tests/core/test_event_bus.py -v`

---

- [x] T4. **Implement EventType + EventValidator**

  **What to do**:
  - Implement `EventType.get_category(event_type: str) -> Optional[EventCategory]`: Map event type string to its category enum
  - Implement `EventType.is_valid_type(event_type: str) -> bool`: Check if event type exists in `EVENT_SCHEMAS`
  - Implement `EventType.list_by_category(category: EventCategory) -> List[str]`: Return all event type strings in that category
  - Implement `EventValidator.validate_event(event_type, data) -> bool`: Use `EVENT_SCHEMAS` to validate required fields present
  - Implement `EventValidator.get_validation_errors(event_type, data) -> List[str]`: Return list of missing/invalid fields
  - Implement `EventValidator.validate_required_fields(data, required_fields) -> List[str]`: Check data dict has all required keys
  - Use `logging` for debug messages
  - Constants `EventCategory` and `EventSeverity` enums are already defined

  **Must NOT do**:
  - Don't modify `EVENT_SCHEMAS` (pre-defined in architecture)
  - Don't change enum values

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward enum/validation logic, no complex algorithms
  - **Skills**: [`coding-standards`]
    - `coding-standards`: Validation pattern consistency

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1-T3, T5-T6)
  - **Blocks**: T3 tests (but not implementation)
  - **Blocked By**: None

  **References**:
  - `backend/app/core/events/event_types.py:1-100` — Current stubs
  - `backend/app/modules/solving/models.py:20-60` — Pydantic validation pattern

  **Acceptance Criteria**:
  - [ ] `EventType.is_valid_type('SOLVING_STARTED')` returns `True`
  - [ ] `EventType.is_valid_type('INVALID_TYPE')` returns `False`
  - [ ] `EventType.get_category('SOLVING_STARTED')` returns `EventCategory.SOLVING`
  - [ ] `EventValidator.validate_event('SOLVING_STARTED', {'data': 'x'})` returns `True/False` based on schema
  - [ ] `EventValidator.get_validation_errors('SOLVING_STARTED', {})` returns list of missing fields

  **QA Scenarios**:

  \`\`\`
  Scenario: Valid event type is recognized
    Tool: Bash
    Preconditions: EventType implemented
    Steps:
      1. python -c "
from app.core.events.event_types import EventType
assert EventType.is_valid_type('SOLVING_STARTED') == True
assert EventType.is_valid_type('MODULE_INITIALIZED') == True
print('PASS')
"
    Expected Result: Exit code 0, prints PASS
    Failure Indicators: Wrong boolean return
    Evidence: .sisyphus/evidence/t4-valid-type.txt

  Scenario: Invalid event type returns False
    Tool: Bash
    Preconditions: EventType implemented
    Steps:
      1. python -c "
from app.core.events.event_types import EventType
assert EventType.is_valid_type('INVALID_EVENT') == False
print('PASS')
"
    Expected Result: Exit code 0
    Failure Indicators: Exception or wrong return
    Evidence: .sisyphus/evidence/t4-invalid-type.txt

  Scenario: Validation errors returned for missing required fields
    Tool: Bash
    Preconditions: EventValidator implemented
    Steps:
      1. python -c "
from app.core.events.event_types import EventValidator
v = EventValidator()
errors = v.validate_required_fields({'a': 1}, ['a', 'b', 'c'])
assert 'b' in errors
assert 'c' in errors
assert 'a' not in errors
print('PASS')
"
    Expected Result: Missing fields 'b' and 'c' in errors list
    Failure Indicators: Wrong error list
    Evidence: .sisyphus/evidence/t4-validation-errors.txt
  \`\`\`

  **Commit**: YES
  - Message: `feat: implement EventType + EventValidator`
  - Files: `backend/app/core/events/event_types.py`
  - Pre-commit: `python -m pytest tests/core/test_event_types.py -v`

---

