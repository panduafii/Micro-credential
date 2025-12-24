# AI-Powered Micro-Credential Assessment Backend Product Requirements Document (PRD)

## Goals and Background Context

### Goals
- Deliver an async-first FastAPI backend that completes hybrid (rule + GPT) scoring within targeted latency windows.
- Provide RAG-backed micro-credential recommendations that advisors and students can immediately act on.
- Ship an auditable MVP foundation that captures assessment, scoring, and recommendation data for future analytics.
- Ensure explainable outputs with traceable sources so stakeholders can validate AI-driven decisions.

### Problem Statement
Universities and credential providers rely on static assessments and generic advising, leaving students without actionable learning paths and advisors without defensible recommendations. Discovery workshops with our academic partner revealed that advisors currently spend 6–10 days synthesizing results manually, and 80% of surveyed students reported generic course suggestions that did not match their skill interests. This PRD delivers an AI-powered backend that collects hybrid responses, scores them credibly, and recommends micro-credentials with transparent sources so institutions can shorten guidance cycles to <48 hours while increasing student trust.

### Background Context
The AI-powered Micro-Credential Assessment Backend serves universities and credential providers that need personalized, defensible learning guidance. Current static assessments fail to connect demonstrated skills to actionable micro-credentials, eroding advisor trust and student momentum. The four-week MVP focuses on a 10-question hybrid assessment (three theoretical, three essay, and four profile/interest items) so rule-based scoring can deliver instant feedback while GPT handles nuanced essay evaluation. RAG is mandatory to align recommendations with catalog context, and Redis-backed async processing keeps throughput high without overcomplicating operations. By pairing deterministic scoring with explainable AI summaries, the service gives advisors and learners confidence in guidance while keeping infrastructure lean and extensible.

### Target Users

| User Type                         | Needs                                                                       | Success Criteria                                         |
| --------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Students (Primary)**            | Quick, accurate skill evaluation and personalized micro-credential guidance | Receives clear, relevant recommendations with confidence |
| **Academic Advisors (Secondary)** | Reliable AI-based recommendation to support learning path decisions         | AI suggestions are explainable and context-matched       |
| **Developers / Admins**           | Scalable, low-maintenance backend integration                               | API endpoints are stable, documented, and extensible     |

### User Research & Insights
- **First Principles Workshop (2025-10-11):** Facilitated session with advisors highlighted the need for asynchronous scoring, RAG-backed recommendations, and a 10-minute completion window (see `docs/brainstorming-session-results.md`).
- **Advisor Interviews (n=5):** Surface pain of manual spreadsheet tracking and delayed recommendations, with a target to reduce turnaround to <2 days.
- **Student Feedback (pilot cohort n=12):** Reported frustration with generic advice; 70% requested personalized micro-credential suggestions tied to their interests.
- **Key Insight:** Mandatory RAG integration is necessary because a limited question bank alone cannot deliver trusted contextual recommendations.

### Competitive & Market Context
- Traditional LMS assessments (e.g., Canvas quizzes) focus on grading but lack personalized credential mapping.
- Commercial advising tools prioritize dashboards over AI-backed recommendations, leaving gaps in explainability and asynchronous handling.
- Differentiation: This backend combines rule scoring, GPT evaluation, and RAG with transparent traces, enabling institutions to launch contextual guidance without building full-stack systems.

### Business Goals & Success Metrics

| Objective                                          | Success Metric                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| Deliver reliable async API for assessment flow     | Average latency < 500 ms for rule-based scoring; < 10 s for GPT tasks  |
| Ensure recommendation credibility and transparency | ≥ 85% relevance in RAG validation tests with explainable context trace |
| Guarantee operational reliability                  | ≥ 99% uptime and successful async queue completion rate                |
| Validate user satisfaction and adoption            | ≥ 70% student satisfaction, ≥ 80% advisor trust in recommendations     |

### Impact & Differentiation Summary
- Reduce advisor turnaround time from 6–10 days to <48 hours by automating scoring and recommendation assembly.
- Increase advisor trust scores to ≥80% through explainable RAG traces.
- Deliver personalized recommendations aligned to selected roles, addressing the 70% student demand for role-specific guidance captured in pilot feedback.
- Provide an extensible foundation for future adaptive learning features without overexpanding MVP scope.

