# Coding Standards
- **Core Standards:**  
  - Languages & Runtimes: Python 3.12.2 only.  
  - Style & Linting: Ruff (with embedded Black) as the single formatting/linting tool.  
  - Test Organization: Unit tests in `tests/unit/test_<module>.py`; integration tests in `tests/integration/test_<feature>.py`.
- **Critical Rules:**  
  - Use `structlog.get_logger()` for all logging; never use `print()` or bare `logging` calls.  
  - Access Postgres exclusively through repository/unit-of-work abstractions—no direct session usage in API routes or workers.  
  - Keep async code non-blocking; long-running or blocking operations must run via `await` or executor helpers.
