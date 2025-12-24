# AI Development Guidelines

This document provides guidelines for AI agents (GitHub Copilot, BMAD agents, etc.) working on this codebase.

## Critical Rules

### 1. Python Module Imports
**ALWAYS** add path setup when creating scripts in the `scripts/` directory:

```python
import sys
from pathlib import Path

# This MUST be included before importing src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app  # Now this works
```

**Why:** Scripts may run in CI, Docker, or different working directories. Without explicit path setup, `ModuleNotFoundError: No module named 'src'` will occur.

### 2. SQLAlchemy Reserved Keywords
**NEVER** use these as model attribute names without explicit column mapping:
- `metadata` - conflicts with SQLAlchemy's declarative base

**Solution:**
```python
# WRONG
metadata: Mapped[dict] = mapped_column(JSON)

# CORRECT
metadata_: Mapped[dict] = mapped_column("metadata", JSON)
```

### 3. Code Formatting Standards
- Maximum line length: **100 characters**
- Use Ruff for linting and formatting
- Run before committing:
  ```bash
  poetry run ruff check .
  poetry run ruff format .
  ```

### 4. Import Organization
Order imports as follows (enforced by Ruff I001):
```python
from __future__ import annotations  # 1. Future imports

import asyncio                       # 2. Standard library
import sys
from pathlib import Path

from fastapi import FastAPI          # 3. Third-party
from sqlalchemy import select

from src.api.main import app         # 4. Local imports
from src.core.config import settings
```

### 5. FastAPI Dependency Injection
Using `Depends()` in function defaults is **correct** and expected:
```python
def endpoint(
    session: AsyncSession = Depends(get_db_session),  # This is OK
    user: User = Depends(get_current_user),           # This is OK
):
    pass
```

B008 warnings for this pattern are ignored in `pyproject.toml`.

### 6. F-strings with Complex Expressions
**NEVER** nest quotes incorrectly in f-strings:
```python
# WRONG - syntax error
raise ValueError(f"Error: {", ".join(items)}")

# CORRECT - extract to variable first
joined = ", ".join(items)
raise ValueError(f"Error: {joined}")
```

### 7. Testing Requirements
- All code changes must pass existing tests
- Run tests before committing: `poetry run pytest tests/`
- Ensure no import errors: `poetry run python -c "from src.api.main import app"`

## Pre-Commit Checklist

Before creating a commit, ALWAYS verify:
1. ✅ `poetry run ruff check .` passes
2. ✅ `poetry run ruff format --check .` passes  
3. ✅ `poetry run pytest tests/` passes
4. ✅ All new scripts have proper `sys.path` setup
5. ✅ No SQLAlchemy reserved keywords used as column names
6. ✅ Import order is correct (future → stdlib → third-party → local)

## Common Pitfalls

### Problem: ModuleNotFoundError in Scripts
**Symptom:** `ModuleNotFoundError: No module named 'src'` when running scripts

**Solution:** Add path setup at the top of the script:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Problem: SQLAlchemy InvalidRequestError
**Symptom:** `Attribute name 'metadata' is reserved when using the Declarative API`

**Solution:** Use underscore suffix with explicit column name:
```python
metadata_: Mapped[dict] = mapped_column("metadata", JSON)
```

### Problem: Line Too Long (E501)
**Symptom:** Ruff reports E501 errors

**Solution:** Break into multiple lines:
```python
# Long function call
result = some_function(
    arg1,
    arg2,
    arg3,
)

# Long string
message = (
    "This is a very long string that "
    "would exceed 100 characters if "
    "written on a single line"
)
```

### Problem: Import Sorting (I001)
**Symptom:** Ruff reports I001 import order errors

**Solution:** Run auto-fix: `poetry run ruff check --fix .`

## CI/CD Considerations

Scripts must work in GitHub Actions environments where:
- Working directory may vary
- No interactive input possible
- Dependencies installed via `poetry install`
- Python path not automatically configured

Always test scripts with: `poetry run python scripts/your_script.py`

## Agent-Specific Instructions

### For BMAD Agents
When activated as Dev, Architect, or other technical agents:
1. Review this document before making code changes
2. Apply all rules in the Pre-Commit Checklist
3. If creating new scripts, use the script template with path setup
4. Test imports independently: `poetry run python -c "import src.module"`

### For GitHub Copilot
This file is automatically read as workspace context. Follow all rules when:
- Generating new code
- Refactoring existing code
- Creating scripts or utilities
- Fixing linting errors

## Questions?

If uncertain about any rule, check:
1. `docs/architecture/coding-standards.md` - General coding standards
2. `pyproject.toml` - Ruff configuration and ignored rules
3. Existing codebase patterns in `src/` and `tests/`
