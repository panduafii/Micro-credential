Great question — the earlier table was just a **summary**. Below is a **complete API inventory (v1)** for your MVP, organized by domain, with concise request/response notes so engineering can implement straight away.

# Complete API List (v1)

*All endpoints are prefixed with `/api/v1`. Auth is JWT (Bearer). Admin endpoints require `role=admin`.*

## 1) Auth & Users

| Endpoint                | Method | Auth   | Purpose                                           |
| ----------------------- | ------ | ------ | ------------------------------------------------- |
| `/auth/register`        | POST   | Public | Create account (student/admin via invite or code) |
| `/auth/login`           | POST   | Public | Obtain JWT access/refresh tokens                  |
| `/auth/refresh`         | POST   | Public | Refresh access token                              |
| `/auth/logout`          | POST   | Bearer | Invalidate refresh token (server-side blacklist)  |
| `/users/me`             | GET    | Bearer | Get current profile (id, email, role)             |
| `/users/me`             | PUT    | Bearer | Update profile (name, interests)                  |
| `/users/{userId}`       | GET    | Admin  | Admin view of a user                              |
| `/users/{userId}/roles` | PUT    | Admin  | Promote/demote user roles                         |

## 2) Assessment Lifecycle (10 questions: 3 theoretical, 3 essay, 4 profile/interest)

| Endpoint                                | Method | Auth   | Purpose                                                                           |            |      |                        |
| --------------------------------------- | ------ | ------ | --------------------------------------------------------------------------------- | ---------- | ---- | ---------------------- |
| `/assessments/start`                    | POST   | Bearer | Create a new assessment session → returns `assessmentId` and question set (3+3+4) |            |      |                        |
| `/assessments/{assessmentId}`           | GET    | Bearer | Get assessment meta & current state                                               |            |      |                        |
| `/assessments/{assessmentId}/questions` | GET    | Bearer | Fetch question set (id, type, payload)                                            |            |      |                        |
| `/assessments/{assessmentId}/responses` | POST   | Bearer | Submit responses (can be partial or full)                                         |            |      |                        |
| `/assessments/{assessmentId}/submit`    | POST   | Bearer | Finalize submission → enqueues GPT/RAG jobs                                       |            |      |                        |
| `/assessments/{assessmentId}/status`    | GET    | Bearer | Async status: `queued                                                             | processing | done | failed` (+ progress %) |
| `/assessments/{assessmentId}/result`    | GET    | Bearer | Final scored result + recommendation summary (RAG+GPT fusion)                     |            |      |                        |
| `/assessments/{assessmentId}/cancel`    | POST   | Bearer | Cancel assessment if still processing                                             |            |      |                        |

## 3) Scoring & Recommendations (read-only for students, write by workers)

| Endpoint                                       | Method | Auth   | Purpose                                                          |
| ---------------------------------------------- | ------ | ------ | ---------------------------------------------------------------- |
| `/scores/{assessmentId}`                       | GET    | Bearer | Get breakdown: theoretical (rule), profiles (rule), essays (GPT) |
| `/recommendations/{assessmentId}`              | GET    | Bearer | Get recommendations (top N) + RAG trace (sources)                |
| `/recommendations/{assessmentId}/explanations` | GET    | Bearer | Summarized rationale fusing **essay + theoretical + profile**    |
| `/recommendations/{assessmentId}/feedback`     | POST   | Bearer | User/advisor feedback (helpfulness, acceptance)                  |

## 4) Question Bank (Admin)

| Endpoint                    | Method | Auth  | Purpose                                 |       |           |
| --------------------------- | ------ | ----- | --------------------------------------- | ----- | --------- |
| `/questions`                | GET    | Admin | List questions (filters: type=`theory   | essay | profile`) |
| `/questions`                | POST   | Admin | Create question (schema varies by type) |       |           |
| `/questions/{questionId}`   | GET    | Admin | Get question detail                     |       |           |
| `/questions/{questionId}`   | PUT    | Admin | Update question                         |       |           |
| `/questions/{questionId}`   | DELETE | Admin | Soft delete/disable                     |       |           |
| `/forms/assessment-default` | GET    | Admin | Get current default 3/3/4 composition   |       |           |
| `/forms/assessment-default` | PUT    | Admin | Update composition & selection rules    |       |           |

## 5) Content & RAG (Admin / System)

| Endpoint                    | Method | Auth  | Purpose                                             |
| --------------------------- | ------ | ----- | --------------------------------------------------- |
| `/catalog/credentials`      | GET    | Admin | List micro-credentials (source, title, tags)        |
| `/catalog/credentials`      | POST   | Admin | Upsert credential metadata (for RAG grounding)      |
| `/catalog/credentials/{id}` | GET    | Admin | Get credential                                      |
| `/catalog/credentials/{id}` | PUT    | Admin | Update credential                                   |
| `/catalog/credentials/{id}` | DELETE | Admin | Soft delete                                         |
| `/rag/index/rebuild`        | POST   | Admin | Rebuild embedding index from catalog                |
| `/rag/index/stats`          | GET    | Admin | Embedding counts, last build time, dimension, model |

