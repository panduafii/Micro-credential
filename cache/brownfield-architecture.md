# Micro-Credential Assessment Backend – Brownfield Architecture

## 1. Introduction
- **Purpose**: Capture the present-state architecture for the Micro-Credential Assessment backend so future agents understand what exists, what is stubbed out, and where to focus when implementing new work.
- **Repository Reality**: This workspace currently contains product documentation only (`docs/prd/mvp-microcredential-backend-prd.md`). There is no application source tree (`src/`), dependency manifest, or infrastructure code in this repo. All implementation details in this document describe the intended system as defined in the PRD and call out the absence of concrete code where applicable.
- **Documentation Standard**: Structured using a C4-inspired approach (Context, Container, Component, Sequence) with explicit brownfield notes about actual vs. planned state.

## 2. Executive Summary
- The backend platform described in the PRD targets FastAPI (Python 3.11), PostgreSQL, JWT auth, GPT-3.5–assisted essay scoring via an async queue, and rule-based recommendation lookup.
- No runtime artifacts exist in this repository today—key modules (auth, assessment engine, scoring normalization, GPT integration, recommendations) are unimplemented.
- Critical upcoming enhancement is semantic search with RAG/ChromaDB; integration points need to be reserved in the recommendation pipeline even though the baseline implementation is absent.

## 3. Context View (C4 Level 1)
- **Primary System**: Micro-Credential Assessment Backend (not yet implemented).
- **Actors**:
  - IT Student / Candidate: Initiates assessments, submits answers, retrieves skill profiles.
  - Academic Advisor / Coach: Reads assessment outcomes and recommendations.
  - Partner Frontend / LMS Integrations: Consume REST APIs for assessment lifecycle and recommendations.
  - OpenAI GPT-3.5 API: Scores essay responses and generates rationale text.
- **Interactions**:
  - RESTful calls from clients to backend (authentication, assessment, profile, recommendations).
  - Backend-to-OpenAI requests for essay scoring (async queue with synchronous fallback).
  - Backend-to-PostgreSQL for persistence.
- **Reality Check**: The above flows are specified only in the PRD; no FastAPI app or OpenAI integration code currently exists in this repository.

## 4. Container View (C4 Level 2)
| Container | Responsibility | Technology (Planned) | Current State |
| --- | --- | --- | --- |
| API Service | Hosts REST endpoints for auth, assessment lifecycle, profiles, recommendations | FastAPI (Python 3.11) + Uvicorn | Not present; no `src/main.py` or router modules in repo |
| Async Worker | Processes GPT scoring jobs, retries failures, normalizes scores | FastAPI background tasks or lightweight queue (e.g., Dramatiq/RQ) | Queue not provisioned; no worker scripts, configs, or task definitions |
| Database | Stores users, assessments, answers, scores, recommendations | PostgreSQL via SQLAlchemy/Alembic | No schema files or migration scripts; DB layer absent |
| Recommendation Lookup | Resolves course suggestions by role, score band, interests | SQL tables plus lookup logic | Tables and services missing; only PRD description |
| Observability Stack | Logging, metrics, health checks | Structured logging + basic metrics (Prometheus-ready) | No instrumentation or config in codebase |
| External AI Service | Essay scoring and rationale generation | OpenAI GPT-3.5-turbo | Integration not yet configured; no API client code or prompt definitions |

## 5. Component View Highlights (C4 Level 3)
Even though components are unimplemented, the PRD outlines the modules that must exist. Highlighting the most critical:

- **Authentication & Session Management**
  - Expected Components: JWT issuance, refresh tokens, rate limiting.
  - Reality: No auth package or security utilities in this repo; agents must scaffold from scratch.

- **Assessment Orchestration**
  - Expected Flow: `/assessments/start`, `/next`, `/answer`, `/complete`.
  - Planned Modules: Router layer, assessment service orchestrator, repositories for session/question storage.
  - Reality: No routers, services, or schemas exist; question bank is not checked into this repository.

- **Scoring & Normalization**
  - Expected Logic: Rule-based MCQ grading, GPT essay scoring, normalization to 0–100 overall score with domain breakdown.
  - Critical Complexity: Combining async GPT results with deterministic MCQ scoring; fallback path when async queue lags.
  - Reality: No scoring modules; normalization weights and score-band definitions live only in the PRD narrative.

- **GPT Integration & Async Queue**
  - Expected Components: Task enqueue function, worker consumer, error handling, prompt templates, usage tracking.
  - Reality: No queue configuration (Redis, database-backed, etc.), no prompt files or integration wrappers.

