# Coding Standards
- **Core Standards:**  
  - Languages & Runtimes: Python 3.12.2 only.  
  - Style & Linting: Ruff (with embedded Black) as the single formatting/linting tool.  
  - Test Organization: Unit tests in `tests/unit/test_<module>.py`; integration tests in `tests/integration/test_<feature>.py`.

- **Critical Rules:**  
  - Use `structlog.get_logger()` for all logging; never use `print()` or bare `logging` calls.  
  - Access Postgres exclusively through repository/unit-of-work abstractions—no direct session usage in API routes or workers.  
  - Keep async code non-blocking; long-running or blocking operations must run via `await` or executor helpers.

## Python Module Import Standards

### Scripts Directory
All standalone Python scripts in the `scripts/` directory **MUST** include path setup to allow importing the `src` package:

```python
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.module import something  # Now this works
```

**Rationale:** Scripts run independently and may be executed from different working directories (local dev, CI, containers). Explicit path setup ensures consistent imports.

### Import Order
Follow this import order (enforced by Ruff I001):
1. Future imports (`from __future__ import annotations`)
2. Standard library imports
3. Third-party library imports  
4. Local application imports (`from src.*`)

Separate each group with a blank line.

### Reserved Attributes
- **Never** use `metadata` as a SQLAlchemy model attribute name - it conflicts with declarative base
- Use `metadata_` with explicit column name: `metadata_: Mapped[dict] = mapped_column("metadata", JSON)`

### Line Length
- Maximum line length: **100 characters**
- Break long lines using:
  - Parentheses for implicit continuation
  - Multi-line function calls
  - String concatenation with parentheses

### FastAPI Patterns
- Using `Depends()` in function default arguments is acceptable (ignore B008 warning)
- This is the standard FastAPI dependency injection pattern
