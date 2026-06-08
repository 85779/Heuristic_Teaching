# Intervention Testing - Issues

## Issue: Import errors with app.infrastructure stubs

### Problem
When running pytest on the intervention module tests, got `ImportError: cannot import name 'MongoDBConnection' from 'database' (unknown location)`. The stubs in conftest.py were not being applied before module imports.

### Solution
1. Created a proper module hierarchy for stubs:
   - Stub `app.infrastructure.database` with `MongoDBConnection`
   - Stub `app.infrastructure.llm.base_client` with `BaseLLMClient` and `Message`
   - Stub all submodules (`cache`, `logging`) 
2. Created a proper `StubMessage` class that accepts `(role: str, content: str)` arguments like the real `Message` class

### Key Pattern
```python
class StubMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    def to_dict(self):
        return {"role": self.role, "content": self.content}

stub_llm_base.Message = StubMessage
```

## Issue: test_record_outcome_accepted - missing import

### Problem
`NameError: name 'Intervention' is not defined` because `Intervention` was not imported in the test file.

### Solution
Added `Intervention` to the import statement:
```python
from app.modules.intervention.models import InterventionType, InterventionStatus, Intervention
```