### MVP Scope

**In Scope**
- Async FastAPI backend with hybrid (rule + GPT) scoring logic.
- RAG-powered recommendations sourced from curated micro-credential catalog with traceable snippets.
- 3 theoretical, 3 essay, and 4 profile/interest questions tailored to a selected role.
- Redis queue, worker processes, and degraded-mode fallbacks for resilience.
- Postgres persistence, Chroma (or PGVector) embeddings, and audit logging.
- Basic admin endpoints for track/question/catalog management plus metrics collection.

**Out of Scope / Deferred**
- Advanced semantic analytics dashboards beyond basic health metrics.
- Dynamic advisor-facing question authoring UI (manual data loading for MVP).
- Adaptive course orchestration and continuous learning loops.
- Mobile-native apps; MVP relies on responsive web experiences.

### Design Philosophy
- **Async-first:** Handles concurrent assessments without blocking.
- **Explainable AI:** GPT output is backed by RAG retrieval sources surfaced to end users.
- **Scalable Foundation:** Modular monolith enables future services without premature complexity.

### Rationale Recap
- Asynchronous architecture ensures fast, scalable student processing within performance targets.
- Role-driven RAG recommendations build advisor confidence and align with stakeholder feedback.
- Balanced question composition (3/3/4) achieves both accuracy and personalization for the MVP.
- Four-week delivery plan matches resource constraints outlined in brainstorming sessions.

### Change Log
| Date | Version | Description | Author |
| 2025-10-13 | 0.1 | Initial PRD draft synthesized from brainstorming outputs | John (PM) |
| 2025-10-14 | 0.2 | Added research insights, UX flows, validation plan, and cross-functional requirements | John (PM) |

## Requirements

### Functional Requirements
- FR1: The `POST /api/v1/assessments/start` endpoint must require the student to choose a target role/track (e.g., “Backend Engineer”, “Data Analyst”) and return a 10-question bundle tailored to that role from the active bank within 400 ms p95.
- FR2: The system must expose `/api/v1/tracks` so students can preview available roles, associated skill focus, and question mix before starting an assessment.
- FR3: The system must accept partial response batches and persist them idempotently so students can resume assessments without data loss.
- FR4: On final submission the backend must synchronously compute rule-based scores for theoretical and profile questions, persist them to the `rule_scores` table, and enqueue RQ jobs (`score_essay`, `generate_recommendations`) with a retry cap of three attempts.
- FR5: Essay-scoring workers must evaluate each essay via GPT against rubric dimensions (clarity, accuracy, coherence) and save structured scores plus feedback traces into the `essay_scores` table.
- FR6: The RAG service must build a retrieval query using the selected role, profile signals, and essay insights, fetch Top-K credentials from Chroma, and persist ranked items with source snippets.
- FR7: The fusion service must combine role context, rule scores, essay insights, and RAG output into a single recommendation summary while flagging degraded results when fallbacks were used.
- FR8: Students must be able to poll `/api/v1/assessments/{id}/status` and `/api/v1/assessments/{id}/result`, and receive webhooks (when configured) when processing completes.
- FR9: Admins must manage the question bank, credential catalog, track definitions, and RAG index through secured endpoints with full audit logging.
- FR10: The system must capture user/advisor feedback on recommendation relevance and perceived fit for the selected role to inform future tuning.

### Non-Functional Requirements
- NFR1: Average synchronous endpoint latency must stay <500 ms p95; async GPT completion must stay <10 s p95; RAG retrieval <1.5 s average.
- NFR2: The system must handle ≥100 concurrent assessments by horizontally scaling API and worker pods without data loss.
- NFR3: Redis queues must tolerate worker restarts with exactly-once processing guarantees enforced through job status locking.
- NFR4: Postgres must encrypt PII at rest and ensure referential integrity across `assessments`, `assessment_question_snapshots`, `assessment_responses`, `rule_scores`, `essay_scores`, `recommendations`, and track selections in `role_catalog`.
- NFR5: Every recommendation must include traceable sources so advisors can validate AI output.
- NFR6: Observability must capture structured logs, queue depth, latency histograms, and inference token counts for SLO tracking, segmented by role/track.
- NFR7: The system must provide a static recommendation fallback when GPT or RAG paths fail while logging the degraded mode and affected role/track.

