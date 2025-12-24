# Pre-Commit Checklist

Use this checklist before every commit to ensure code quality.

## Required Checks

### 1. Linting
```bash
poetry run ruff check .
```
**Status:** ⬜ Not Run | ✅ Passed | ❌ Failed

**If failed:** Run `poetry run ruff check --fix .` to auto-fix

---

### 2. Code Formatting
```bash
poetry run ruff format --check .
```
**Status:** ⬜ Not Run | ✅ Passed | ❌ Failed

**If failed:** Run `poetry run ruff format .` to auto-format

---

### 3. Tests
```bash
poetry run pytest tests/
```
**Status:** ⬜ Not Run | ✅ Passed | ❌ Failed

**If failed:** Fix failing tests before committing

---

### 4. Module Import Check (for new scripts)
```bash
poetry run python scripts/your_new_script.py
```
**Status:** ⬜ Not Applicable | ✅ Works | ❌ Failed

**If failed:** Add sys.path setup (see scripts/_template.py)

---

## Additional Checks (if applicable)

### 5. Database Migration (if models changed)
```bash
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```
**Status:** ⬜ Not Applicable | ✅ Done

---

### 6. OpenAPI Schema (if API routes changed)
```bash
poetry run python scripts/export_openapi.py
git add docs/api/openapi.json
```
**Status:** ⬜ Not Applicable | ✅ Done

---

## Common Issues & Solutions

### Issue: ModuleNotFoundError in scripts
**Solution:** Add to script header:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Import order (I001)
**Solution:** Run `poetry run ruff check --fix .`

### Issue: Line too long (E501)
**Solution:** Break lines at 100 chars using parentheses

### Issue: SQLAlchemy metadata error
**Solution:** Use `metadata_: Mapped[dict] = mapped_column("metadata", JSON)`

---

## Quick Fix Commands

```bash
# Fix all auto-fixable issues
poetry run ruff check --fix .

# Format all code
poetry run ruff format .

# Run all checks in sequence
poetry run ruff check . && \
poetry run ruff format --check . && \
poetry run pytest tests/ && \
echo "✅ All checks passed!"
```

---

## Commit Template

After all checks pass:

```bash
git add -A
git commit -m "Brief description of changes

- Detail 1
- Detail 2
- Detail 3"
git push
```

---

## References

- [Coding Standards](docs/architecture/coding-standards.md)
- [AI Development Guidelines](docs/architecture/ai-development-guidelines.md)
- [Script Template](scripts/_template.py)
