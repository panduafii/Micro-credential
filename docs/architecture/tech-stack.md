# Tech Stack

## Cloud Infrastructure
- **Provider:** Railway (primary) or Render; AWS ECS Fargate documented as a future upgrade path when budget allows.
- **Key Services:** Railway/Render app services for API and worker, managed Postgres, managed Redis, platform TLS, metrics dashboards.
- **Regions:** Railway us-east deployment (default); document switch path if latency requires another region.

## Technology Stack Table
| Category               | Technology                                 | Version      | Purpose                                  | Rationale                                                                 |
| ---------------------- | ------------------------------------------- | ------------ | ---------------------------------------- | ------------------------------------------------------------------------- |
| Language               | Python                                      | 3.12.2       | Unified runtime                          | Matches PRD preference; modern async features.                            |
| Backend Framework      | FastAPI                                     | 0.110.2      | HTTP API server                          | High-performance async with auto OpenAPI docs.                            |
| Data Validation        | Pydantic                                    | 2.8.2        | Request/response validation              | Native FastAPI integration.                                               |
| ORM                    | SQLAlchemy (async)                          | 2.0.25       | Data access layer                        | Mature ORM with async support.                                            |
| Migrations             | Alembic                                     | 1.13.2       | Database migrations                      | Standard with SQLAlchemy.                                                 |
| Background Jobs        | RQ                                          | 1.15.1       | Redis-backed job processing              | Lightweight and aligns with PRD.                                          |
| Scheduler              | rq-scheduler                                | 0.12.0       | Scheduled jobs                           | Refresh embeddings and cleanup tasks.                                     |
| AI Model               | OpenAI gpt-3.5-turbo                        | 2024-05-01   | Essay scoring & explanations             | Cost-effective balance for MVP.                                           |
| RAG Framework          | LangChain                                   | 0.1.23       | RAG pipeline orchestration               | Compatible with Chroma and OpenAI.                                        |
| Embedding Model        | sentence-transformers all-MiniLM-L6-v2      | 2.2.2        | Local embedding generation               | Low-cost embedding per Haystack tutorial.                                 |
| Collaborative Filtering| scikit-learn                                | 1.5.2        | KNN recommendation blending              | Implements KNN as referenced in research.                                 |
| Database               | PostgreSQL (managed)                        | 15.5         | System of record                         | Aligns with PRD technical assumptions.                                    |
| Vector Store           | ChromaDB                                    | 0.4.24       | Semantic search storage                  | Open-source, deployable alongside Postgres.                               |
| Cache/Queue            | Redis                                       | 7.2 managed  | Queue + caching                          | Powers RQ jobs and optional caching.                                      |
| Containerization       | Docker                                      | 25.0.5       | Dev/prod parity                          | Standard container tooling.                                               |
| Hosting                | Railway / Render                            | 2024 stack   | Deployment platform                      | Provides free-tier hosting for API + workers.                             |
| CI/CD                  | GitHub Actions                              | 2024 runner  | Build, test, deploy                      | Integrates with repository workflows.                                     |
| Logging                | structlog                                   | 24.1.0       | Structured logging                       | Produces audit-ready JSON logs.                                           |
| Testing                | pytest                                      | 8.2.1        | Test runner                              | Async-friendly testing.                                                   |
| Linting                | ruff                                        | 0.5.7        | Lint + format                            | Fast linting and formatting.                                              |
| Formatting             | black (via ruff)                            | 24.8.0       | Code formatting                          | Consistent style with minimal config.                                     |
