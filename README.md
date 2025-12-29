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
- `docs/stories`: Implementation documentation for each user story.

## API Documentation

### SwaggerUI
After starting the API, access interactive documentation at:
- **SwaggerUI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Available Endpoints (Epic 1)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | - | Health check |
| GET | `/tracks` | - | List all active tracks |
| GET | `/tracks/{slug}` | - | Get track by slug |
| POST | `/tracks` | Admin | Create track |
| PATCH | `/tracks/{slug}` | Admin | Update track |
| DELETE | `/tracks/{slug}` | Admin | Soft-delete track |
| GET | `/questions` | - | List questions (filter by role_slug) |
| GET | `/questions/{id}` | - | Get question by ID |
| POST | `/questions` | Admin | Create question |
| PATCH | `/questions/{id}` | Admin | Update question (versioned) |
| DELETE | `/questions/{id}` | Admin | Soft-delete question |
| POST | `/assessments/start` | Student | Start/resume assessment |
| POST | `/assessments/{id}/submit` | Student | Submit for scoring |
| GET | `/assessments/{id}/status` | Student | Get progress status |
| POST | `/assessments/{id}/webhook` | Student | Register webhook URL |

### Generate Test Token
```python
from src.core.auth import create_access_token

# Student token
token = create_access_token("test-user", roles=["student"])

# Admin token
token = create_access_token("admin-user", roles=["admin"])
```

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

## Implementation Progress

### Epic 1: Role-Gated Assessment Foundation ✅
- [x] Story 1.1: Monorepo Baseline and Auth Skeleton
- [x] Story 1.2: Track Catalog Management
- [x] Story 1.3: Question Bank CRUD and Versioning
- [x] Story 1.4: Role-Gated Assessment Start

### Epic 2: Async Scoring and Persistence Backbone ✅
- [x] Story 2.1: Submission Finalization and Rule Scoring
- [x] Story 2.2: GPT Essay Scoring Worker
- [x] Story 2.3: Status Polling, Webhooks, and Idempotency

### Epic 3: Recommendations, Transparency, and Feedback Loop 🔜
- [ ] Story 3.1: RAG-Powered Credential Recommendations
- [ ] Story 3.2: Transparency Dashboard
- [ ] Story 3.3: Feedback Collection and Analytics

