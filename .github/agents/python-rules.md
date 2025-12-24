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

## Line Length
- Max: 100 characters
- Use parentheses for implicit line continuation

## FastAPI Patterns
- `Depends()` in defaults is OK (B008 ignored)
- This is standard FastAPI DI pattern

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

## Agent Activation Checklist

When BMAD Dev agent is activated:
- [ ] Read `docs/architecture/ai-development-guidelines.md`
- [ ] Check `docs/architecture/coding-standards.md`
- [ ] Verify all scripts have path setup
- [ ] Run quality gates before commit
- [ ] Test in isolation: `poetry run python script.py`