## 6) Monitoring, Logs & Ops (Admin)

| Endpoint                    | Method | Auth   | Purpose                                           |
| --------------------------- | ------ | ------ | ------------------------------------------------- |
| `/ops/health`               | GET    | Public | Health probe (db/redis/chroma)                    |
| `/ops/metrics`              | GET    | Admin  | Basic metrics (latency, queue depth, token usage) |
| `/ops/queues`               | GET    | Admin  | Queue stats (pending, failed, retries)            |
| `/ops/queues/retry/{jobId}` | POST   | Admin  | Retry failed job                                  |
| `/ops/queues/kill/{jobId}`  | POST   | Admin  | Kill job                                          |
| `/ops/audit`                | GET    | Admin  | Security & change audit events                    |

## 7) Webhooks (Server → Client integration, optional)

| Endpoint                         | Method | Auth | Purpose                                          |
| -------------------------------- | ------ | ---- | ------------------------------------------------ |
| `/webhooks/assessment-completed` | POST   | HMAC | Notify client app when async scoring+RAG is done |
| `/webhooks/assessment-failed`    | POST   | HMAC | Notify failures with error code & retry hint     |

## 8) Admin Analytics (MVP-level, no heavy BI)

| Endpoint               | Method | Auth  | Purpose                                      |
| ---------------------- | ------ | ----- | -------------------------------------------- |
| `/analytics/usage`     | GET    | Admin | Calls/day, unique users, completion rate     |
| `/analytics/relevance` | GET    | Admin | RAG relevance score, acceptance rate         |
| `/analytics/costs`     | GET    | Admin | GPT token costs, embedding costs (estimates) |

---

## Key Payload Sketches (concise)

### Start Assessment

**POST** `/api/v1/assessments/start`

```json
{
  "track": "general", 
  "composition": {"theoretical":3, "essay":3, "profile":4}
}
```

**200**

```json
{
  "assessmentId": "asmt_01H...",
  "expiresAt": "2025-10-20T12:00:00Z",
  "questions": [
    {"id":"q_t_1","type":"theoretical","prompt":"...","options":["A","B","C","D"]},
    {"id":"q_e_1","type":"essay","prompt":"Explain ..."},
    {"id":"q_p_1","type":"profile","prompt":"Rate interest in ... (1-5)"}
  ]
}
```

### Submit Responses

**POST** `/api/v1/assessments/{assessmentId}/responses`

```json
{
  "responses": [
    {"questionId":"q_t_1","answer":"B"},
    {"questionId":"q_e_1","answer":"<essay text>"},
    {"questionId":"q_p_1","answer":4}
  ],
  "isFinalChunk": false
}
```

### Finalize & Enqueue

**POST** `/api/v1/assessments/{assessmentId}/submit`

```json
{"submit": true}
```

**202**

```json
{"status":"queued","jobId":"job_9rA..."}
```

### Result (Fusion + RAG Trace)

**GET** `/api/v1/assessments/{assessmentId}/result`

```json
{
  "assessmentId":"asmt_01H...",
  "scores":{
    "theoretical":{"correct":2,"total":3},
    "essays":[{"qid":"q_e_1","score":0.78,"rubric":{"clarity":0.8,"accuracy":0.75}}],
    "profile":{"interests":{"data":"high","web":"medium","ml":"high"}}
  },
  "recommendations":[
    {
      "id":"cred_py_data_101",
      "title":"Data Analysis with Python (MC)",
      "reasoningSummary":"Strong Python theory + high data interest + essay emphasis on collaboration.",
      "ragTrace":[
        {"source":"PartnerX Catalog","snippet":"...","url":"..."}
      ]
    }
  ],
  "status":"done",
  "generatedAt":"2025-10-13T13:05:00Z"
}
```

---

## Conventions & Cross-Cutting Concerns

**Versioning**

* Prefix all routes with `/api/v1`. Breaking changes → `/api/v2`.

**Pagination & Filtering**

* List endpoints accept: `?page=1&pageSize=20&sort=-createdAt&filter[type]=essay`.

**Errors**

* Consistent error body:

```json
{"error":{"code":"VALIDATION_ERROR","message":"...","fields":{"responses[1].answer":"required"}}}
```

**Security**

* JWT Bearer; roles: `student`, `admin`.
* PII encryption at rest (Postgres).
* API keys (GPT/VectorDB) via env vars/secret manager.

**Rate Limits**

* Default: 60 req/min per token; stricter on admin write operations.

**Idempotency**

* Use `Idempotency-Key` header for `responses` and `submit` endpoints.

**Async Processing**

* Redis-backed queue; retries (3) with exponential backoff.
* `/status` returns queue state and progress (0–100).

**Observability**

* Request IDs, tracing, latency histograms, token accounting.

---

## Quick Sequence (Happy Path)

1. `POST /assessments/start` → returns questions
2. `POST /assessments/{id}/responses` (stream/partial OK)
3. `POST /assessments/{id}/submit` → queue GPT (essays) + RAG retrieval
4. `GET /assessments/{id}/status` → `done`
5. `GET /assessments/{id}/result` → scores + recommendations + fusion summary

---


