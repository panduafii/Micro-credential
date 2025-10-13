Awesome — I’ll deliver **both**:
**Section 4: Detailed API–Service Contracts** *and* a **DB Schema (SQL migrations)** matching the ERD from Section 3 and your MVP plan (async + hybrid scoring + RAG + fusion). Key choices align with the brainstorming doc (async flow, RAG mandatory, cost/latency targets) .

---

# Section 4: Detailed API–Service Contracts (MVP)

*All routes are `/api/v1/*`. Auth: JWT Bearer. Admin routes require `role=admin`. All responses include `requestId` header for tracing.*

## 4.1 Auth & Users

### POST `/auth/register`

**Req**

```json
{"email":"user@mail.com","password":"•••","name":"Pandu","inviteCode":"ADM1N-OPT"}
```

**Res 201**

```json
{"id":"usr_01H...","email":"user@mail.com","role":"student","createdAt":"2025-10-13T12:00:00Z"}
```

### POST `/auth/login`

**Req**

```json
{"email":"user@mail.com","password":"•••"}
```

**Res 200**

```json
{"accessToken":"jwt...","refreshToken":"jwt...","expiresIn":3600}
```

### GET `/users/me` (Bearer)

**Res 200**

```json
{"id":"usr_01H...","email":"user@mail.com","role":"student","name":"Pandu","interests": ["data","web"]}
```

---

## 4.2 Assessment Lifecycle (3 theoretical + 3 essay + 4 profile)

### POST `/assessments/start` (Bearer)

**Req**

```json
{"track":"general","composition":{"theoretical":3,"essay":3,"profile":4}}
```

**Res 201**

```json
{
  "assessmentId":"asmt_01H...",
  "expiresAt":"2025-10-20T12:00:00Z",
  "questions":[
    {"id":"q_t_1","type":"theoretical","prompt":"...","options":["A","B","C","D"]},
    {"id":"q_e_1","type":"essay","prompt":"Explain ...","rubric":["clarity","accuracy","coherence"]},
    {"id":"q_p_1","type":"profile","prompt":"Rate interest in ML (1-5)","scale":{"min":1,"max":5}}
  ]
}
```

### POST `/assessments/{assessmentId}/responses` (partial OK)

**Req**

```json
{
  "responses":[
    {"questionId":"q_t_1","answer":"B"},
    {"questionId":"q_e_1","answer":"<essay text>"},
    {"questionId":"q_p_1","answer":4}
  ],
  "isFinalChunk": false
}
```

**Res 202**

```json
{"saved":3,"next":"submit when ready"}
```

### POST `/assessments/{assessmentId}/submit`

**Req** `{}`
**Res 202**

```json
{"status":"queued","jobId":"job_9rA..."}
```

### GET `/assessments/{assessmentId}/status`

**Res 200**

```json
{"status":"processing","progress":65,"stages":["rule-score","gpt-essays","rag","fusion"]}
```

### GET `/assessments/{assessmentId}/result`

**Res 200**

```json
{
  "assessmentId":"asmt_01H...",
  "scores":{
    "theoretical":{"correct":2,"total":3,"perItem":[true,false,true]},
    "essays":[{"qid":"q_e_1","score":0.78,"rubric":{"clarity":0.8,"accuracy":0.75,"coherence":0.79}}],
    "profile":{"interests":{"data":"high","web":"medium","ml":"high"}}
  },
  "recommendations":[
    {
      "id":"cred_py_data_101",
      "title":"Data Analysis with Python (MC)",
      "reasoningSummary":"Fusion of essay + theoretical + profile indicates strong fit.",
      "ragTrace":[{"source":"PartnerX Catalog","snippet":"...","url":"..."}]
    }
  ],
  "degraded": false,
  "generatedAt":"2025-10-13T13:05:00Z"
}
```

---

## 4.3 Scores & Recommendations (read-only to students)

### GET `/scores/{assessmentId}`

**Res 200** — same `scores` object as in `/result`.

### GET `/recommendations/{assessmentId}`

**Res 200**

```json
{"items":[{"id":"cred_123","title":"...","rank":1,"reasonShort":"Python theory + data interests"}]}
```

### GET `/recommendations/{assessmentId}/explanations`

**Res 200**

```json
{"summary":"Based on strong Python theory, essays on collaboration, and high data interest..."}
```

---

## 4.4 Question Bank (Admin)

### GET `/questions?type=essay`

**Res 200**

```json
{"items":[{"id":"q_e_1","type":"essay","prompt":"Explain ...","rubric":["clarity","accuracy","coherence"],"active":true}]}
```

### POST `/questions`

**Req**

```json
{"type":"theoretical","prompt":"2+2?","options":["1","2","3","4"],"rules":{"correct":"4"}}
```

**Res 201** `{"id":"q_t_99"}`

### PUT `/forms/assessment-default`

**Req**

```json
{"composition":{"theoretical":3,"essay":3,"profile":4}}
```

**Res 200** `{"ok":true}`

---

## 4.5 Catalog & RAG (Admin/System)

### GET `/catalog/credentials`

**Res 200**

```json
{"items":[{"id":"cred_123","title":"Data Analysis with Python","tags":["python","data"],"provider":"PartnerX","url":"...","active":true}]}
```

### POST `/rag/index/rebuild`

**Res 202** `{"status":"rebuilding","startedAt":"2025-10-13T12:00:00Z"}`

### GET `/rag/index/stats`

**Res 200**

```json
{"embeddings":1240,"model":"text-embedding-3-large","dim":3072,"lastBuild":"2025-10-12T18:00:00Z"}
```

---

