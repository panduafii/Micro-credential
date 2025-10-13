# Technical Assumptions

## Repository Structure: Monorepo
Single FastAPI-centric repository containing API, workers, shared domain models, and infrastructure scripts (Docker, IaC). Keeps async pipeline cohesive and accelerates iteration within the four-week MVP window.

## Service Architecture
Modular monolith using FastAPI for HTTP routes and Redis-backed workers (RQ or Celery) for GPT essay scoring and RAG retrieval. Workers share ORM access and configuration modules, enabling independent horizontal scaling of API and worker containers without microservice overhead.

## Testing Requirements
Adopt Unit + Integration coverage. Unit tests cover rule scorers, fusion logic, track routing, and RAG query builders. Integration tests exercise end-to-end async pipeline with local Postgres/Redis/Chroma containers. Contract tests mock OpenAI interactions to stay within budget. Full UI E2E deferred until companion front-end exists.

## Additional Technical Assumptions and Requests
- Language/Framework: Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2.
- Queue: Redis-backed RQ (or Celery) with exponential backoff and dead-letter queues for failed jobs.
- Vector Store: Chroma or PGVector managed with migrations; embeddings generated via OpenAI `text-embedding-3-small`.
- Deployment: Docker Compose for local dev; container images target AWS ECS Fargate (or similar) with Terraform/IaC stubs for future scaling.
- Secrets: Environment variables locally; parameter store/secret manager for production; rotate OpenAI keys monthly.
- Observability: OpenTelemetry-compatible logging, Prometheus exporters for queue depth/latency; Grafana dashboard skeleton.
- Role catalogs and question pools stored in Postgres with versioned seeds for track-based question selection.
- Security: JWT auth with role claims, HTTPS enforcement, rate limiting (token bucket), and audit logging on admin actions.
- Cost Control: Batch GPT essay scoring with low temperature; embed catalog refresh scheduled weekly to stay within spend limits.