## MVP Validation Plan
- **Pilot Cohort:** Run the MVP with at least 30 students and 5 advisors across two academic programs during Week 4, capturing quantitative metrics (latency, recommendation acceptance) and qualitative feedback.
- **Success Criteria:** Achieve ≥70% student satisfaction, ≥80% advisor trust rating, and ≤48-hour turnaround per assessment; degraded-mode incidents must remain <10% of total runs.
- **Feedback Loop:** Collect advisor/student feedback via in-product forms (FR10) and conduct follow-up interviews; feed insights into backlog grooming for post-MVP iterations.
- **Analytics & Instrumentation:** Instrument metrics dashboard to track queue depth and failure rates; review daily during pilot.
- **Go/No-Go Decision:** If success criteria met and no Sev-1 incidents outstanding, proceed to broader rollout planning; otherwise schedule remediation sprint focused on identified bottlenecks (GPT latency, RAG accuracy, or UX friction).

## User Experience Requirements

### User Journeys & Flows
- **Student Path (Entry → Exit):** Select role/track → preview question composition → complete hybrid assessment (supporting save/resume) → receive async status updates → review results and provide feedback. Edge cases include expired assessments (prompt to restart) and degraded recommendations (labelled with fallback messaging).
- **Advisor Path:** Authenticate with advisor role → view cohort dashboard → inspect individual student recommendations with RAG traces → record accept/reject feedback → flag degraded cases for follow-up. Handles scenario where recommendations are pending by surfacing in-progress status.
- **Admin Path:** Login with admin role → manage tracks/questions/catalog → monitor system health metrics → trigger embedding rebuilds. Includes guardrails for publishing changes while jobs are running.

### Usability Requirements
- Accessibility target WCAG AA; leverage semantic HTML, keyboard navigation, and high-contrast defaults.
- Responsive web layout optimized for desktop and tablet; critical student/advisor views scale to mobile.
- Loading states communicate async progress (e.g., “Scoring essays — up to 10 seconds remaining”).
- Feedback prompts after recommendation review capture qualitative insights with minimal input friction.

### Error States & Recovery
- Assessment submission failures provide retry guidance and contact path; auto-resume if partial data saved.
- Queue or GPT/RAG outages trigger degraded-mode banners with timestamp and expected resolution.
- Admin actions validate dependencies (e.g., cannot delete active question without replacement) and log errors with remediation steps.
- Webhook or notification failures surface in ops dashboard with ability to resend.

### UI Design Goals
Deliver lightweight, role-aware web dashboards that surface assessment progress, scoring breakdowns, and recommendation rationales so students, advisors, and admins can trust backend outputs without dense configuration screens.

### Key Interaction Paradigms
- Role-gated navigation (student vs advisor vs admin) with JWT SSO to surface only relevant data.
- Async-status indicators translating backend job states into plain-language progress checkpoints.
- Recommendation cards exposing RAG source snippets alongside summary scores to uphold transparency.
- Minimal data entry; focus on viewing results, acknowledging recommendations, and capturing feedback.

### Core Screens and Views
- Student Assessment Status and Result page (progress, scores, recommendation summary, feedback action).
- Advisor Recommendation Review console (per-student history, rationale, accept/reject feedback).
- Admin Catalog and Question Manager (track definitions, question bank activation toggles, index rebuild triggers).
- Operations Health dashboard (queue depth, latency metrics, degraded-mode alerts).

### Accessibility: WCAG AA (target)
Commit to WCAG AA conformance so internal dashboards can graduate to student-facing experiences without rework; assume standard responsive web controls.

### Branding
Neutral light theme with sans-serif typography and placeholders for institutional logos; finalize palette once university partner is confirmed.

### Target Device and Platforms: Web Responsive
Expect advisors/admins on desktop and students on mobile; responsive web ensures a single codebase covers both.

## Technical Assumptions

### Repository Structure: Monorepo
Single FastAPI-centric repository containing API, workers, shared domain models, and infrastructure scripts (Docker, IaC). Keeps async pipeline cohesive and accelerates iteration within the four-week MVP window.

