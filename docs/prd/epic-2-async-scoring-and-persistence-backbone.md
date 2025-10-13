# Epic 2 Async Scoring and Persistence Backbone
**Goal:** Deliver the hybrid scoring pipeline: inline rule scoring, Redis-backed GPT essay evaluation, durable storage, and status visibility.

## Story 2.1 Submission Finalization and Rule Scoring
As a student, I want my responses finalized and scored instantly for rule-based items so that I get immediate progress confirmation.

### Acceptance Criteria
1. `POST /api/v1/assessments/{id}/submit` enforces completion, locks responses, and computes theoretical/profile scores synchronously.
2. Scores written to Postgres `scores` table with per-question breakdown.
3. Job records created (`gpt`, `rag`, `fusion`) with status `queued`.
4. Degraded flag set if required data is missing.

## Story 2.2 GPT Essay Scoring Worker
As a scoring worker, I want to evaluate essays asynchronously via GPT so that rubric-based scores persist without blocking the API.

### Acceptance Criteria
1. Worker pulls from Redis queue, batches essays per assessment, and calls GPT with deterministic prompt.
2. GPT responses parsed into rubric metrics; retries up to three attempts with exponential backoff.
3. Failures log detailed diagnostics and mark job `failed` while triggering degraded state.
4. Unit tests mock GPT responses and cover retry logic.

## Story 2.3 Status Polling, Webhooks, and Idempotency
As a student, I want to track assessment processing so that I know when results are ready.

### Acceptance Criteria
1. `/api/v1/assessments/{id}/status` returns stage progress (rule-score, gpt, rag, fusion) and percentage.
2. Optional webhook registration stored; worker triggers callback on completion or failure.
3. Idempotency keys enforced on submissions to prevent duplicate jobs.
4. Observability metrics exported for job durations and queue depth.
