# Epic 1: Role-Gated Assessment Foundation

## Overview
**Goal:** Establish the FastAPI monorepo, secure auth, role catalog, and question management so students must pick a target role before receiving a 10-question bundle.

## Status: ✅ Completed (December 25, 2025)

## Stories Summary

| Story | Title | Status | Tests |
|-------|-------|--------|-------|
| 1.1 | [Monorepo Baseline and Auth Skeleton](./1.1.monorepo-baseline-and-auth-skeleton.md) | ✅ Done | 2 |
| 1.2 | [Track Catalog Management](./1.2.track-catalog-management.md) | ✅ Done | 9 |
| 1.3 | [Question Bank CRUD and Versioning](./1.3.question-bank-crud-versioning.md) | ✅ Done | 11 |
| 1.4 | [Role-Gated Assessment Start](./1.4.role-gated-assessment-start.md) | ✅ Done | 5 |

**Total Tests: 27 passing**

## API Endpoints Delivered

### Tracks (`/tracks`)
- `GET /tracks` - List active tracks with question counts
- `GET /tracks/{slug}` - Get track details
- `POST /tracks` - Create track (admin)
- `PATCH /tracks/{slug}` - Update track (admin)
- `DELETE /tracks/{slug}` - Soft-delete track (admin)

### Questions (`/questions`)
- `GET /questions` - List active questions (filter by role_slug)
- `GET /questions/{id}` - Get question details
- `POST /questions` - Create question (admin)
- `PATCH /questions/{id}` - Update with versioning (admin)
- `DELETE /questions/{id}` - Soft-delete question (admin)

### Assessments (`/assessments`)
- `POST /assessments/start` - Start or resume assessment (student)

## Database Migrations
1. `202412250001_initial_schema.py` - Base tables
2. `202412250002_add_track_catalog_fields.py` - Track metadata fields
3. `202412250003_add_question_versioning.py` - Question versioning columns
4. `202412250004_add_assessment_expiry.py` - Assessment expiry field

## Key Features Implemented

### Authentication & Authorization
- JWT-based authentication with role claims
- Role-based access control: `student`, `advisor`, `admin`
- Dependency injection via `require_roles()`

### Track Management
- Full CRUD with soft delete
- Skill focus tags and question mix overrides
- Seed data: Backend Engineer, Data Analyst

### Question Bank
- Support for theoretical, essay, profile types
- Versioning on updates (immutable history)
- Metadata for rubrics and rules
- Soft delete preserves historical data

### Assessment Flow
- Role selection required to start
- Question mix: 3 theoretical + 3 essay + 4 profile
- 24-hour expiry with resume capability
- Analytics event logging

## Architecture Highlights
- FastAPI async with Pydantic v2
- SQLAlchemy async ORM
- PostgreSQL + Redis backing services
- Structlog JSON logging
- Docker Compose for local development

## Next: Epic 2
[Async Scoring and Persistence Backbone](../../prd/epic-2-async-scoring-and-persistence-backbone.md)
