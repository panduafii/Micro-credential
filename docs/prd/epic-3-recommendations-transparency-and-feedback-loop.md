# Epic 3 Recommendations, Transparency, and Feedback Loop
**Goal:** Produce RAG-powered recommendations with explainable traces, gather stakeholder feedback, and expose health dashboards.

## Story 3.1 Role-Aware RAG Retrieval
As a recommendation service, I want to retrieve micro-credentials using role context so that advisors see relevant options.

### Acceptance Criteria
1. Worker composes RAG query from track tags, profile signals, and essay embeddings.
2. Chroma (or PGVector) returns Top-K credentials with metadata.
3. Results persisted in `recommendation_items` with ranked order.
4. Static fallback path activates when vector store fails and toggles `degraded` flag.

## Story 3.2 Fusion Summary and Result Delivery
As a student, I want a unified recommendation summary with traceable sources so that I understand why a credential fits my chosen role.

### Acceptance Criteria
1. Fusion job combines rule scores, essay metrics, and RAG results into narrative summary stored in `recommendations`.
2. `/api/v1/assessments/{id}/result` returns summary, ranked items, RAG traces, and degraded status.
3. Response includes timestamp, processing duration, and cost metrics snapshot.
4. Integration tests verify end-to-end flow from submission to result across success and degraded paths.

## Story 3.3 Advisor and Student Feedback plus Observability Dashboards
As an advisor, I want to log feedback on recommendations and monitor system health so that we can improve future cohorts.

### Acceptance Criteria
1. `/api/v1/recommendations/{id}/feedback` captures ratings (relevance, acceptance) and comments tied to track.
2. Dashboard endpoints expose aggregated feedback, queue latency, GPT usage, and failure modes.
3. Metrics tagged by track for analytics alignment.
4. Security audit ensures advisor feedback requires proper role and logs events.
