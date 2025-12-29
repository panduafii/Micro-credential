"""
Feedback Service for Story 3.3: Feedback Collection.

Captures advisor/student feedback on recommendations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from src.infrastructure.db.models import (
    Assessment,
    Feedback,
    Recommendation,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class RecommendationNotFoundError(Exception):
    """Raised when recommendation not found."""


class FeedbackService:
    """Service for feedback collection."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_feedback(
        self,
        assessment_id: str,
        user_id: str,
        user_role: str,
        rating_relevance: int | None = None,
        rating_acceptance: int | None = None,
        comment: str | None = None,
    ) -> dict:
        """
        Create feedback for an assessment's recommendations.

        AC1: Captures ratings and comments tied to track.
        AC4: Requires proper role and logs events.
        """
        # Get assessment to verify and get track
        stmt = select(Assessment).where(Assessment.id == assessment_id)
        result = await self.session.execute(stmt)
        assessment = result.scalar_one_or_none()

        if not assessment:
            from src.domain.services.status import AssessmentNotFoundError

            raise AssessmentNotFoundError(f"Assessment {assessment_id} not found")

        # Get recommendation
        rec_stmt = select(Recommendation).where(Recommendation.assessment_id == assessment_id)
        rec_result = await self.session.execute(rec_stmt)
        recommendation = rec_result.scalar_one_or_none()

        if not recommendation:
            raise RecommendationNotFoundError(
                f"No recommendation found for assessment {assessment_id}"
            )

        # Create feedback
        feedback = Feedback(
            recommendation_id=recommendation.id,
            user_id=user_id,
            user_role=user_role,
            rating_relevance=rating_relevance,
            rating_acceptance=rating_acceptance,
            comment=comment,
            track_slug=assessment.role_slug,  # AC3: Tagged by track
        )
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)

        # AC4: Log event
        await logger.ainfo(
            "feedback_submitted",
            feedback_id=feedback.id,
            recommendation_id=recommendation.id,
            user_id=user_id,
            user_role=user_role,
            track_slug=assessment.role_slug,
            rating_relevance=rating_relevance,
            rating_acceptance=rating_acceptance,
        )

        return {
            "id": feedback.id,
            "recommendation_id": feedback.recommendation_id,
            "user_id": feedback.user_id,
            "rating_relevance": feedback.rating_relevance,
            "rating_acceptance": feedback.rating_acceptance,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        }

    async def get_feedback_stats(self, track_slug: str | None = None) -> dict:
        """
        Get aggregated feedback statistics.

        AC2: Aggregated feedback metrics.
        AC3: Can filter by track.
        """
        from sqlalchemy import func

        # Build base query
        query = select(
            func.count(Feedback.id).label("total_count"),
            func.avg(Feedback.rating_relevance).label("avg_relevance"),
            func.avg(Feedback.rating_acceptance).label("avg_acceptance"),
        )

        if track_slug:
            query = query.where(Feedback.track_slug == track_slug)

        result = await self.session.execute(query)
        row = result.first()

        return {
            "track_slug": track_slug,
            "total_feedback_count": row.total_count if row else 0,
            "average_relevance_rating": round(row.avg_relevance or 0, 2),
            "average_acceptance_rating": round(row.avg_acceptance or 0, 2),
        }
