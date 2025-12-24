# MicroCred GenAI Monorepo

## Prerequisites
- Python 3.12.2
- Poetry 1.8.x
- Docker & Docker Compose

## Bootstrap
1. Install dependencies:
   ```bash
   poetry install
   ```
2. Copy environment template and supply secrets:
   ```bash
   cp .env.example .env
   ```
3. Launch backing services along with API and worker:
   ```bash
   docker compose up --build
   ```
4. Run database migrations to install reference data (roles, question templates):
   ```bash
   poetry run alembic upgrade head
   ```

## Local Development
- Run the API without Docker:
  ```bash
  poetry run uvicorn src.api.main:app --reload
  ```
- Start the worker:
  ```bash
  poetry run python -m src.workers.worker
  ```
- Check available tracks:
  ```bash
  curl http://localhost:8000/tracks
  ```
- Start/resume an assessment (requires JWT from `/tests/utils.py` helper or issue_smoke_token):
  ```bash
  curl -H "Authorization: Bearer <token>" \
       -X POST http://localhost:8000/assessments/start \
       -d '{"role_slug": "backend-engineer"}'
  ```
- Execute linting and tests:
  ```bash
  scripts/run-tests.sh
  ```
- Refresh OpenAPI schema:
  ```bash
  poetry run python scripts/export_openapi.py
  ```

## Project Structure
Key directories follow the architecture guide:
- `src/api`: FastAPI application and route definitions.
- `src/workers`: RQ worker entrypoint and job handlers.
- `src/domain`: Shared domain models between services.
- `src/infrastructure`: Repositories and data access abstractions.
  - `udemy_courses.csv`: Sample dataset (3,684 courses) for recommendations and RAG features.
- `tests`: Pytest-based unit and integration suites.

## Development Guidelines

### For Developers
- **Coding Standards**: See [docs/architecture/coding-standards.md](docs/architecture/coding-standards.md)
- **Script Development**: Always add path setup to scripts (see coding standards)
- **Quality Gates**: Run `poetry run ruff check .` and `poetry run pytest` before committing

### For AI Agents & Copilot
- **Primary Guide**: [docs/architecture/ai-development-guidelines.md](docs/architecture/ai-development-guidelines.md)
- **Quick Reference**: [.github/agents/python-rules.md](.github/agents/python-rules.md)
- **Critical**: All scripts must include `sys.path` setup for module imports

### Before Committing
```bash
# Run quality checks
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/

# If all pass
git add -A
git commit -m "your message"
git push
```
