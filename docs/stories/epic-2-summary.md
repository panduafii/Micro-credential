# Epic 2 Summary: Async Scoring and Persistence Backbone

## Status
- **Completed** ✅

## Epic Goal
Deliver rule-based scoring inline, Redis queue plus worker for GPT essays, Postgres persistence, status polling/webhooks, and degraded-mode handling.

## Stories Completed

| Story | Title | Status | Tests |
|-------|-------|--------|-------|
| 2.1 | Submission Finalization and Rule Scoring | ✅ | 15 |
| 2.2 | GPT Essay Scoring Worker | ✅ | 9 |
| 2.3 | Status Polling, Webhooks, and Idempotency | ✅ | 10 |

**Total Tests Added:** 34

## Key Deliverables

### 1. Assessment Submission Flow
- POST /assessments/{id}/submit endpoint
- Response locking (no edits after submit)
- Degraded mode for missing responses

### 2. Rule-Based Scoring
- Theoretical questions: correct/incorrect scoring
- Profile questions: full weight for all responses
- Immediate results returned in submit response

### 3. Async Job Queue
- Redis-backed job queue for async processing
- Job types: gpt, rag, fusion
- Status tracking: queued → in_progress → completed/failed

### 4. GPT Essay Scoring
- OpenAI integration with rubric-based evaluation
- 4-dimension scoring (relevance, depth, clarity, technical)
- Retry logic with exponential backoff
- Error handling for timeouts and rate limits

### 5. Status Polling & Webhooks
- GET /assessments/{id}/status for progress tracking
- Stage-by-stage progress (rule_score, gpt, rag, fusion)
- Webhook URL registration for completion callbacks

### 6. Idempotency
- Idempotency-Key header support on submissions
- Prevents duplicate processing

## API Endpoints Added

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /assessments/{id}/submit | Submit assessment for scoring |
| GET | /assessments/{id}/status | Get progress and job status |
| POST | /assessments/{id}/webhook | Register webhook URL |

## Database Schema Changes

### New Tables
- `scores` - Stores all score records (theoretical, profile, essay)
- `async_jobs` - Tracks async job status and metadata

### Modified Tables
- `assessments` - Added `webhook_url`, `idempotency_key` columns

## Technical Decisions

### 1. String Columns vs PostgreSQL Enum
Used `String(20)` columns instead of PostgreSQL Enum types for `async_jobs.job_type` and `async_jobs.status` to avoid enum conflicts with SQLAlchemy migrations.

### 2. Score Structure
Scores stored per question with type discrimination:
- `theoretical` - Rule-based correct/incorrect
- `profile` - Full weight for responses
- `essay_gpt` - GPT rubric scores

### 3. Stage Weights
Overall progress calculated with weights:
- rule_score: 20%
- gpt: 30%
- rag: 30%
- fusion: 20%

## Files Structure

```
src/
├── api/
│   ├── routes/assessments.py     # Submit, status, webhook endpoints
│   └── schemas/assessments.py    # Response schemas
├── domain/
│   └── services/
│       ├── submission.py         # Submission and rule scoring
│       ├── gpt_scoring.py        # GPT essay scoring
│       └── status.py             # Status and webhook services
└── infrastructure/
    ├── db/models.py              # Score, AsyncJob models
    └── gpt_client.py             # OpenAI API client

alembic/versions/
├── 202412250003_add_scores_table.py
├── 202412250004_add_async_jobs_table.py
└── 202412250006_add_webhook_and_idempotency.py

tests/unit/
├── test_assessment_submission.py  # 15 tests
├── test_gpt_scoring.py           # 9 tests
└── test_status_and_webhooks.py   # 10 tests
```

## Lessons Learned

1. **Enum Naming**: PostgreSQL enum names use snake_case (`assessment_status` not `assessmentstatus`)
2. **Enum Conflicts**: Use String columns to avoid SQLAlchemy/Alembic enum conflicts
3. **Model Fields**: Always verify actual column names (e.g., `owner_id` not `student_id`)
4. **Ruff Formatting**: Both `ruff check` (lint) AND `ruff format` must pass for CI

## Next Steps → Epic 3

Epic 3 will implement:
- RAG-powered credential recommendations
- Transparency dashboard with traceable sources
- Feedback collection and analytics
