# Cross-Functional Requirements

## Data Requirements
- Core entities: users, assessments, questions, responses, scores, recommendations, recommendation_items, rag_traces, credentials, embeddings_meta, jobs, audit_events, metrics (see ERD outline in `docs/section_3_brainstrom.md`).
- Storage: PostgreSQL as system of record with JSONB for rubric/score payloads; Chroma/PGVector for embeddings; Redis for transient queue state.
- Data Quality: Validation ensures question snapshots are immutable per assessment; scores and recommendations must have consistent foreign-key relationships; degraded-mode flag captured for analytics.
- Retention: Assessment data retained for at least 24 months; queue metadata retained 30 days; audit logs retained 36 months for compliance.
- Migration Strategy: Versioned SQL migrations per entity with rollback scripts; catalog seeds managed via migration fixtures.

## Integration Requirements
- External services: OpenAI GPT (essay scoring, summarization) and embedding APIs; vector store (Chroma/PGVector) hosted within deployment environment.
- Authentication: JWT for internal API access; OpenAI key stored in secret manager; vector store secured via VPC networking or API keys.
- Data Exchange: REST/JSON for external interactions; internal services communicate over shared database/queues; webhook payloads signed for integrity.
- Testing: Mock OpenAI responses in integration tests; replay recorded embeddings for deterministic validation.

## Operational Requirements
- Deployment cadence: Weekly deployments during MVP build; automated CI/CD to staging then production with canary validation.
- Environments: Dev (local Docker Compose), Staging (shared ECS cluster), Production (isolated ECS cluster with managed Postgres/Redis).
- Monitoring & Alerting: Prometheus/Grafana dashboards for latency and queue depth; alert thresholds for queue backlog >50 jobs or degraded incidents >5% over 1 hour.
- Support: On-call rotation (product + engineering) during pilot weeks; runbooks covering GPT failures, vector store downtime, and webhook retries.
- Documentation: Living runbooks and API docs linked in repo; onboarding guides for advisors and admins updated prior to pilot.
