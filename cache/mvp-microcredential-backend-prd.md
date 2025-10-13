# Micro-Credential Assessment Backend MVP PRD

**Owner:** Solo developer  
**Version:** v1.0 (2025-10-11)  
**Duration:** 4-week MVP sprint  

## 1. Product Overview

### 1.1 Vision
Deliver a 15–20 minute adaptive-style skills assessment that produces an objective, AI-assisted skill profile and surfaces targeted micro-credential recommendations so IT students immediately know what to learn next. The backend provides RESTful APIs that partner frontends, advisors, and future LMS integrations can consume.

### 1.2 Goals
- Help IT students cut through self-assessment bias and pinpoint skill gaps within one session.
- Give academic advisors evidence-based insight into student capabilities and recommended actions.
- Ship a stable, credible backend that can extend to semantic recommendations post-MVP.

### 1.3 Success Metrics (MVP)
- **Usage:** ≥ 100 unique assessment sessions by end of pilot month.
- **Completion:** ≥ 50% of started assessments reach completion.
- **Perceived Accuracy:** ≥ 80% of surveyed students rate scoring “fair/accurate”.
- **Recommendation Relevance:** ≥ 70% of advisors/students mark suggested courses “helpful”.
- **Performance:** Core endpoints respond in ≤ 500 ms p95; overall uptime ≥ 95%.
- **Engagement Signal:** ≥ 30% click-through on recommended course links.

## 2. Target Users & Scenarios

| User | Scenario | Value |
| --- | --- | --- |
| IT Student (CS / SWE / IS) | Launches assessment from web/mobile frontend, completes 10-question flow, receives profile + courses | Understand current proficiency and next learning actions |
| Academic Advisor / Career Coach | Reviews student profile and recommendations | Confirms skill gaps, guides students with confidence |
| Partner Platform / LMS | Integrates APIs for assessment and recommendations | Adds personalized upskilling experience to their product |

## 3. Scope

### 3.1 In Scope (Baseline MVP)
- Authentication & session management via JWT.
- Fixed 10-question assessment per session (5 essay/coding, 3 MCQ, 2 interest).
- Role selection (8 specialized roles) driving question set and recommendation mapping.
- Rule-based scoring for MCQ; GPT-3.5-turbo scoring + summary for essays only.
- Skill profile generator: overall score (0–100), domain breakdown, strengths, improvements, confidence indicator.
- Recommendation lookup table (role + score range + interest → 2–3 courses).
- PostgreSQL storage for users, sessions, questions, answers, profiles, recommendations.
- In-process async job queue for GPT calls with synchronous fallback.
- REST API surface covering assessment lifecycle, profile retrieval, and recommendations.
- Basic observability: structured logs, request metrics, GPT call counters.

### 3.2 Out of Scope / Deferred
- Semantic or vector-based recommendation engine (ChromaDB, embeddings).
- Redis caching, performance tuning beyond baseline.
- Advisor analytics dashboards or cohort reporting.
- Admin UI for authoring questions or courses.
- Multi-course learning path tracking.
- Email notifications or webhook integrations.

## 4. Functional Requirements

### 4.1 Assessment Lifecycle
1. **Role Selection:** `POST /assessments/start`
   - Inputs: `role`, optional `experienceLevel`.
   - Output: `assessmentId`, `expiresAt`, initial question metadata.
2. **Question Delivery:** `GET /assessments/{assessmentId}/next`
   - Returns next unanswered question (type: `mcq`, `essay`, `interest`).
   - Includes timers where applicable.
3. **Answer Submission:** `POST /assessments/{assessmentId}/answer`
   - Validates payload, runs rule-based scoring for MCQ immediately.
   - Queues essay answers for async GPT scoring and persists interim status.
4. **Completion:** `POST /assessments/{assessmentId}/complete`
   - Triggers aggregation of rule-based scores + awaited GPT results (blocking up to timeout; fallback to synchronous call if queue pending).
   - Generates skill profile snapshot and recommendation bundle.
5. **Profile Retrieval:** `GET /profiles/{assessmentId}`
   - Returns normalized profile object: `overallScore`, `domainBreakdown`, `strengths`, `improvements`, `confidenceScore`, `recommendations`.

### 4.2 Recommendation Delivery
- **Data Model:** Seeded lookup table keyed by `(role, scoreBand, interestTag)` returning 2–3 micro-credentials.
- **API:** `GET /recommendations?assessmentId=...` (reads from generated bundle; no recalculation).
- **Course Metadata:** Title, provider, estimated effort, format, URL.

### 4.3 Administration (MVP Lightweight)
- Static YAML/JSON files or database seed scripts to manage question bank and course mapping.
- Internal scripts to refresh lookup tables; no UI required.

