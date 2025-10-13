# Micro-Credential Assessment Backend Product Requirements Document (PRD)

## 1. Goals and Background Context

### Goals
- Deliver an assessment backend that lets IT students pinpoint skill gaps and receive targeted micro-credential guidance in one sitting.
- Equip academic advisors with evidence-based profiles and recommendations so they can coach students with confidence.
- Stand up a stable, extensible service that can grow into semantic recommendations and richer analytics after the MVP.

### Background Context
Micro-credentialing efforts today lean on ad-hoc self-assessments, leaving students unsure which skills to build next and giving advisors limited evidence for coaching. This MVP tackles that gap by providing a 10-question hybrid scoring assessment (rule-based + GPT essays) and simple lookup recommendations, all scoped to what a solo developer can deliver in four weeks. The work draws directly from the 2025-10-11 brainstorming session and the v1.0 PRD, both of which emphasized credibility, speed, and tight scope as the path to trust and adoption.

### Change Log
| Date       | Version | Description                                                            | Author |
|------------|---------|------------------------------------------------------------------------|--------|
| 2025-10-11 | v1.1    | Migrated legacy PRD into template structure and aligned with brainstorm insights | John   |
| 2025-10-11 | v1.0    | Initial PRD authored outside template (referenced as `mvp-microcredential-backend-prd.md`) | Mary   |

## 2. Requirements

### Functional Requirements
1. FR1: Issue JWT-based authentication and session management for students, advisors, and partner frontends.
2. FR2: Provide `POST /assessments/start` to capture role selection, initialize a 10-question session, and return the assessment identifier with expiry.
3. FR3: Serve the next unanswered question via `GET /assessments/{assessmentId}/next`, sequencing MCQ, essay, and interest prompts with associated metadata.
4. FR4: Accept answers through `POST /assessments/{assessmentId}/answer`, performing immediate rule-based scoring for MCQ items and enqueuing essay responses to an async GPT scoring queue (no synchronous execution path).
5. FR5: Finalize assessments with `POST /assessments/{assessmentId}/complete`, marking the assessment as “processing” while awaiting async GPT results and emitting a status token for clients to poll.
6. FR6: Expose `GET /assessments/{assessmentId}/status` (or equivalent event channel) so clients can monitor queue progress and handle delays gracefully.
7. FR7: Publish skill profiles via `GET /profiles/{assessmentId}` once async scoring finishes, returning overall score, domain breakdown, strengths, improvements, and confidence indicators.
8. FR8: Deliver recommendation bundles through `GET /recommendations?assessmentId=…`, mapping role, score band, and interests to 2–3 micro-credentials once the profile is ready.
9. FR9: Support seeding and refreshing of question banks and recommendation tables using lightweight scripts or fixtures (no UI admin tooling in MVP).

### Non-Functional Requirements
1. NFR1: Maintain ≤500 ms p95 latency for REST endpoints (queue submission only) and ≥95% uptime during the pilot.
2. NFR2: Enforce security with bcrypt-hashed credentials, JWT access tokens with refresh flow, and rate limiting on auth endpoints.
3. NFR3: Guarantee queue durability with retry and exponential backoff policies; surface queue depth/age metrics and raise alerts when GPT results exceed defined SLAs.
4. NFR4: Communicate asynchronous state clearly—status endpoint must reflect pending, in-progress, and completed phases, and clients need guidance on retry intervals.
5. NFR5: Limit monthly GPT spend to ≤$5 by capping prompts (~5 per assessment) and monitoring usage.
6. NFR6: Store only necessary PII, provide deletion/export hooks to satisfy baseline GDPR expectations, and log access for auditability.
7. NFR7: Instrument structured logging plus metrics for request rates, GPT job throughput, queue depth, and completion latency to uphold the async workflow.
