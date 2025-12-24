# Goals and Background Context

## Goals
- Deliver an async-first FastAPI backend that completes hybrid (rule + GPT) scoring within targeted latency windows.
- Provide RAG-backed micro-credential recommendations that advisors and students can immediately act on.
- Ship an auditable MVP foundation that captures assessment, scoring, and recommendation data for future analytics.
- Ensure explainable outputs with traceable sources so stakeholders can validate AI-driven decisions.

## Problem Statement
Universities and credential providers rely on static assessments and generic advising, leaving students without actionable learning paths and advisors without defensible recommendations. Discovery workshops with our academic partner revealed that advisors currently spend 6–10 days synthesizing results manually, and 80% of surveyed students reported generic course suggestions that did not match their skill interests. This PRD delivers an AI-powered backend that collects hybrid responses, scores them credibly, and recommends micro-credentials with transparent sources so institutions can shorten guidance cycles to <48 hours while increasing student trust.

## Background Context
The AI-powered Micro-Credential Assessment Backend serves universities and credential providers that need personalized, defensible learning guidance. Current static assessments fail to connect demonstrated skills to actionable micro-credentials, eroding advisor trust and student momentum. The four-week MVP focuses on a 10-question hybrid assessment (three theoretical, three essay, and four profile/interest items) so rule-based scoring can deliver instant feedback while GPT handles nuanced essay evaluation. RAG is mandatory to align recommendations with catalog context, and Redis-backed async processing keeps throughput high without overcomplicating operations. By pairing deterministic scoring with explainable AI summaries, the service gives advisors and learners confidence in guidance while keeping infrastructure lean and extensible.

## Target Users

| User Type                         | Needs                                                                       | Success Criteria                                         |
| --------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Students (Primary)**            | Quick, accurate skill evaluation and personalized micro-credential guidance | Receives clear, relevant recommendations with confidence |
| **Academic Advisors (Secondary)** | Reliable AI-based recommendation to support learning path decisions         | AI suggestions are explainable and context-matched       |
| **Developers / Admins**           | Scalable, low-maintenance backend integration                               | API endpoints are stable, documented, and extensible     |

## User Research & Insights
- **First Principles Workshop (2025-10-11):** Facilitated session with advisors highlighted the need for asynchronous scoring, RAG-backed recommendations, and a 10-minute completion window (see `docs/brainstorming-session-results.md`).
- **Advisor Interviews (n=5):** Surface pain of manual spreadsheet tracking and delayed recommendations, with a target to reduce turnaround to <2 days.
- **Student Feedback (pilot cohort n=12):** Reported frustration with generic advice; 70% requested personalized micro-credential suggestions tied to their interests.
- **Key Insight:** Mandatory RAG integration is necessary because a limited question bank alone cannot deliver trusted contextual recommendations.

## Competitive & Market Context
- Traditional LMS assessments (e.g., Canvas quizzes) focus on grading but lack personalized credential mapping.
- Commercial advising tools prioritize dashboards over AI-backed recommendations, leaving gaps in explainability and asynchronous handling.
- Differentiation: This backend combines rule scoring, GPT evaluation, and RAG with transparent traces, enabling institutions to launch contextual guidance without building full-stack systems.

## Business Goals & Success Metrics

| Objective                                          | Success Metric                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| Deliver reliable async API for assessment flow     | Average latency < 500 ms for rule-based scoring; < 10 s for GPT tasks  |
| Ensure recommendation credibility and transparency | ≥ 85% relevance in RAG validation tests with explainable context trace |
| Guarantee operational reliability                  | ≥ 99% uptime and successful async queue completion rate                |
| Validate user satisfaction and adoption            | ≥ 70% student satisfaction, ≥ 80% advisor trust in recommendations     |

## Impact & Differentiation Summary
- Reduce advisor turnaround time from 6–10 days to <48 hours by automating scoring and recommendation assembly.
- Increase advisor trust scores to ≥80% through explainable RAG traces.
- Deliver personalized recommendations aligned to selected roles, addressing the 70% student demand for role-specific guidance captured in pilot feedback.
- Provide an extensible foundation for future adaptive learning features without overexpanding MVP scope.

## MVP Scope

**In Scope**
- Async FastAPI backend with hybrid (rule + GPT) scoring logic.
- RAG-powered recommendations sourced from curated micro-credential catalog with traceable snippets.
- 3 theoretical, 3 essay, and 4 profile/interest questions tailored to a selected role.
- Redis queue, worker processes, and degraded-mode fallbacks for resilience.
- Postgres persistence, Chroma (or PGVector) embeddings, and audit logging.
- Basic admin endpoints for track/question/catalog management plus metrics collection.

**Out of Scope / Deferred**
- Advanced semantic analytics dashboards beyond basic health metrics.
- Dynamic advisor-facing question authoring UI (manual data loading for MVP).
- Adaptive course orchestration and continuous learning loops.
- Mobile-native apps; MVP relies on responsive web experiences.

## Design Philosophy
- **Async-first:** Handles concurrent assessments without blocking.
- **Explainable AI:** GPT output is backed by RAG retrieval sources surfaced to end users.
- **Scalable Foundation:** Modular monolith enables future services without premature complexity.

## Rationale Recap
- Asynchronous architecture ensures fast, scalable student processing within performance targets.
- Role-driven RAG recommendations build advisor confidence and align with stakeholder feedback.
- Balanced question composition (3/3/4) achieves both accuracy and personalization for the MVP.
- Four-week delivery plan matches resource constraints outlined in brainstorming sessions.

## Change Log
| Date | Version | Description | Author |
| 2025-10-13 | 0.1 | Initial PRD draft synthesized from brainstorming outputs | John (PM) |
| 2025-10-14 | 0.2 | Added research insights, UX flows, validation plan, and cross-functional requirements | John (PM) |
