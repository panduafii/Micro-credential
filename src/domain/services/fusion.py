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
    AssessmentQuestionSnapshot,
    AssessmentResponse,
    AssessmentStatus,
    AsyncJob,
    JobStatus,
    JobType,
    QuestionType,
    Recommendation,
    RecommendationItem,
    Score,
    UserModel,
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
        profile_signals: dict | None = None,
        missed_topics: list[str] | None = None,
        user_name: str | None = None,
        rag_traces: dict | None = None,
    ) -> str:
        """Generate narrative summary from scores and recommendations."""
        readiness = None
        if isinstance(rag_traces, dict):
            readiness_candidate = rag_traces.get("readiness")
            if isinstance(readiness_candidate, dict):
                readiness = readiness_candidate

        return format_assessment_summary(
            role_title=role_title,
            overall_pct=breakdown.overall_pct,
            theoretical_pct=breakdown.theoretical_pct,
            profile_pct=breakdown.profile_pct,
            essay_pct=breakdown.essay_pct,
            has_essay=breakdown.essay_max > 0,
            recommendations=recommendations,
            degraded=degraded,
            profile_signals=profile_signals,
            missed_topics=missed_topics,
            user_name=user_name,
            readiness=readiness,
        )

    async def _get_user_name(self, owner_id: str) -> str | None:
        """Get user's full name by owner_id."""
        stmt = select(UserModel.full_name).where(UserModel.id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _extract_profile_signals(self, assessment_id: str) -> dict:
        """Extract profile signals from assessment responses.

        Returns dict with keys:
            - tech-preferences: What user wants to learn (Q8) - can be custom text
            - content-duration: Preferred duration (Q9)
            - payment-preference: Paid/free preference (Q10)
        """
        stmt = (
            select(AssessmentQuestionSnapshot, AssessmentResponse)
            .join(
                AssessmentResponse,
                AssessmentResponse.question_snapshot_id == AssessmentQuestionSnapshot.id,
            )
            .where(
                AssessmentQuestionSnapshot.assessment_id == assessment_id,
                AssessmentQuestionSnapshot.question_type == QuestionType.PROFILE,
            )
        )
        rows = (await self.session.execute(stmt)).all()
        signals: dict[str, str | list[str]] = {}
        for snapshot, response in rows:
            response_data = response.response_data or {}
            # Try multiple keys to get the value (different FE implementations)
            value = (
                response_data.get("value")
                or response_data.get("selected_option")
                or response_data.get("answer")
                or response_data.get("answer_text")
                or response_data.get("custom_text")
                or response_data.get("text")
            )
            if not value:
                continue
            key = (snapshot.metadata_ or {}).get("dimension") or str(snapshot.sequence)
            if isinstance(value, list):
                cleaned = [str(item).strip() for item in value if str(item).strip()]
                if not cleaned:
                    continue
                signals[str(key)] = cleaned
            else:
                text_value = str(value).strip()
                if not text_value:
                    continue
                signals[str(key)] = text_value
        return signals

    async def _extract_missed_topics(self, assessment_id: str) -> list[str]:
        """Extract topics from THEORETICAL/ESSAY questions that scored poorly (< 60%).

        Only extracts topics from non-profile questions to avoid showing
        dimension names like 'experience-level' as missed topics.
        """
        # Profile dimensions to exclude from missed topics
        profile_dimensions = {
            "experience-level",
            "tech-preferences",
            "content-duration",
            "payment-preference",
        }

        stmt = (
            select(Score, AssessmentQuestionSnapshot)
            .join(
                AssessmentQuestionSnapshot,
                AssessmentQuestionSnapshot.id == Score.question_snapshot_id,
            )
            .where(Score.assessment_id == assessment_id)
        )
        rows = (await self.session.execute(stmt)).all()
        missed: list[str] = []
        for score, snapshot in rows:
            if score.max_score <= 0:
                continue
            ratio = score.score / score.max_score
            if ratio >= 0.6:
                continue

            # Skip profile questions - they don't have technical topics
            if snapshot.question_type == QuestionType.PROFILE:
                continue

            # Get topic/dimension from metadata (only if not a profile dimension)
            dimension = (snapshot.metadata_ or {}).get("dimension")
            if dimension and dimension not in profile_dimensions:
                missed.append(str(dimension))

            # Extract key topics from prompt for more context
            prompt = snapshot.prompt or ""
            prompt_lower = prompt.lower()
            # Extract key topics from prompt
            topic_keywords = [
                "api",
                "rest",
                "database",
                "sql",
                "cache",
                "security",
                "testing",
                "docker",
                "kubernetes",
                "microservice",
                "async",
                "authentication",
            ]
            for kw in topic_keywords:
                if kw in prompt_lower and kw not in missed:
                    missed.append(kw)
        return missed

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
        job_stmt = (
            select(AsyncJob)
            .where(
                AsyncJob.assessment_id == assessment_id,
                AsyncJob.job_type == JobType.FUSION.value,
                AsyncJob.status == JobStatus.QUEUED.value,
            )
            .order_by(AsyncJob.queued_at.desc())
        )
        job_result = await self.session.execute(job_stmt)
        job = job_result.scalars().first()  # Get most recent queued job

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
        degraded = bool(
            (recommendation.degraded if recommendation else False) or assessment.degraded
        )
        rag_traces = recommendation.rag_traces if recommendation else None

        # Extract profile signals for personalization
        profile_signals = await self._extract_profile_signals(assessment_id)

        # Extract missed topics (areas where user needs improvement)
        missed_topics = await self._extract_missed_topics(assessment_id)

        # Get user's name for personalized greeting
        user_name = await self._get_user_name(assessment.owner_id)

        # Generate summary with personalization and missed topics
        role_title = assessment.role.name if assessment.role else assessment.role_slug
        summary = self._generate_summary(
            role_title,
            breakdown,
            items,
            degraded,
            profile_signals,
            missed_topics,
            user_name,
            rag_traces,
        )

        # Calculate processing duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Update or create recommendation
        if recommendation:
            recommendation.summary = summary
            recommendation.overall_score = breakdown.overall_score
            recommendation.degraded = degraded
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
                degraded=degraded,
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
        completed_at = datetime.now(UTC)
        assessment.status = AssessmentStatus.COMPLETED
        assessment.degraded = degraded
        assessment.completed_at = completed_at

        # Update job status
        if job:
            job.status = JobStatus.COMPLETED.value
            job.completed_at = completed_at

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
            completed_at=completed_at.isoformat(),
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
        status_value = (
            assessment.status.value
            if hasattr(assessment.status, "value")
            else str(assessment.status)
        )

        if not recommendation:
            return {
                "assessment_id": assessment_id,
                "status": status_value,
                "message": "Results not yet available. Processing may still be in progress.",
                "completed": False,
            }

        completed = status_value == AssessmentStatus.COMPLETED.value
        degraded = bool(assessment.degraded or recommendation.degraded)
        completed_at = (
            assessment.completed_at.isoformat()
            if assessment.completed_at
            else recommendation.created_at.isoformat()
        )

        return {
            "assessment_id": assessment_id,
            "status": status_value,
            "completed": completed,
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
            "degraded": degraded,
            "processing_duration_ms": recommendation.processing_duration_ms,
            "completed_at": completed_at,
        }
