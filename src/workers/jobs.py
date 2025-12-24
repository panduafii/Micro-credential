from __future__ import annotations

import asyncio
from typing import Any

import structlog
from src.infrastructure.repositories import UnitOfWork

logger = structlog.get_logger()


def score_essay_job(
    assessment_id: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entry point for running essay scoring asynchronously."""
    return asyncio.run(_score_essay_async(assessment_id, payload or {}))


def generate_recommendations_job(
    user_id: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entry point for generating recommendations."""
    return asyncio.run(_generate_recommendations_async(user_id, context or {}))


async def _score_essay_async(assessment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with UnitOfWork() as uow:
        await uow.assessments.mark_scoring_started(assessment_id)
        # Placeholder scoring logic.
        await uow.assessments.store_score(assessment_id, score=payload.get("score", 0.0))
    result = {
        "assessment_id": assessment_id,
        "status": "queued",
    }
    logger.info("essay_scoring_enqueued", **result)
    return result


async def _generate_recommendations_async(user_id: str, context: dict[str, Any]) -> dict[str, Any]:
    recommendations = context.get("recommendations", [])
    async with UnitOfWork() as uow:
        await uow.recommendations.save_recommendations(
            user_id,
            recommendations=recommendations,
        )
    result = {
        "user_id": user_id,
        "status": "queued",
    }
    logger.info("recommendations_enqueued", **result)
    return result
