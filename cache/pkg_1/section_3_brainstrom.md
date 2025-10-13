# Section 3: System Architecture Design (MVP)

> Basis: async-first backend with **hybrid scoring (rule + GPT)** and **RAG-powered recommendations**; four-week MVP; $5/500-call cost target; mandatory RAG; sync fallback when needed.

---

## 3.1 High-Level Architecture (Components)

**Edge & API**

* **FastAPI Gateway**: JWT auth, request routing, OpenAPI docs.
* **Rate Limiter**: simple token bucket (per-token/per-IP).

**Domain Services**

* **Assessment Service**

  * Issue question set (**3 theoretical + 3 essay + 4 profile/interest**), accept responses, finalize.
  * Compute **rule-based** scores (theory & profile) synchronously.
* **Scoring Worker**

  * Async **GPT essay evaluation** (rubrics), retries, idempotency.
* **RAG Service**

  * Query **Chroma** on micro-credential catalog; returns top-K with metadata.
* **Fusion & Summarization Service**

  * Fuses **essay + theoretical + profile** signals; generates **final recommendation summary** with traceable sources (explainability).
* **Admin Ops**

  * Question bank (admin), catalog CRUD, index rebuilds, metrics.

**State & Infra**

* **PostgreSQL**: users, assessments, responses, scores, recommendations, audit.
* **Redis**: queues (GPT/RAG jobs), short-lived caches, progress.
* **ChromaDB**: embeddings for credentials catalog (RAG).
* **Observability**: structured logs, latency histograms, queue depth, token usage.

**Resilience**

* **Sync Fallback**: static lookup / cached recs when GPT/RAG is down.

---

## 3.2 Deployment Topology (MVP)

* **Containers**:

  * `api` (FastAPI + Uvicorn/Gunicorn)
  * `worker` (RQ/Celery/Arq) for GPT & RAG tasks
  * `redis`, `postgres`, `chroma`
* **Scaling**:

  * Horizontally scale `api` and `worker` independently.
  * Redis and Chroma can be single-node MVP, upgradeable later.
* **Secrets**: ENV (OpenAI key, DB URL, JWT secret).
* **Networking**: API behind reverse proxy (nginx/traefik). Health probes on `/ops/health`.

---

## 3.3 Data Model (ERD Tables)

**users**

* `id (pk)`, `email (uniq)`, `password_hash`, `role [student|admin]`, `name`, `interests_json`, `created_at`

**assessments**

* `id (pk)`, `user_id (fk users)`, `status [draft|queued|processing|done|failed]`, `composition_json` (e.g., `{theory:3, essay:3, profile:4}`), `created_at`, `finalized_at`

**questions**

* `id (pk)`, `type [theory|essay|profile]`, `prompt`, `options_json` (nullable), `rules_json` (rule scoring), `active`

**assessment_questions** (snapshot for stability)

* `id (pk)`, `assessment_id (fk)`, `question_id (fk)`, `prompt_snapshot`, `type`, `order`

**responses**

* `id (pk)`, `assessment_id (fk)`, `assessment_question_id (fk)`, `answer_text` (for essay), `answer_option` (for MCQ), `answer_numeric` (for profile scales), `submitted_at`

**scores**

* `id (pk)`, `assessment_id (fk)`,

  * `theory_score_json` (per-question correctness),
  * `profile_signals_json` (interests, strengths),
  * `essay_scores_json` (per-essay rubric: clarity, accuracy, coherence, etc.),
  * `computed_at`

**recommendations**

* `id (pk)`, `assessment_id (fk)`, `summary_text` (fusion of **essay+theory+profile**), `generated_at`

**recommendation_items**

* `id (pk)`, `recommendation_id (fk)`, `credential_id (fk credentials)`, `rank`, `reason_short`

**rag_traces**

* `id (pk)`, `recommendation_id (fk)`, `item_id (fk recommendation_items)`, `source_title`, `snippet`, `source_url`, `score`

**credentials** (admin-managed catalog, RAG corpus)

* `id (pk)`, `title`, `provider`, `tags`, `desc`, `url`, `active`, `updated_at`

**embeddings_meta**

* `id (pk)`, `credential_id (fk)`, `embedding_id` (chroma key), `model`, `dim`, `created_at`

