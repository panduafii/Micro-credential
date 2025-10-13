Excellent 👏
We’ll now move to **Section 2: Functional and Non-Functional Requirements** — the backbone of your PRD, describing *what* the system must do and *how* it should perform.

Below is your **drafted Section 2**, based on the finalized Section 1 and your brainstorming session results.

---

## **Section 2: Requirements**

---

### **2.1 Functional Requirements**

#### **2.1.1 Assessment Flow**

| ID   | Requirement                             | Description                                                                                                                                              | Priority |
| ---- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| FR-1 | **User Authentication (Async)**         | System must provide JWT-based authentication via FastAPI for students and admins, enabling secure session handling.                                      | High     |
| FR-2 | **Assessment API (10 Questions)**       | Backend provides endpoints for delivering and submitting assessments composed of **3 theoretical**, **3 essay**, and **4 profile & interest** questions. | High     |
| FR-3 | **Rule-Based Scoring Module**           | Theoretical and profile questions scored instantly using predefined rulesets (JSON-configurable).                                                        | High     |
| FR-4 | **Async GPT Evaluation**                | Essay questions are sent to GPT asynchronously for semantic evaluation, with results stored in Postgres once completed.                                  | High     |
| FR-5 | **RAG-Powered Recommendation Engine**   | RAG (Retrieval-Augmented Generation) retrieves relevant micro-credential metadata (via ChromaDB) and generates recommendations.                          | Critical |
| FR-6 | **Summarization Engine (Fusion Layer)** | Summarizes recommendation by integrating insights from **essay**, **theoretical**, and **profile/interest** results.                                     | Critical |
| FR-7 | **Sync Fallback Mode**                  | When GPT or RAG is unavailable, fallback to static lookup or cached recommendation data.                                                                 | Medium   |
| FR-8 | **Admin Dashboard API**                 | Allows admins to view submissions, latency logs, and scoring accuracy reports.                                                                           | Medium   |
| FR-9 | **Result Storage and History**          | Each assessment and generated recommendation is stored for analytics and future validation.                                                              | High     |

---

#### **2.1.2 Data Management**

| ID    | Requirement                   | Description                                                                                          | Priority |
| ----- | ----------------------------- | ---------------------------------------------------------------------------------------------------- | -------- |
| FR-10 | **Database Persistence**      | Use PostgreSQL for main data storage, including user profiles, question bank, results, and metadata. | High     |
| FR-11 | **Embedding Storage**         | Store RAG embeddings and metadata in ChromaDB for semantic retrieval.                                | Critical |
| FR-12 | **Queue Management**          | Use Redis to manage async tasks and retries for GPT calls and RAG lookups.                           | High     |
| FR-13 | **Logging and Observability** | Capture latency metrics, GPT token usage, and RAG retrieval accuracy.                                | High     |

---

#### **2.1.3 API Endpoints (Summary)**

| Endpoint                  | Method   | Purpose                                              |
| ------------------------- | -------- | ---------------------------------------------------- |
| `/auth/register`          | POST     | Register new student or admin                        |
| `/auth/login`             | POST     | Generate JWT for session                             |
| `/assessment/start`       | GET      | Retrieve question set (3+3+4)                        |
| `/assessment/submit`      | POST     | Submit responses for async processing                |
| `/assessment/status/{id}` | GET      | Check completion or queue state                      |
| `/assessment/result/{id}` | GET      | Retrieve scored results and RAG-based recommendation |
| `/admin/logs`             | GET      | Retrieve latency and performance logs                |
| `/admin/questions`        | POST/PUT | Manage question bank (future version)                |

---

### **2.2 Non-Functional Requirements**

#### **2.2.1 Performance**

| ID    | Requirement           | Metric                                                    |
| ----- | --------------------- | --------------------------------------------------------- |
| NFR-1 | **Async Latency**     | Rule-based response < 500 ms; GPT evaluation < 10 seconds |
| NFR-2 | **Concurrent Users**  | System handles ≥ 100 concurrent assessments               |
| NFR-3 | **Queue Reliability** | ≥ 99% success rate for Redis task completion              |
| NFR-4 | **RAG Latency**       | ≤ 1.5 seconds average retrieval per query                 |

---

#### **2.2.2 Scalability**

* System designed to scale horizontally via FastAPI workers (Uvicorn + Gunicorn).
* Redis queue and ChromaDB can scale independently as workloads increase.
* Database indexing ensures query times stay consistent up to 10,000 assessments.

---

#### **2.2.3 Security**

| ID    | Requirement                        | Description                                                          |
| ----- | ---------------------------------- | -------------------------------------------------------------------- |
| NFR-5 | **Authentication & Authorization** | All endpoints secured via JWT; role-based access for admin features. |
| NFR-6 | **Data Privacy**                   | No raw essay data shared externally; PII encrypted at rest.          |
| NFR-7 | **API Key Management**             | GPT and RAG credentials stored securely using environment variables. |

---

#### **2.2.4 Reliability and Fault Tolerance**

* Fallback mechanism activates static recommendation lookup when RAG fails.
* Automatic retries for GPT evaluation up to 3 times per task.
* Queue monitoring dashboard tracks failed and pending tasks.

---

#### **2.2.5 Maintainability**

* Modular codebase (FastAPI routers + service layers).
* Configurable question banks (JSON or YAML).
* Comprehensive logging for debugging and performance optimization.
* Automated tests for API endpoints and scoring logic.

---

#### **2.2.6 Usability**

* Clear API documentation with examples (OpenAPI / Swagger UI).
* Simple JSON payload structure for client integration.
* User feedback messages for async completion and error handling.

---

### **2.3 Constraints**

| Type           | Constraint                                                     |
| -------------- | -------------------------------------------------------------- |
| **Time**       | 4-week MVP development cycle                                   |
| **Budget**     | ≤ $5 per 500 GPT assessments                                   |
| **Resources**  | 1 backend engineer, 1 data engineer, shared analyst/QA support |
| **Technology** | Python 3.11+, FastAPI, PostgreSQL, Redis, ChromaDB, OpenAI API |

---

### **2.4 Dependencies**

| Dependency                | Purpose                            |
| ------------------------- | ---------------------------------- |
| **OpenAI GPT API**        | Essay evaluation and summarization |
| **ChromaDB**              | Embedding store for RAG retrieval  |
| **Redis**                 | Queue and async job management     |
| **PostgreSQL**            | Persistent data layer              |
| **Pydantic / SQLAlchemy** | Schema and ORM handling            |
| **FastAPI**               | Core framework for API operations  |

---

### **2.5 Acceptance Criteria**

1. Students can complete the full 10-question test, receive results asynchronously, and obtain recommendations.
2. Recommendations must explicitly cite or be traceable to essay, theoretical, and profile data sources.
3. Average async completion time ≤ 10 seconds.
4. RAG retrieval accuracy validated with at least 85% relevance on test set.
5. Fallback mode (static lookup) correctly activates during RAG or GPT downtime.
6. All endpoints return proper JSON schemas and error codes.

---

