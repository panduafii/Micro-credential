# Python Project Development Rules

## CRITICAL: Module Import Setup

### For ALL Scripts in `scripts/` Directory
Every Python script MUST include this header before any `src` imports:

```python
from __future__ import annotations

import sys
from pathlib import Path

# REQUIRED: Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now you can import from src
from src.api.main import app
```

**Reason:** Prevents `ModuleNotFoundError: No module named 'src'` in CI/CD pipelines.

## Code Quality Gates

Before any commit:
```bash
# 1. Lint check
poetry run ruff check .

# 2. Format check  
poetry run ruff format --check .

# 3. Run tests
poetry run pytest tests/

# 4. If all pass, commit
git add -A
git commit -m "your message"
git push
```

## SQLAlchemy Reserved Keywords

**NEVER use these names directly:**
- `metadata` → use `metadata_` with explicit column: `mapped_column("metadata", JSON)`

## Import Order (Ruff I001)
1. `from __future__ import annotations`
2. Standard library
3. Third-party
4. Local `from src.*`

**IMPORTANT:** Run `ruff check --fix .` before commit to auto-sort imports.

## Line Length (E501)
- **Maximum: 100 characters**
- Use parentheses or backslash for line continuation:

```python
# BAD - line too long (E501)
ESSAY_SCORING_SYSTEM_PROMPT = """You are an expert essay evaluator for a micro-credential assessment platform.

# GOOD - use backslash continuation
ESSAY_SCORING_SYSTEM_PROMPT = """You are an expert essay evaluator for a \
micro-credential assessment platform.

# GOOD - use parentheses for assignment
self.timeout = (
    timeout_seconds if timeout_seconds is not None else settings.gpt_timeout_seconds
)

# GOOD - break long strings in tests/data
response_data = {
    "answer": (
        "First part of the long string "
        "second part of the long string"
    )
}

# GOOD - break long Enum in migrations
sa.Enum(
    "value1", "value2", "value3",
    name="enumname",
    create_type=False,
),
```

## Unused Imports (F401)
- **ALWAYS** remove unused imports before commit
- Run `ruff check --fix .` to auto-remove them
- Don't import "just in case" - import when needed

```python
# BAD - imported but never used
from typing import TYPE_CHECKING, Any
from src.models import User  # Never used!

# GOOD - only import what you use
from typing import Any
```

## Unused Variables (F841)
- **NEVER** assign to a variable you don't use:

```python
# BAD
except httpx.TimeoutException as e:  # e is never used
    last_error = GPTTimeoutError("Request timed out")

# GOOD - use underscore for intentionally unused
except httpx.TimeoutException as _:
    last_error = GPTTimeoutError("Request timed out")

# OR just don't assign
except httpx.TimeoutException:
    last_error = GPTTimeoutError("Request timed out")
```

## Undefined Names (F821)
- **NEVER** use a class/function that's not imported
- Always verify imports exist before using:

```python
# BAD - UnitOfWork is not imported!
async with UnitOfWork() as uow:
    pass

# GOOD - use available imports or create placeholder
# TODO: Implement when UnitOfWork is available
result = {"status": "placeholder"}
```

## FastAPI Patterns
- `Depends()` in defaults is OK (B008 ignored)
- This is standard FastAPI DI pattern

## Test Fixtures Naming
- Use consistent fixture names across tests
- Common: `db` for database session, `test_client` for HTTP client

```python
# Conftest standard fixtures
@pytest.fixture
async def db(test_client: TestClient) -> AsyncIterator[AsyncSession]:
    """Provide a database session for tests."""
    ...

# In tests - use 'db' NOT 'async_session'
async def test_something(db: AsyncSession):
    ...
```

## Dataclass Required Fields
- When creating dataclass responses, include ALL required fields:

```python
# BAD - missing total_tokens and finish_reason
GPTResponse(
    content="...",
    model="gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
)

# GOOD - all fields included
GPTResponse(
    content="...",
    model="gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,  # Don't forget!
    finish_reason="stop",  # Don't forget!
)
```

## Model Field Names
- Always check actual model definition before creating instances:

```python
# Check the model first!
# class AssessmentQuestionSnapshot:
#     question_template_id: int  # NOT source_question_id!

# BAD - using wrong field name
snapshot = AssessmentQuestionSnapshot(
    source_question_id=q.id,  # Wrong!
    version_at_snapshot=1,     # Doesn't exist!
)

# GOOD - using actual field names
snapshot = AssessmentQuestionSnapshot(
    question_template_id=q.id,  # Correct!
)
```

## Enum Values
- Always verify enum values exist before using:

```python
# BAD - PENDING doesn't exist!
job = AsyncJob(status=JobStatus.PENDING)

# Check the actual enum:
# class JobStatus(str, Enum):
#     QUEUED = "queued"  # Use this!

# GOOD
job = AsyncJob(status=JobStatus.QUEUED)
```

## Common Fixes

### Fix Import Errors
```bash
poetry run ruff check --fix .
```

### Fix Formatting
```bash
poetry run ruff format .
```

### Test Imports
```bash
poetry run python -c "from src.api.main import app; print('OK')"
```

## Pre-Commit Checklist

Before EVERY commit:
1. [ ] `poetry run ruff check .` - passes
2. [ ] `poetry run ruff format --check .` - passes  
3. [ ] `poetry run pytest tests/` - all tests pass
4. [ ] No line > 100 characters
5. [ ] No unused imports (F401)
6. [ ] No undefined names (F821)
7. [ ] All required dataclass fields provided
8. [ ] Correct model field names used
9. [ ] Correct enum values used

## Agent Activation Checklist

When BMAD Dev agent is activated:
- [ ] Read `docs/architecture/ai-development-guidelines.md`
- [ ] Check `docs/architecture/coding-standards.md`
- [ ] Verify all scripts have path setup
- [ ] Run quality gates before commit
- [ ] Test in isolation: `poetry run python script.py`
