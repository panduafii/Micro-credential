# BMAD Agent Context: Python Development Rules

**AUTO-LOAD:** This file is automatically loaded when BMAD agents are activated for Python development tasks.

## CRITICAL RULES - ALWAYS APPLY

### 1. Script Module Import Setup
**EVERY** script in `scripts/` directory **MUST** start with:

```python
from __future__ import annotations

import sys
from pathlib import Path

# REQUIRED: Enable src package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.module import something  # Now works
```

**Violation Impact:** CI pipeline fails with `ModuleNotFoundError: No module named 'src'`

### 2. SQLAlchemy Reserved Names
**NEVER** use `metadata` as column name. Use this pattern:
```python
metadata_: Mapped[dict] = mapped_column("metadata", JSON)
```

### 3. Code Quality Gates - Run Before Commit
```bash
poetry run ruff check .           # Linting
poetry run ruff format --check .  # Format check
poetry run pytest tests/          # Tests
```

### 4. Line Length Limit
- Maximum: **100 characters**
- Use parentheses for multi-line continuation

### 5. Import Order (Ruff I001)
```python
from __future__ import annotations  # 1. Future

import sys                           # 2. Stdlib
from pathlib import Path

from fastapi import FastAPI          # 3. Third-party

from src.api import routes           # 4. Local
```

## Agent Workflow

1. **Before Writing Code:**
   - Check `docs/architecture/coding-standards.md`
   - Review `docs/architecture/ai-development-guidelines.md`
   - Use `scripts/_template.py` for new scripts

2. **After Writing Code:**
   - Run: `poetry run ruff check --fix .`
   - Run: `poetry run ruff format .`
   - Test imports: `poetry run python -c "from src.api.main import app"`
   - Run: `poetry run pytest tests/`

3. **Before Commit:**
   - Verify all checks pass
   - Ensure no syntax errors
   - Check CI will succeed

## Quick References

- Template: `scripts/_template.py`
- Checklist: `docs/PRE-COMMIT-CHECKLIST.md`
- Standards: `docs/architecture/coding-standards.md`
- AI Guide: `docs/architecture/ai-development-guidelines.md`

## Common Fixes

```bash
# Auto-fix linting issues
poetry run ruff check --fix .

# Auto-format code
poetry run ruff format .

# Verify script imports work
poetry run python scripts/your_script.py
```

## Ignored Warnings
- **B008**: FastAPI `Depends()` in function defaults (intentional pattern)

## Questions?
Read: `docs/architecture/ai-development-guidelines.md` for detailed explanations.