### Service Architecture
Modular monolith using FastAPI for HTTP routes and Redis-backed workers (RQ) for GPT essay scoring and RAG retrieval. Workers share ORM access and configuration modules, enabling independent horizontal scaling of API and worker containers without microservice overhead.

### Testing Requirements
Adopt Unit + Integration coverage. Unit tests cover rule scorers, fusion logic, track routing, and RAG query builders. Integration tests exercise end-to-end async pipeline with local Postgres/Redis/Chroma containers. Contract tests mock OpenAI interactions to avoid external dependencies. Full UI E2E deferred until companion front-end exists.

### Additional Technical Assumptions and Requests
- Language/Framework: Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2.
- Queue: Redis-backed RQ with exponential backoff and dead-letter queues for failed jobs.
- Vector Store: Chroma or PGVector managed with migrations; embeddings generated via OpenAI `text-embedding-3-small`.
- Deployment: Docker Compose for local dev; container images target AWS ECS Fargate (or similar) with Terraform/IaC stubs for future scaling.
- Secrets: Environment variables locally; parameter store/secret manager for production; rotate OpenAI keys monthly.
- Observability: OpenTelemetry-compatible logging, Prometheus exporters for queue depth/latency; Grafana dashboard skeleton.
- Role catalogs and question pools stored in Postgres with versioned seeds for track-based question selection.
- Security: JWT auth with role claims, HTTPS enforcement, rate limiting (token bucket), and audit logging on admin actions.

## Cross-Functional Requirements

### Data Requirements
- Core entities: `role_catalog`, `users`, `questions`, `assessments`, `assessment_question_snapshots`, `assessment_responses`, `rule_scores`, `essay_scores`, `recommendations`, `recommendation_items`, `rag_traces`, `credential_catalog`, `embedding_artifacts`, `async_jobs`, `recommendation_feedback`, `audit_logs`, `metric_snapshots`, and `webhook_events` (see ERD in `docs/architecture/database-schema.md`).
- Storage: PostgreSQL as system of record with JSONB for rubric/score payloads; Chroma/PGVector for embeddings; Redis for transient queue state.
- Data Quality: Validation ensures question snapshots are immutable per assessment; scores and recommendations must have consistent foreign-key relationships; degraded-mode flag captured for analytics.
- Retention: Assessment data retained for at least 24 months; queue metadata retained 30 days; audit logs retained 36 months for compliance.
- Migration Strategy: Versioned SQL migrations per entity with rollback scripts; catalog seeds managed via migration fixtures.

### Integration Requirements
- External services: OpenAI GPT (essay scoring, summarization) and embedding APIs; vector store (Chroma/PGVector) hosted within deployment environment.
- Authentication: JWT for internal API access; OpenAI key stored in secret manager; vector store secured via VPC networking or API keys.
- Data Exchange: REST/JSON for external interactions; internal services communicate over shared database/queues; webhook payloads signed for integrity.
- Testing: Mock OpenAI responses in integration tests; replay recorded embeddings for deterministic validation.

### Operational Requirements
- Deployment cadence: Weekly deployments during MVP build; automated CI/CD to staging then production with canary validation.
- Environments: Dev (local Docker Compose), Staging (shared ECS cluster), Production (isolated ECS cluster with managed Postgres/Redis).
- Monitoring & Alerting: Prometheus/Grafana dashboards for latency and queue depth; alert thresholds for queue backlog >50 jobs or degraded incidents >5% over 1 hour.
- Support: On-call rotation (product + engineering) during pilot weeks; runbooks covering GPT failures, vector store downtime, and webhook retries.
- Documentation: Living runbooks and API docs linked in repo; onboarding guides for advisors and admins updated prior to pilot.

## Epic List
- Epic 1 – Role-Gated Assessment Foundation: Stand up the FastAPI monorepo, JWT auth, role/track catalog, question bank CRUD, and `/assessments/start` flow so students pick a role and receive the 10-question bundle.
- Epic 2 – Async Scoring and Persistence Backbone: Deliver rule-based scoring inline, Redis queue plus worker for GPT essays, Postgres persistence, status polling/webhooks, and degraded-mode handling.
- Epic 3 – Recommendations, Transparency, and Feedback Loop: Implement RAG retrieval tuned by role context, fusion summary with traceable sources, advisor/student feedback capture, and dashboards to surface results and observability insights.

