"""
GPT Essay Scoring Service.

Story 2.2: Evaluates essays asynchronously via GPT with rubric-based scoring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db.models import (
    Assessment,
    AssessmentQuestionSnapshot,
    AssessmentResponse,
    AsyncJob,
    JobStatus,
    QuestionType,
    Score,
)
from src.libs.gpt_client import (
    GPTClientError,
    GPTClientProtocol,
    OpenAIClient,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Rubric dimensions for essay scoring
ESSAY_RUBRIC_DIMENSIONS = [
    "relevance",  # How relevant is the answer to the question
    "depth",  # Depth of analysis and understanding
    "clarity",  # Clarity of expression
    "completeness",  # Completeness of the answer
    "technical",  # Technical accuracy (if applicable)
]

# System prompt for deterministic essay scoring
ESSAY_SCORING_SYSTEM_PROMPT = """You are an expert essay evaluator for a \
micro-credential assessment platform.
Your task is to score essays based on the following rubric dimensions:
- relevance (0-100): How well does the answer address the question asked
- depth (0-100): Level of analysis, critical thinking, and understanding shown
- clarity (0-100): How clearly the ideas are expressed and organized
- completeness (0-100): Whether all aspects of the question are addressed
- technical (0-100): Technical accuracy and use of appropriate terminology

For each essay, provide:
1. A score (0-100) for each dimension
2. A brief explanation for the overall score
3. A total weighted score (average of all dimensions)

Respond in JSON format only:
{
  "scores": {
    "relevance": <number>,
    "depth": <number>,
    "clarity": <number>,
    "completeness": <number>,
    "technical": <number>
  },
  "total_score": <number>,
  "explanation": "<brief explanation>"
}
"""


@dataclass(slots=True)
class EssayScoreResult:
    """Result of scoring a single essay."""

    question_snapshot_id: str
    score: float
    max_score: float
    rubric_scores: dict[str, float]
    explanation: str
    model: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int


@dataclass(slots=True)
class EssayScoringResult:
    """Result of scoring all essays in an assessment."""

    assessment_id: str
    essay_scores: list[EssayScoreResult]
    total_score: float
    max_score: float
    status: str  # "success" or "partial" or "failed"
    failed_count: int
    error_message: str | None = None


class GPTScoringError(Exception):
    """Raised when GPT scoring fails."""

    def __init__(self, message: str, question_id: str | None = None):
        super().__init__(message)
        self.question_id = question_id


class GPTEssayScoringService:
    """
    Service for scoring essays using GPT.

    AC1: Batches essays per assessment and calls GPT with deterministic prompt.
    AC2: Parses GPT responses into rubric metrics.
    AC3: Retries up to three attempts with exponential backoff.
    """

    MAX_SCORE = 100.0

    def __init__(
        self,
        session: AsyncSession,
        gpt_client: GPTClientProtocol | None = None,
    ) -> None:
        self.session = session
        self.gpt_client = gpt_client or OpenAIClient()

    async def score_assessment_essays(
        self,
        assessment_id: str,
        job_id: str,
    ) -> EssayScoringResult:
        """
        Score all essay responses for an assessment.

        AC1: Worker pulls essays and calls GPT with deterministic prompt.
        AC2: GPT responses parsed into rubric metrics.
        AC3: Failures logged and job marked failed.
        """
        # Update job status to in_progress
        await self._update_job_status(job_id, JobStatus.IN_PROGRESS)

        try:
            # Get assessment with essay responses
            essays = await self._get_essay_responses(assessment_id)

            if not essays:
                await logger.ainfo(
                    "no_essays_to_score",
                    assessment_id=assessment_id,
                )
                await self._update_job_status(job_id, JobStatus.COMPLETED)
                return EssayScoringResult(
                    assessment_id=assessment_id,
                    essay_scores=[],
                    total_score=0.0,
                    max_score=0.0,
                    status="success",
                    failed_count=0,
                )

            # Score each essay
            results: list[EssayScoreResult] = []
            failed_count = 0

            for snapshot, response in essays:
                try:
                    score_result = await self._score_single_essay(
                        snapshot=snapshot,
                        response=response,
                    )
                    results.append(score_result)

                    # Save score to database
                    await self._save_essay_score(assessment_id, score_result)

                except (GPTScoringError, GPTClientError) as e:
                    failed_count += 1
                    await logger.aerror(
                        "essay_scoring_failed",
                        assessment_id=assessment_id,
                        question_id=snapshot.id,
                        error=str(e),
                    )

            # Calculate totals
            total_score = sum(r.score for r in results) if results else 0.0
            max_score = self.MAX_SCORE * len(essays)

            # Determine status
            if failed_count == 0:
                status = "success"
            elif failed_count < len(essays):
                status = "partial"
            else:
                status = "failed"

            # Update job status
            job_status = JobStatus.COMPLETED if status != "failed" else JobStatus.FAILED
            await self._update_job_status(
                job_id,
                job_status,
                error_payload={"failed_count": failed_count} if failed_count > 0 else None,
            )

            # If any failures, mark assessment as degraded
            if failed_count > 0:
                await self._mark_assessment_degraded(assessment_id)

            # Log completion
            await logger.ainfo(
                "essay_scoring_completed",
                assessment_id=assessment_id,
                scored_count=len(results),
                failed_count=failed_count,
                total_score=total_score,
                max_score=max_score,
            )

            return EssayScoringResult(
                assessment_id=assessment_id,
                essay_scores=results,
                total_score=total_score,
                max_score=max_score,
                status=status,
                failed_count=failed_count,
            )

        except Exception as e:
            # Unexpected error - mark job failed
            await logger.aerror(
                "essay_scoring_unexpected_error",
                assessment_id=assessment_id,
                error=str(e),
            )
            await self._update_job_status(
                job_id,
                JobStatus.FAILED,
                error_payload={"error": str(e)},
            )
            await self._mark_assessment_degraded(assessment_id)
            raise

    async def _get_essay_responses(
        self,
        assessment_id: str,
    ) -> list[tuple[AssessmentQuestionSnapshot, AssessmentResponse]]:
        """Get all essay questions and responses for an assessment."""
        stmt = (
            select(AssessmentQuestionSnapshot, AssessmentResponse)
            .join(
                AssessmentResponse,
                AssessmentResponse.question_snapshot_id == AssessmentQuestionSnapshot.id,
            )
            .where(
                AssessmentQuestionSnapshot.assessment_id == assessment_id,
                AssessmentQuestionSnapshot.question_type == QuestionType.ESSAY,
            )
            .order_by(AssessmentQuestionSnapshot.sequence)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def _score_single_essay(
        self,
        snapshot: AssessmentQuestionSnapshot,
        response: AssessmentResponse,
    ) -> EssayScoreResult:
        """Score a single essay using GPT."""
        # Build user prompt
        essay_text = response.response_data.get("answer", "")
        if not essay_text:
            # No answer provided - give zero score
            return EssayScoreResult(
                question_snapshot_id=snapshot.id,
                score=0.0,
                max_score=self.MAX_SCORE,
                rubric_scores={dim: 0.0 for dim in ESSAY_RUBRIC_DIMENSIONS},
                explanation="Tidak ada jawaban yang diberikan",
                model="rule",
                latency_ms=0,
                prompt_tokens=0,
                completion_tokens=0,
            )

        user_prompt = f"""Question: {snapshot.prompt}

