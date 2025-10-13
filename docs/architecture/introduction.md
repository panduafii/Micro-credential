# Introduction
This document outlines the backend architecture for the AI-Powered Micro-Credential Assessment project. It covers the FastAPI-based services, asynchronous workers, data stores, and operational practices required to deliver explainable hybrid scoring and recommendations. A future Frontend Architecture document should be produced for the dashboards referenced in the PRD; stack decisions captured here remain authoritative for any UI work.

## Starter Template or Existing Project
No existing starter template or codebase is being reused. A lightweight FastAPI monorepo scaffold will be created (via Cookiecutter or custom script) to align with the async queue, Postgres, Redis, and embedding requirements.

## Change Log
| Date       | Version | Description                                               | Author               |
| ---------- | ------- | --------------------------------------------------------- | -------------------- |
| 2025-10-14 | v0.1    | Initial architecture draft aligned with PRD v4 decisions. | Winston (Architect)  |
