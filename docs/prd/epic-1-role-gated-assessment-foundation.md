# Epic 1 Role-Gated Assessment Foundation
**Goal:** Establish the FastAPI monorepo, secure auth, role catalog, and question management so students must pick a target role before receiving a 10-question bundle.

## Story 1.1 Monorepo Baseline and Auth Skeleton
As a developer, I want a FastAPI monorepo with JWT auth scaffolding so that we can enforce secure, role-aware access across services.

### Acceptance Criteria
1. Repo contains FastAPI app, worker stub, shared models, and Docker Compose with Postgres/Redis.
2. JWT auth middleware issues and validates tokens with role claims (`student`, `advisor`, `admin`).
3. CI pipeline runs lint and unit tests on pull requests.
4. Health endpoint and logging format follow observability conventions.

## Story 1.2 Track Catalog Management
As an admin, I want to define and maintain role/track metadata so that assessments can tailor content to the selected focus area.

### Acceptance Criteria
1. `/api/v1/tracks` CRUD endpoints exist (admin-only) with audit logging.
2. Track schema captures name, description, skill focus tags, and question mix overrides.
3. GET endpoints expose active tracks for student preview.
4. Track seeds load during migration with examples (Backend Engineer, Data Analyst).

## Story 1.3 Question Bank CRUD and Versioning
As an admin, I want to manage question pools per track so that theoretical, essay, and profile questions stay aligned with role requirements.

### Acceptance Criteria
1. Question CRUD endpoints support type, prompt, track tags, and rubric/rules payloads.
2. Soft delete keeps historical data while removing items from active rotations.
3. Version snapshot stored when questions change.
4. Unit tests cover rule parsing and rubric validation.

## Story 1.4 Role-Gated Assessment Start
As a student, I want to start an assessment by choosing a role so that I receive questions aligned with that track.

### Acceptance Criteria
1. `POST /api/v1/assessments/start` requires `trackId` and validates eligibility.
2. Endpoint assembles three theoretical, three essay, and four profile questions mapped to the selected track, snapshots prompts, and returns bundle <400 ms p95.
3. Partial response tokens created with expiry and resume capability.
4. API captures analytics event tying student, track, and assessment ID.
