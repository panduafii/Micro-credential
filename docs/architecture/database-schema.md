# Database Schema
```sql
-- Roles and Users
CREATE TABLE role_catalog (
  id UUID PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  description TEXT,
  skills_profile JSONB,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  email CITEXT UNIQUE NOT NULL,
  role VARCHAR(32) NOT NULL CHECK (role IN ('student','advisor','admin')),
  profile JSONB,
  status VARCHAR(16) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Questions and assessments
CREATE TABLE questions (
  id UUID PRIMARY KEY,
  role_id UUID REFERENCES role_catalog(id),
  question_type VARCHAR(32) NOT NULL CHECK (question_type IN ('multiple_choice','essay','profile')),
  prompt TEXT NOT NULL,
  choices JSONB,
  rubric JSONB NOT NULL,
  weight NUMERIC(5,2) NOT NULL,
  version VARCHAR(32) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE assessments (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  role_id UUID REFERENCES role_catalog(id),
  status VARCHAR(24) NOT NULL CHECK (status IN ('in_progress','awaiting_async','completed','failed')),
  degraded BOOLEAN NOT NULL DEFAULT FALSE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE assessment_question_snapshots (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  question_id UUID NOT NULL,
  prompt TEXT NOT NULL,
  rubric JSONB NOT NULL,
  question_type VARCHAR(32) NOT NULL,
  choices JSONB,
  weight NUMERIC(5,2),
  version VARCHAR(32) NOT NULL,
  UNIQUE (assessment_id, question_id)
);

CREATE TABLE assessment_responses (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  question_snapshot_id UUID REFERENCES assessment_question_snapshots(id),
  answer JSONB NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (assessment_id, question_snapshot_id)
);

-- Scoring
CREATE TABLE rule_scores (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  question_snapshot_id UUID REFERENCES assessment_question_snapshots(id),
  score NUMERIC(5,2) NOT NULL,
  explanation TEXT,
  rules_applied JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (assessment_id, question_snapshot_id)
);

CREATE TABLE essay_scores (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  question_snapshot_id UUID REFERENCES assessment_question_snapshots(id),
  score NUMERIC(5,2),
  model VARCHAR(64) NOT NULL,
  prompt_version VARCHAR(32) NOT NULL,
  latency_ms INTEGER,
  cost_cents NUMERIC(7,2),
  response_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (assessment_id, question_snapshot_id)
);

-- Recommendations
CREATE TABLE credential_catalog (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  skills TEXT[],
  provider TEXT,
  metadata JSONB,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE embedding_artifacts (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(32) NOT NULL,
  entity_id UUID NOT NULL,
  provider VARCHAR(32) NOT NULL,
  vector VECTOR(384),
  raw_embedding BYTEA,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_type, entity_id, provider)
);

CREATE TABLE recommendations (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id) UNIQUE,
  summary TEXT,
  degraded BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(24) NOT NULL CHECK (status IN ('pending','ready','failed')),
  generated_at TIMESTAMPTZ,
  metrics JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE recommendation_items (
  id UUID PRIMARY KEY,
  recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
  credential_id UUID REFERENCES credential_catalog(id),
  title TEXT NOT NULL,
  confidence NUMERIC(5,3) NOT NULL,
  rationale TEXT,
  source_trace_ids UUID[],
  position INTEGER NOT NULL,
  UNIQUE (recommendation_id, credential_id)
);

CREATE TABLE rag_traces (
  id UUID PRIMARY KEY,
  recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
  source_uri TEXT NOT NULL,
  snippet TEXT NOT NULL,
  similarity NUMERIC(5,3) NOT NULL,
  embedding_artifact_id UUID REFERENCES embedding_artifacts(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Async jobs and notifications
CREATE TABLE async_jobs (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  job_type VARCHAR(32) NOT NULL,
  status VARCHAR(24) NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  payload JSONB,
  error_payload JSONB,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ
);

CREATE TABLE webhook_events (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  event_type VARCHAR(32) NOT NULL,
  payload JSONB NOT NULL,
  status VARCHAR(24) NOT NULL,
  response_code INTEGER,
  last_attempt TIMESTAMPTZ,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Feedback, auditing, metrics
CREATE TABLE recommendation_feedback (
  id UUID PRIMARY KEY,
  recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
  submitted_by UUID REFERENCES users(id),
  submitted_by_role VARCHAR(16) NOT NULL,
  relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 5),
  acceptance_status VARCHAR(16),
  comments TEXT,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  actor_id UUID,
  actor_role VARCHAR(16),
  action VARCHAR(64) NOT NULL,
  resource_type VARCHAR(32) NOT NULL,
  resource_id UUID,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE metric_snapshots (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  metric_type VARCHAR(32) NOT NULL,
  value NUMERIC(12,3) NOT NULL,
  context JSONB,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX idx_assessments_user ON assessments(user_id);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_async_jobs_status_next_run ON async_jobs(status, next_run_at);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendation_items_position ON recommendation_items(recommendation_id, position);
CREATE INDEX idx_embedding_artifacts_provider ON embedding_artifacts(provider);
CREATE INDEX idx_recommendation_feedback_reco ON recommendation_feedback(recommendation_id);
```