- **Recommendation Service**
  - Expected Components: Lookup table keyed by `(role, scoreBand, interest)`, SQL queries, API response formatting, rationale generator.
  - Reality: Lookup data and SQL queries absent; no code to generate user-facing rationales.

- **Observability & Reliability**
  - Expected Components: Structured logging, metrics counters (e.g., GPT latency), health endpoints.
  - Reality: No logging configuration or middleware in place.

## 6. Sequence View (Assessment Session, Planned vs. Actual)
1. **User Authenticates** → `POST /auth/login` issues JWT, refresh token.  
   - *Actual State*: Auth endpoints not implemented.
2. **Assessment Start** → `POST /assessments/start` seeds session, returns first question.  
   - *Actual State*: API layer and session persistence absent.
3. **Question Loop** → `GET /assessments/{id}/next` and `POST /assessments/{id}/answer`.  
   - MCQ answers scored immediately; essay answers enqueued for GPT.  
   - *Actual State*: No router/service to manage progression; queue not built.
4. **Completion** → `POST /assessments/{id}/complete` waits for scoring, aggregates profile.  
   - *Actual State*: Aggregation logic not implemented; profile model missing.
5. **Profile & Recommendations** → `GET /profiles/{id}` and `GET /recommendations?assessmentId=...`.  
   - Should return structured profile + 2–3 course suggestions with rationale.  
   - *Actual State*: Endpoints, serializers, and data queries absent.

## 7. Data Model Reality
- PRD prescribes tables for `users`, `assessments`, `questions`, `answers`, `profiles`, `recommendations`.
- No SQLAlchemy models, Alembic migrations, or seed scripts exist in this repository.
- Recommendation lookup table (role + score band + interest) is conceptual only—no seed data or schema.

## 8. Technical Debt & Gaps
- **Complete Lack of Implementation**: Core modules (auth, assessment, scoring, GPT, recommendations) do not exist yet.
- **Queue Strategy Undefined**: Choice of background processing framework and persistence is undecided; design must balance async throughput with synchronous fallback constraints.
- **Scoring Normalization**: Weights, band definitions, and conflict resolution (e.g., missing GPT scores) live only in documentation—need concrete constants and test coverage.
- **Error Handling & Observability**: No middleware, logging, or monitoring scaffolding; reliability targets (≤500 ms p95, retry policies) cannot be enforced until instrumentation exists.

## 9. Development & Deployment Notes
- **Local Setup**: No `requirements.txt`, `pyproject.toml`, or Makefile in this repository. Agents must establish the Python environment from scratch (suggest starting with FastAPI, SQLAlchemy, Pydantic, OpenAI SDK).
- **Configuration**: `.env` handling, secret management, and environment variable mapping are unspecified. Document once implemented.
- **Deployment**: PRD suggests Render/Railway, but no Terraform, Dockerfile, or CI/CD pipeline exists.

## 10. Testing Reality
- No test suite (unit, integration, or e2e) is present.
- Reliability expectations (≥95% uptime, retry handling, GPT circuit breakers) are unverified and unenforced.
- Future agents should create tests around scoring normalization, async queue resilience, and recommendation correctness as features are implemented.

## 11. Upcoming Enhancement: Semantic Search (RAG/ChromaDB)
- Enhancement Goal: Integrate vector-based semantic search into the recommendation pipeline using ChromaDB, enriching the rule-based lookup with embeddings-driven matches.
- Current Readiness: There is no scaffolding for embeddings generation, vector store clients, or hybrid ranking logic.
- Recommended Preparation:
  - Reserve extension points in the recommendation service to call out to an embeddings layer.
  - Plan data ingestion scripts for course content embeddings.
  - Design cache/latency strategy so RAG augmentation does not degrade the ≤500 ms p95 target.

## 12. Recommendations for Next Actions
1. Scaffold the FastAPI application structure (`src/`) with routers, services, repositories, and DTOs aligned to the PRD contracts.
2. Implement database schema via SQLAlchemy + Alembic; seed the recommendation lookup table to support MVP endpoints.
3. Establish GPT integration with an async task runner, explicit retry/fallback policies, and prompt templates under version control.
4. Introduce observability basics (structured logging, metrics hooks) and automated tests covering scoring, queue behavior, and recommendation accuracy.
5. Plan the semantic search integration by defining vector store schemas and API extension points before business logic becomes tightly coupled.
