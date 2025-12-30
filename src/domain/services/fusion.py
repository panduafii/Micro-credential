"""
Fusion Service for Story 3.2: Fusion Summary and Result Delivery.

Combines rule scores, essay metrics, and RAG results into a narrative summary.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.domain.services.summary_formatter import format_assessment_summary
from src.infrastructure.db.models import (
    Assessment,
    AssessmentStatus,
    AsyncJob,
    JobStatus,
    JobType,
    QuestionType,
    Recommendation,
    RecommendationItem,
    Score,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class ScoreBreakdown:
    """Breakdown of scores by type."""

    theoretical_score: float
    theoretical_max: float
    theoretical_pct: float
    profile_score: float
    profile_max: float
    profile_pct: float
    essay_score: float
    essay_max: float
    essay_pct: float
    overall_score: float
    overall_pct: float


@dataclass
class FusionResult:
    """Result from fusion processing."""

    assessment_id: str
    summary: str
    overall_score: float
    score_breakdown: dict
    recommendations: list[dict]
    rag_traces: dict | None
    degraded: bool
    processing_duration_ms: int
    completed_at: str


class FusionError(Exception):
    """Raised when fusion processing fails."""


class FusionService:
    """Service for combining scores and generating recommendation summaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_score_breakdown(self, assessment_id: str) -> ScoreBreakdown:
        """Calculate score breakdown from all scores."""
        stmt = select(Score).where(Score.assessment_id == assessment_id)
        result = await self.session.execute(stmt)
        scores = result.scalars().all()

        theoretical_score = 0.0
        theoretical_max = 0.0
        profile_score = 0.0
        profile_max = 0.0
        essay_score = 0.0
        essay_max = 0.0

        for score in scores:
            if score.question_type == QuestionType.THEORETICAL:
                theoretical_score += score.score
                theoretical_max += score.max_score
            elif score.question_type == QuestionType.PROFILE:
                profile_score += score.score
                profile_max += score.max_score
            elif score.question_type == QuestionType.ESSAY:
                essay_score += score.score
                essay_max += score.max_score

        # Calculate percentages
        theoretical_pct = (theoretical_score / theoretical_max * 100) if theoretical_max > 0 else 0
        profile_pct = (profile_score / profile_max * 100) if profile_max > 0 else 0
        essay_pct = (essay_score / essay_max * 100) if essay_max > 0 else 0

        # Overall score (weighted average)
        total_score = theoretical_score + profile_score + essay_score
        total_max = theoretical_max + profile_max + essay_max
        overall_pct = (total_score / total_max * 100) if total_max > 0 else 0

        return ScoreBreakdown(
            theoretical_score=theoretical_score,
            theoretical_max=theoretical_max,
            theoretical_pct=round(theoretical_pct, 1),
            profile_score=profile_score,
            profile_max=profile_max,
            profile_pct=round(profile_pct, 1),
            essay_score=essay_score,
            essay_max=essay_max,
            essay_pct=round(essay_pct, 1),
            overall_score=total_score,
            overall_pct=round(overall_pct, 1),
        )

    def _generate_summary(
        self,
        role_title: str,
        breakdown: ScoreBreakdown,
        recommendations: list[RecommendationItem],
        degraded: bool,
    ) -> str:
        """Generate narrative summary from scores and recommendations."""
        return format_assessment_summary(
            role_title=role_title,
            overall_pct=breakdown.overall_pct,
            theoretical_pct=breakdown.theoretical_pct,
            profile_pct=breakdown.profile_pct,
            essay_pct=breakdown.essay_pct,
            has_essay=breakdown.essay_max > 0,
            recommendations=recommendations,
            degraded=degraded,
        )

    async def process_fusion_job(self, assessment_id: str) -> FusionResult:
        """
        Process fusion job - combine all scores and generate summary.

        AC1: Combines rule scores, essay metrics, and RAG results into narrative summary.
        AC3: Includes timestamp and processing duration.
        """
        start_time = time.time()

        # Get assessment with role
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .options(selectinload(Assessment.role))
        )
        result = await self.session.execute(stmt)
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise FusionError(f"Assessment {assessment_id} not found")

        # Get fusion job
        job_stmt = select(AsyncJob).where(
            AsyncJob.assessment_id == assessment_id,
            AsyncJob.job_type == JobType.FUSION.value,
        )
        job_result = await self.session.execute(job_stmt)
        job = job_result.scalar_one_or_none()

        if job:
            job.status = JobStatus.IN_PROGRESS.value
            job.started_at = datetime.now(UTC)
            job.attempts += 1
            await self.session.flush()

        # Get score breakdown
        breakdown = await self._get_score_breakdown(assessment_id)

        # Get recommendation and items
        rec_stmt = (
            select(Recommendation)
            .where(Recommendation.assessment_id == assessment_id)
            .options(selectinload(Recommendation.items))
        )
        rec_result = await self.session.execute(rec_stmt)
        recommendation = rec_result.scalar_one_or_none()

        items = recommendation.items if recommendation else []
        degraded = recommendation.degraded if recommendation else False
        rag_traces = recommendation.rag_traces if recommendation else None

        # Generate summary
        role_title = assessment.role.name if assessment.role else assessment.role_slug
        summary = self._generate_summary(role_title, breakdown, items, degraded)

        # Calculate processing duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Update or create recommendation
        if recommendation:
            recommendation.summary = summary
            recommendation.overall_score = breakdown.overall_score
            recommendation.score_breakdown = {
                "theoretical": {
                    "score": breakdown.theoretical_score,
                    "max": breakdown.theoretical_max,
                    "percentage": breakdown.theoretical_pct,
                },
                "profile": {
                    "score": breakdown.profile_score,
                    "max": breakdown.profile_max,
                    "percentage": breakdown.profile_pct,
                },
                "essay": {
                    "score": breakdown.essay_score,
                    "max": breakdown.essay_max,
                    "percentage": breakdown.essay_pct,
                },
                "overall": {
                    "score": breakdown.overall_score,
                    "percentage": breakdown.overall_pct,
                },
            }
            recommendation.processing_duration_ms = duration_ms
        else:
            recommendation = Recommendation(
                assessment_id=assessment_id,
                summary=summary,
                overall_score=breakdown.overall_score,
                degraded=False,
                score_breakdown={
                    "theoretical": {
                        "score": breakdown.theoretical_score,
                        "max": breakdown.theoretical_max,
                        "percentage": breakdown.theoretical_pct,
                    },
                    "profile": {
                        "score": breakdown.profile_score,
                        "max": breakdown.profile_max,
                        "percentage": breakdown.profile_pct,
                    },
                    "essay": {
                        "score": breakdown.essay_score,
                        "max": breakdown.essay_max,
                        "percentage": breakdown.essay_pct,
                    },
                    "overall": {
                        "score": breakdown.overall_score,
                        "percentage": breakdown.overall_pct,
                    },
                },
                processing_duration_ms=duration_ms,
            )
            self.session.add(recommendation)

        # Update assessment status to completed
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completed_at = datetime.now(UTC)

        # Update job status
        if job:
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now(UTC)

        await self.session.commit()

        await logger.ainfo(
            "fusion_completed",
            assessment_id=assessment_id,
            overall_score=breakdown.overall_score,
            duration_ms=duration_ms,
        )

        return FusionResult(
            assessment_id=assessment_id,
            summary=summary,
            overall_score=breakdown.overall_score,
            score_breakdown=recommendation.score_breakdown,
            recommendations=[
                {
                    "rank": item.rank,
                    "course_id": item.course_id,
                    "course_title": item.course_title,
                    "course_url": item.course_url,
                    "relevance_score": item.relevance_score,
                    "match_reason": item.match_reason,
                }
                for item in items
            ],
            rag_traces=rag_traces,
            degraded=degraded,
            processing_duration_ms=duration_ms,
            completed_at=datetime.now(UTC).isoformat(),
        )

    async def get_assessment_result(self, assessment_id: str, user_id: str) -> dict:
        """
        Get assessment result for API response.

        AC2: Returns summary, ranked items, RAG traces, and degraded status.
        """
        # Get assessment
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .options(selectinload(Assessment.role))
        )
        result = await self.session.execute(stmt)
        assessment = result.scalar_one_or_none()

        if not assessment:
            from src.domain.services.status import AssessmentNotFoundError

            raise AssessmentNotFoundError(f"Assessment {assessment_id} not found")

        if assessment.owner_id != user_id:
            from src.domain.services.status import AssessmentNotOwnedError

            raise AssessmentNotOwnedError("You do not own this assessment")

        # Get recommendation with items
        rec_stmt = (
            select(Recommendation)
            .where(Recommendation.assessment_id == assessment_id)
            .options(selectinload(Recommendation.items))
        )
        rec_result = await self.session.execute(rec_stmt)
        recommendation = rec_result.scalar_one_or_none()

        if not recommendation:
            return {
                "assessment_id": assessment_id,
                "status": assessment.status.value,
                "message": "Results not yet available. Processing may still be in progress.",
                "completed": False,
            }

        return {
            "assessment_id": assessment_id,
            "status": assessment.status.value,
            "completed": assessment.status == AssessmentStatus.COMPLETED,
            "summary": recommendation.summary,
            "overall_score": recommendation.overall_score,
            "score_breakdown": recommendation.score_breakdown,
            "recommendations": [
                {
                    "rank": item.rank,
                    "course_id": item.course_id,
                    "course_title": item.course_title,
                    "course_url": item.course_url,
                    "relevance_score": item.relevance_score,
                    "match_reason": item.match_reason,
                    "metadata": item.course_metadata,
                }
                for item in recommendation.items
            ],
            "rag_traces": recommendation.rag_traces,
            "degraded": recommendation.degraded,
            "processing_duration_ms": recommendation.processing_duration_ms,
            "completed_at": recommendation.created_at.isoformat(),
        }