## 4.6 Ops, Analytics & Webhooks

### GET `/ops/health` (public)

```json
{"api":"ok","db":"ok","redis":"ok","chroma":"ok"}
```

### GET `/analytics/relevance` (admin)

```json
{"ragRelevanceP95":0.86,"acceptanceRate":0.78}
```

### Webhooks (HMAC)

* `/webhooks/assessment-completed`
* `/webhooks/assessment-failed`

---

## 4.7 Errors (Unified)

**4xx/5xx**

```json
{"error":{"code":"VALIDATION_ERROR","message":"...","fields":{"responses[1].answer":"required"}}}
```

---

# Database Schema (SQL migrations, MVP)

> Postgres 14+. JSONB for flexible rubrics and signals; FK with `ON DELETE CASCADE`; essential indexes for latency/analytics. The async + RAG + fusion design mirrors Section 3 .

```sql
-- 0001_users.sql
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         CITEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('student','admin')),
  name          TEXT,
  interests_json JSONB DEFAULT '{}'::jsonb,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON users (email);

-- 0002_assessments.sql
CREATE TABLE assessments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status          TEXT NOT NULL CHECK (status IN ('draft','queued','processing','done','failed')),
  composition_json JSONB NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  finalized_at    TIMESTAMPTZ
);
CREATE INDEX idx_assessments_user ON assessments(user_id);
CREATE INDEX idx_assessments_status ON assessments(status);

-- 0003_questions.sql
CREATE TABLE questions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type         TEXT NOT NULL CHECK (type IN ('theory','essay','profile')),
  prompt       TEXT NOT NULL,
  options_json JSONB,              -- for MCQ
  rules_json   JSONB,              -- rule-based scoring config
  rubric_json  JSONB,              -- for essays: ["clarity","accuracy","coherence"]
  active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_questions_active_type ON questions(active, type);

-- 0004_assessment_questions.sql (snapshot)
CREATE TABLE assessment_questions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id  UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  question_id    UUID REFERENCES questions(id),
  type           TEXT NOT NULL CHECK (type IN ('theory','essay','profile')),
  order_no       INT NOT NULL,
  prompt_snapshot TEXT NOT NULL,
  options_snapshot JSONB,
  rubric_snapshot  JSONB
);
CREATE INDEX idx_aq_assessment ON assessment_questions(assessment_id);

-- 0005_responses.sql
CREATE TABLE responses (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id           UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  assessment_question_id  UUID NOT NULL REFERENCES assessment_questions(id) ON DELETE CASCADE,
  answer_text    TEXT,
  answer_option  TEXT,
  answer_numeric NUMERIC,
  submitted_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_responses_assessment ON responses(assessment_id);

-- 0006_scores.sql
CREATE TABLE scores (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id       UUID UNIQUE NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  theory_score_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
  profile_signals_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  essay_scores_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 0007_credentials.sql (catalog for RAG)
CREATE TABLE credentials (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title      TEXT NOT NULL,
  provider   TEXT,
  tags       TEXT[],
  url        TEXT,
  desc       TEXT,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_credentials_active ON credentials(active);
CREATE INDEX idx_credentials_tags ON credentials USING GIN (tags);

-- 0008_embeddings_meta.sql
CREATE TABLE embeddings_meta (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  credential_id  UUID NOT NULL REFERENCES credentials(id) ON DELETE CASCADE,
  embedding_id   TEXT NOT NULL,       -- Chroma key
  model          TEXT NOT NULL,
  dim            INT NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_embed_credential ON embeddings_meta(credential_id);

-- 0009_recommendations.sql
CREATE TABLE recommendations (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id  UUID UNIQUE NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  summary_text   TEXT NOT NULL,       -- fusion of essay + theory + profile
  degraded       BOOLEAN NOT NULL DEFAULT FALSE,
  generated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recommendation_items (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_id  UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
  credential_id      UUID NOT NULL REFERENCES credentials(id),
  rank               INT NOT NULL,
  reason_short       TEXT
);
CREATE INDEX idx_rec_items_rec ON recommendation_items(recommendation_id);

CREATE TABLE rag_traces (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_id  UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
  item_id            UUID NOT NULL REFERENCES recommendation_items(id) ON DELETE CASCADE,
  source_title       TEXT,
  snippet            TEXT,
  source_url         TEXT,
  score              NUMERIC
);
CREATE INDEX idx_rag_traces_rec ON rag_traces(recommendation_id);

-- 0010_jobs.sql (async pipeline audit)
CREATE TABLE jobs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  type         TEXT NOT NULL CHECK (type IN ('gpt','rag','fusion')),
  status       TEXT NOT NULL CHECK (status IN ('queued','processing','done','failed')),
  attempts     INT NOT NULL DEFAULT 0,
  last_error   TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jobs_assessment ON jobs(assessment_id);
CREATE INDEX idx_jobs_status_type ON jobs(status, type);

-- 0011_audit_metrics.sql
CREATE TABLE audit_events (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor      TEXT,
  action     TEXT,
  resource   TEXT,
  meta_json  JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE metrics (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL,          -- e.g., "rag_latency_ms","queue_depth"
  value      NUMERIC NOT NULL,
  labels     JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_metrics_name_time ON metrics(name, created_at);
```

**Notes**

* `scores.assessment_id` is `UNIQUE` → exactly one score record per assessment.
* `recommendations.assessment_id` is `UNIQUE` → one fused summary per assessment.
* `assessment_questions` snapshots the text/rubric/options to preserve integrity if the bank changes.
* `jobs` table mirrors Redis queue state for auditability and debugging (optional but helpful for MVP SLOs that came from your session) .

---