## 5. Non-Functional Requirements
- **Latency:** Assessment and recommendation endpoints ≤ 500 ms p95 (excluding GPT call durations handled asynchronously).
- **Availability:** ≥ 95% uptime during pilot.
- **Security:** bcrypt password hashing, JWT access tokens (24h expiry) with refresh, rate limiting on auth endpoints.
- **Privacy:** Store minimal PII (name, email). Align with basic GDPR: allow account deletion, data export stub.
- **Reliability:** Retry with exponential backoff for GPT failures; circuit breaker after repeated errors; log + alert.
- **Cost:** GPT usage capped at 5 prompts per assessment (~$0.01), monthly ≤ $5 (tracking via usage dashboards or manual logs).

## 6. Technical Architecture
- **Language / Framework:** Python 3.11, FastAPI.
- **Data:** PostgreSQL (SQLAlchemy ORM / Alembic migrations). Essays stored as text columns. Optional S3-compatible storage post-MVP.
- **Async Queue:** FastAPI background tasks or lightweight library (e.g., `dramatiq` or `rq`) with same DB backend; synchronous fallback path for reliability.
- **AI Integration:** OpenAI GPT-3.5-turbo; structured prompt expecting JSON: `{ "score": 0-10, "strengths": "...", "improvements": "..." }`.
- **Deployment:** Free-tier PaaS (Railway/Render) with environment variables for secrets.
- **Observability:** Structured logs (JSON), minimal metrics (e.g., Prometheus or service-provided stats), health checks.

## 7. Content & Scoring Design

### 7.1 Question Bank (Baseline)
- 5 essay/coding prompts across chosen role domains.
- 3 MCQ/theoretical questions covering core concepts.
- 2 interest/profile questions capturing preferred learning style or career objectives.
- Each question tagged with domain (e.g., `backend.logic`, `data.modeling`).

### 7.2 Scoring Model
- MCQ: binary scoring (correct=1, incorrect=0) with weight per domain.
- Essay: GPT returns 0–10; normalized to 0–1 weight per domain.
- Interest: stored for recommendation filters; no scoring.
- Aggregate: Weighted formula producing 0–100 overall, domain-level percentages, confidence score derived from answer completeness + GPT response reliability.

## 8. Implementation Plan (4 Weeks)

| Week | Focus | Key Deliverables |
| --- | --- | --- |
| **Week 1** | Auth & Assessment Sequencing | Auth endpoints, JWT workflow, assessment start/next/answer endpoints, initial question bank seeded |
| **Week 2** | Scoring & Persistence | Rule-based scoring, GPT integration spike, database schema & migrations, data access layer |
| **Week 3** | Async Queue & Recommendations | Background processing for GPT, synchronous fallback, recommendation lookup service & endpoint, OpenAPI documentation |
| **Week 4** | QA & Launch Polish | Automated tests, end-to-end walkthroughs, deployment scripts, monitoring hooks, contingency fixes |

## 9. Validation Plan
- **Question Bank Pilot:** Test with 5–7 students; capture completion time, difficulty feedback, perceived fairness.
- **GPT Consistency Check:** Score 10 sample essays twice; variance < 1 point; adjust prompts if needed.
- **Recommendation Review:** Present generated recommendations to 3 advisors; aim for ≥ 70% “relevant” rating.
- **Usability Smoke Test:** Observe 3 users completing assessment; target ≤ 10 minutes, no critical blockers.
- **Performance Test:** Simulate 20 concurrent sessions; ensure queue handles GPT latency without blocking.

## 10. Risks & Mitigations
- **GPT Latency/Failures:** Mitigation—async queue with retries and synchronous fallback; cache last acceptable response pattern.
- **Question Bank Quality:** Mitigation—pilot testing and advisor review before launch.
- **Solo Resource Burnout:** Mitigation—15% time buffer and weekly checkpoints; fallback plan trims scope to rapid screener if needed.
- **Recommendation Staleness:** Mitigation—quarterly review of lookup table; add manual override notes.
- **Budget Overrun:** Mitigation—monitor GPT call counts; throttle assessments if trending above limit.

## 11. Roadmap Beyond MVP
- **Fallback Plan (if delays):** Switch to 5-question rapid screener, pure rule-based scoring, all-in-Postgres synchronous flow.
- **Stretch Upgrade:** 20-question deep dive, curated role-specific course playlists, Redis caching, ChromaDB semantic retrieval, expanded metrics (time-to-complete, advisor approvals).
- **Future Enhancements:** Advisor analytics dashboard, admin tooling for content management, adaptive assessment logic, automated learning path orchestration, notification workflows.

---

*Prepared from brainstorming session on 2025-10-11 to guide MVP execution and stakeholder alignment.*
