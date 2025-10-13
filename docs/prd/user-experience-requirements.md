# User Experience Requirements

## User Journeys & Flows
- **Student Path (Entry → Exit):** Select role/track → preview question composition → complete hybrid assessment (supporting save/resume) → receive async status updates → review results and provide feedback. Edge cases include expired assessments (prompt to restart) and degraded recommendations (labelled with fallback messaging).
- **Advisor Path:** Authenticate with advisor role → view cohort dashboard → inspect individual student recommendations with RAG traces → record accept/reject feedback → flag degraded cases for follow-up. Handles scenario where recommendations are pending by surfacing in-progress status.
- **Admin Path:** Login with admin role → manage tracks/questions/catalog → monitor system health metrics → trigger embedding rebuilds. Includes guardrails for publishing changes while jobs are running.

## Usability Requirements
- Accessibility target WCAG AA; leverage semantic HTML, keyboard navigation, and high-contrast defaults.
- Responsive web layout optimized for desktop and tablet; critical student/advisor views scale to mobile.
- Loading states communicate async progress (e.g., “Scoring essays — up to 10 seconds remaining”).
- Feedback prompts after recommendation review capture qualitative insights with minimal input friction.

## Error States & Recovery
- Assessment submission failures provide retry guidance and contact path; auto-resume if partial data saved.
- Queue or GPT/RAG outages trigger degraded-mode banners with timestamp and expected resolution.
- Admin actions validate dependencies (e.g., cannot delete active question without replacement) and log errors with remediation steps.
- Webhook or notification failures surface in ops dashboard with ability to resend.

## UI Design Goals
Deliver lightweight, role-aware web dashboards that surface assessment progress, scoring breakdowns, and recommendation rationales so students, advisors, and admins can trust backend outputs without dense configuration screens.

## Key Interaction Paradigms
- Role-gated navigation (student vs advisor vs admin) with JWT SSO to surface only relevant data.
- Async-status indicators translating backend job states into plain-language progress checkpoints.
- Recommendation cards exposing RAG source snippets alongside summary scores to uphold transparency.
- Minimal data entry; focus on viewing results, acknowledging recommendations, and capturing feedback.

## Core Screens and Views
- Student Assessment Status and Result page (progress, scores, recommendation summary, feedback action).
- Advisor Recommendation Review console (per-student history, rationale, accept/reject feedback).
- Admin Catalog and Question Manager (track definitions, question bank activation toggles, index rebuild triggers).
- Operations Health dashboard (queue depth, latency metrics, degraded-mode alerts).

## Accessibility: WCAG AA (target)
Commit to WCAG AA conformance so internal dashboards can graduate to student-facing experiences without rework; assume standard responsive web controls.

## Branding
Neutral light theme with sans-serif typography and placeholders for institutional logos; finalize palette once university partner is confirmed.

## Target Device and Platforms: Web Responsive
Expect advisors/admins on desktop and students on mobile; responsive web ensures a single codebase covers both.