**jobs**

* `id (pk)`, `assessment_id (fk)`, `type [gpt|rag|fusion]`, `status`, `attempts`, `last_error`, `created_at`, `updated_at`

**audits / metrics**

* `id (pk)`, `actor`, `action`, `resource`, `meta_json`, `created_at`

> Rationale: the split keeps MVP lean yet auditable; fusion & trace tables ensure explainability demanded by advisors.

---

## 3.4 Key Data Flows (Text “Diagrams”)

### A) Assessment → Scores → Recommendations (Happy Path)

1. **Start**: API creates `assessment`, snapshots 10 Qs (3/3/4), returns payload.
2. **Submit**: Client posts responses (partial allowed).
3. **Finalize**: `submit` enqueues **two jobs**:

   * **Rule Scoring** (inline): compute theory/profile instantly; persist `scores.theory/profile`.
   * **Essay GPT** (async): worker calls GPT with rubric prompt → write `scores.essay`.
4. **RAG Retrieval**: worker queries Chroma with profile+essay embeddings; fetches catalog Top-K; store `recommendation_items` + `rag_traces`.
5. **Fusion & Summary**: combine **essay + theoretical + profile** → generate final **summary_text**; store in `recommendations`.
6. **Complete**: status→`done`; client polls `/status` or receives webhook; fetch `/result`.

### B) Degradation / Fallback

* If **GPT** fails after retries → proceed with theory+profile signals and cached/static recommendations; mark result `degraded=true`.
* If **RAG** latency high → serve last-known good from cache; schedule rebuild; log metric.

### C) Catalog & Index Maintenance

* Admin updates credentials → `/catalog/credentials` (CRUD).
* Rebuild embeddings → `/rag/index/rebuild` (batch to Chroma, write `embeddings_meta`).
* `/rag/index/stats` surfaces counts, model, last build.

---

## 3.5 Component–API Responsibility Map

* **Assessment Service**

  * `/assessments/*`, `/scores/*` (read), orchestrates finalize & job enqueue.
* **Scoring Worker**

  * Consumes essay jobs; updates `scores.essay`.
* **RAG Service**

  * `/recommendations/*` (read), internal vector queries, writes `recommendation_items` & `rag_traces`.
* **Fusion Service**

  * Generates `/result` payload; writes `recommendations.summary_text`.
* **Admin Service**

  * `/questions`, `/catalog/credentials`, `/rag/index/*`, `/ops/*`, `/analytics/*`.

---

## 3.6 Security & Compliance (MVP)

* **JWT** with roles (`student`, `admin`), per-route RBAC.
* **PII at rest**: Postgres column-level encryption (or pgcrypto).
* **Secrets**: ENV / secret manager.
* **Audit** every admin write and index rebuild.
* **Prompt Safety**: ground essay prompts; sanitize inputs.

---

## 3.7 Performance & Scalability

* **Latency SLOs**: rule paths < 500 ms; GPT completion < 10 s p95; RAG ≤ 1.5 s avg.
* **Throughput**: ≥100 concurrent assessments (scale workers first).
* **Queues**: exponential backoff (×3); dead-letter queue for post-mortem.
* **Caching**: Redis for hot credentials & prior Top-K to absorb spikes.
* **Cost**: constrain GPT tokens by **3 essays** only; keep RAG Top-K small (e.g., 6–8).

---

## 3.8 Technology Choices (Justification)

* **FastAPI + Pydantic**: speed & type safety for JSON contracts.
* **Redis Queue**: simple, observable async backbone.
* **Chroma**: lightweight vector store aligns with MVP speed & budget.
* **PostgreSQL**: reliable OLTP core; easy JSON columns for flexible rubrics.
* **OpenAI GPT**: constrained to essays & summarization to meet budget.

---

## 3.9 Sequence: Week-by-Week (Build Plan)

* **Week 1**: Auth, Assessment start/submit, rule scoring, static fallback path.
* **Week 2**: Essay GPT scoring, Postgres persistence, `/result` v0.
* **Week 3**: RAG retrieval + Fusion summary + Redis cache + ops endpoints.
* **Week 4**: QA, perf tuning, webhooks, resilience polish, launch.

---