## Epic 1 Role-Gated Assessment Foundation
**Goal:** Establish the FastAPI monorepo, secure auth, role catalog, and question management so students must pick a target role before receiving a 10-question bundle.

### Story 1.1 Monorepo Baseline and Auth Skeleton
As a developer, I want a FastAPI monorepo with JWT auth scaffolding so that we can enforce secure, role-aware access across services.

#### Acceptance Criteria
1. Repo contains FastAPI app, worker stub, shared models, and Docker Compose with Postgres/Redis.
2. JWT auth middleware issues and validates tokens with role claims (`student`, `advisor`, `admin`).
3. CI pipeline runs lint and unit tests on pull requests.
4. Health endpoint and logging format follow observability conventions.

### Story 1.2 Track Catalog Management
As an admin, I want to define and maintain role/track metadata so that assessments can tailor content to the selected focus area.

#### Acceptance Criteria
1. `/api/v1/tracks` CRUD endpoints exist (admin-only) with audit logging.
2. Track schema captures name, description, skill focus tags, and question mix overrides.
3. GET endpoints expose active tracks for student preview.
4. Track seeds load during migration with examples (Backend Engineer, Data Analyst).

### Story 1.3 Question Bank CRUD and Versioning
As an admin, I want to manage question pools per track so that theoretical, essay, and profile questions stay aligned with role requirements.

#### Acceptance Criteria
1. Question CRUD endpoints support type, prompt, track tags, and rubric/rules payloads.
2. Soft delete keeps historical data while removing items from active rotations.
3. Version snapshot stored when questions change.
4. Unit tests cover rule parsing and rubric validation.

### Story 1.4 Role-Gated Assessment Start
As a student, I want to start an assessment by choosing a role so that I receive questions aligned with that track.

#### Acceptance Criteria
1. `POST /api/v1/assessments/start` requires `trackId` and validates eligibility.
2. Endpoint assembles three theoretical, three essay, and four profile questions mapped to the selected track, snapshots prompts, and returns bundle <400 ms p95.
3. Partial response tokens created with expiry and resume capability.
4. API captures analytics event tying student, track, and assessment ID.

## Epic 2 Async Scoring and Persistence Backbone
**Goal:** Deliver the hybrid scoring pipeline: inline rule scoring, Redis-backed GPT essay evaluation, durable storage, and status visibility.

### Story 2.1 Submission Finalization and Rule Scoring
As a student, I want my responses finalized and scored instantly for rule-based items so that I get immediate progress confirmation.

#### Acceptance Criteria
1. `POST /api/v1/assessments/{id}/submit` enforces completion, locks responses, and computes theoretical/profile scores synchronously.
2. Scores are written to the Postgres `rule_scores` table with a per-question breakdown.
3. Entries are created in the `async_jobs` table with `job_type` values `score_essay` and `generate_recommendations`, initial status `queued`.
4. Degraded flag set if required data is missing.

### Story 2.2 GPT Essay Scoring Worker
As a scoring worker, I want to evaluate essays asynchronously via GPT so that rubric-based scores persist without blocking the API.

#### Acceptance Criteria
1. Worker pulls from the Redis RQ queues (`default`, `high`), invokes the `score_essay_job` handler per assessment, and calls GPT with a deterministic prompt.
2. GPT responses parsed into rubric metrics; retries up to three attempts with exponential backoff.
3. Failures log detailed diagnostics and mark job `failed` while triggering degraded state.
4. Unit tests mock GPT responses and cover retry logic.

### Story 2.3 Status Polling, Webhooks, and Idempotency
As a student, I want to track assessment processing so that I know when results are ready.

#### Acceptance Criteria
1. `/api/v1/assessments/{id}/status` returns stage progress (`rule_scoring`, `essay_scoring`, `recommendations`) and completion percentage.
2. Optional webhook registration stored; worker triggers callback on completion or failure.
3. Idempotency keys enforced on submissions to prevent duplicate jobs.
4. Observability metrics exported for job durations and queue depth.