Student's Essay Answer:
{essay_text}

Please score this essay according to the rubric dimensions."""

        messages = [
            {"role": "system", "content": ESSAY_SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Call GPT (retries handled by client)
        gpt_response = await self.gpt_client.chat_completion(
            messages=messages,
            temperature=0.0,  # Deterministic
            max_tokens=500,
        )

        # Parse response
        try:
            parsed = self._parse_gpt_response(gpt_response.content)
        except Exception as e:
            raise GPTScoringError(
                f"Failed to parse GPT response: {e}",
                question_id=snapshot.id,
            ) from e

        return EssayScoreResult(
            question_snapshot_id=snapshot.id,
            score=parsed["total_score"],
            max_score=self.MAX_SCORE,
            rubric_scores=parsed["scores"],
            explanation=parsed["explanation"],
            model=gpt_response.model,
            latency_ms=gpt_response.latency_ms,
            prompt_tokens=gpt_response.prompt_tokens,
            completion_tokens=gpt_response.completion_tokens,
        )

    def _parse_gpt_response(self, content: str) -> dict[str, Any]:
        """Parse GPT response JSON."""
        # Try to extract JSON from response
        content = content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GPT response: {e}") from e

        # Validate structure
        if "scores" not in data or "total_score" not in data:
            raise ValueError("Missing required fields in GPT response")

        scores = data["scores"]
        for dim in ESSAY_RUBRIC_DIMENSIONS:
            if dim not in scores:
                scores[dim] = 0.0
            else:
                # Clamp to 0-100
                scores[dim] = max(0.0, min(100.0, float(scores[dim])))

        return {
            "scores": scores,
            "total_score": max(0.0, min(100.0, float(data["total_score"]))),
            "explanation": data.get("explanation", ""),
        }

    async def _save_essay_score(
        self,
        assessment_id: str,
        result: EssayScoreResult,
    ) -> None:
        """Save essay score to database."""
        score = Score(
            assessment_id=assessment_id,
            question_snapshot_id=result.question_snapshot_id,
            question_type=QuestionType.ESSAY,
            score=result.score,
            max_score=result.max_score,
            explanation=result.explanation,
            scoring_method="gpt",
            rules_applied={"rubric_scores": result.rubric_scores},
            model_info={
                "model": result.model,
                "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            },
        )
        self.session.add(score)
        await self.session.flush()

    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_payload: dict[str, Any] | None = None,
    ) -> None:
        """Update async job status."""
        values: dict[str, Any] = {"status": status}

        if status == JobStatus.IN_PROGRESS:
            values["started_at"] = datetime.now(UTC)
            values["attempts"] = AsyncJob.attempts + 1
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            values["completed_at"] = datetime.now(UTC)

        if error_payload:
            values["error_payload"] = error_payload

        await self.session.execute(update(AsyncJob).where(AsyncJob.id == job_id).values(**values))
        await self.session.commit()

    async def _mark_assessment_degraded(self, assessment_id: str) -> None:
        """Mark assessment as degraded due to scoring failures."""
        await self.session.execute(
            update(Assessment).where(Assessment.id == assessment_id).values(degraded=True)
        )
        await self.session.commit()
