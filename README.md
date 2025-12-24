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
4. Run database migrations (placeholder):
   ```bash
   poetry run alembic upgrade head  # TODO: implement migrations
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
- `tests`: Pytest-based unit and integration suites.