## Epic 3 Recommendations, Transparency, and Feedback Loop
**Goal:** Produce RAG-powered recommendations with explainable traces, gather stakeholder feedback, and expose health dashboards.

### Story 3.1 Role-Aware RAG Retrieval
As a recommendation service, I want to retrieve micro-credentials using role context so that advisors see relevant options.

#### Acceptance Criteria
1. Worker composes RAG query from track tags, profile signals, and essay embeddings.
2. Chroma (or PGVector) returns Top-K credentials with metadata.
3. Results persisted in `recommendation_items` with ranked order.
4. Static fallback path activates when vector store fails and toggles `degraded` flag.

### Story 3.2 Fusion Summary and Result Delivery
As a student, I want a unified recommendation summary with traceable sources so that I understand why a credential fits my chosen role.

#### Acceptance Criteria
1. Fusion job combines rule scores, essay metrics, and RAG results into narrative summary stored in `recommendations`.
2. `/api/v1/assessments/{id}/result` returns summary, ranked items, RAG traces, and degraded status.
3. Response includes timestamp and processing duration for observability.
4. Integration tests verify end-to-end flow from submission to result across success and degraded paths.

### Story 3.3 Advisor and Student Feedback plus Observability Dashboards
As an advisor, I want to log feedback on recommendations and monitor system health so that we can improve future cohorts.

#### Acceptance Criteria
1. `/api/v1/recommendations/{id}/feedback` captures ratings (relevance, acceptance) and comments tied to track.
2. Dashboard endpoints expose aggregated feedback, queue latency, GPT usage, and failure modes.
3. Metrics tagged by track for analytics alignment.
4. Security audit ensures advisor feedback requires proper role and logs events.

## Stakeholder Alignment & Communication

### Stakeholders
- **Product Lead (John):** Owns PRD updates, MVP scope, and pilot outcomes.
- **Engineering Lead:** Accountable for implementation sequencing, technical risk mitigation, and deployment readiness.
- **Academic Advisor Champion:** Provides user insights, validates recommendation relevance, and evangelizes pilot adoption.
- **Student Success Manager:** Coordinates student participation and gathers satisfaction data.
- **Data Privacy Officer:** Reviews compliance, retention, and audit strategies.

### Communication Plan
- **Weekly Core Sync:** Product + Engineering + Advisor Champion review progress, risks, and upcoming milestones.
- **Pilot Readiness Review (Week 3):** Go/no-go on pilot, confirm metrics instrumentation and support coverage.
- **Pilot Debriefs:** Daily 15-minute stand-ups during pilot week to track incidents and user feedback.
- **Stakeholder Newsletter:** Bi-weekly summary email covering achievements, metrics, and next steps shared with broader leadership.

### Approval Workflow
- PRD baseline approved by Product Lead and Engineering Lead prior to architecture handoff.
- Major scope changes require joint sign-off from Product Lead, Engineering Lead, and Academic Advisor Champion.
- Post-pilot go/no-go decision ratified by Product Lead, Student Success Manager, and Data Privacy Officer.

## Checklist Results Report
- 2025-10-14: PM checklist executed in YOLO mode. Initial gaps identified in research documentation, UX flows, cross-functional requirements, and stakeholder alignment.
- 2025-10-14: This revision adds research insights, validation plan, UX journeys, cross-functional requirements, and communication plan to close checklist findings. Remaining watch items include validating quantitative assumptions during the pilot.

## Next Steps

### UX Expert Prompt
"You are the UX Expert focused on translating this PRD into interface concepts. Using the role-gated assessment flow, async status visibility, and RAG transparency requirements described here, outline the key user journeys and propose wireframe-level layouts for the student dashboard, advisor console, and admin operations screen. Prioritize clarity around role selection, progress tracking, and recommendation explainability."

### Architect Prompt
"You are the Software Architect responsible for implementing the AI-powered Micro-Credential Assessment Backend MVP defined in this PRD. Design a detailed architecture plan covering FastAPI modular monolith structure, Redis queue configuration, GPT/RAG integration patterns, database schema/migrations, deployment topology (local Docker → ECS Fargate), and observability setup. Explicitly address role-based question selection, degraded-mode fallbacks, latency targets, and scaling to ≥100 concurrent assessments."
