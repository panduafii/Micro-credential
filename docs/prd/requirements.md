# Requirements

## Functional Requirements
- FR1: The `POST /api/v1/assessments/start` endpoint must require the student to choose a target role/track (e.g., “Backend Engineer”, “Data Analyst”) and return a 10-question bundle tailored to that role from the active bank within 400 ms p95.
- FR2: The system must expose `/api/v1/tracks` so students can preview available roles, associated skill focus, and question mix before starting an assessment.
- FR3: The system must accept partial response batches and persist them idempotently so students can resume assessments without data loss.
- FR4: On final submission the backend must synchronously compute rule-based scores for theoretical and profile questions, update the score record, and enqueue GPT/RAG jobs with a retry cap of three attempts.
- FR5: Essay-scoring workers must evaluate each essay via GPT against rubric dimensions (clarity, accuracy, coherence) and save structured scores plus feedback traces.
- FR6: The RAG service must build a retrieval query using the selected role, profile signals, and essay insights, fetch Top-K credentials from Chroma, and persist ranked items with source snippets.
- FR7: The fusion service must combine role context, rule scores, essay insights, and RAG output into a single recommendation summary while flagging degraded results when fallbacks were used.
- FR8: Students must be able to poll `/api/v1/assessments/{id}/status` and `/api/v1/assessments/{id}/result`, and receive webhooks (when configured) when processing completes.
- FR9: Admins must manage the question bank, credential catalog, track definitions, and RAG index through secured endpoints with full audit logging.
- FR10: The system must capture user/advisor feedback on recommendation relevance and perceived fit for the selected role to inform future tuning.

## Non-Functional Requirements
- NFR1: Average synchronous endpoint latency must stay <500 ms p95; async GPT completion must stay <10 s p95; RAG retrieval <1.5 s average.
- NFR2: The system must handle ≥100 concurrent assessments by horizontally scaling API and worker pods without data loss.
- NFR3: Total OpenAI plus embedding spend must remain ≤$5 per 500 assessments, managed via prompt/token budgeting.
- NFR4: Redis queues must tolerate worker restarts with exactly-once processing guarantees enforced through job status locking.
- NFR5: Postgres must encrypt PII at rest and ensure referential integrity across assessments, scores, recommendations, and track selections.
- NFR6: Every recommendation must include traceable sources so advisors can validate AI output.
- NFR7: Observability must capture structured logs, queue depth, latency histograms, and inference token counts for SLO tracking, segmented by role/track.
- NFR8: The system must provide a static recommendation fallback when GPT or RAG paths fail while logging the degraded mode and affected role/track.
