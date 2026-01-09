"""
Submission service for assessment finalization and rule-based scoring.

Story 2.1: Submission Finalization and Rule Scoring
- POST /assessments/{id}/submit locks responses
- Computes theoretical/profile scores synchronously
- Creates async job records for GPT/RAG/fusion
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.infrastructure.db.models import (
    Assessment,
    AssessmentQuestionSnapshot,
    AssessmentResponse,
    AssessmentStatus,
    AsyncJob,
    JobStatus,
    JobType,
    QuestionType,
    Score,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class AssessmentNotFoundError(Exception):
    """Raised when assessment does not exist."""


class AssessmentNotOwnedError(Exception):
    """Raised when user does not own the assessment."""


class AssessmentAlreadySubmittedError(Exception):
    """Raised when assessment has already been submitted."""


class AssessmentExpiredError(Exception):
    """Raised when assessment has expired."""


class DuplicateSubmissionError(Exception):
    """Raised when a duplicate submission is detected via idempotency key."""


class InvalidResponseError(Exception):
    """Raised when the client submits responses that cannot be persisted."""


class IncompleteResponsesError(Exception):
    """Raised when not all questions have responses."""

    def __init__(self, message: str, missing_count: int):
        super().__init__(message)
        self.missing_count = missing_count


@dataclass(slots=True)
class ScoreBreakdown:
    question_snapshot_id: str
    question_type: str
    score: float
    max_score: float
    explanation: str | None
    scoring_method: str


@dataclass(slots=True)
class SubmissionResult:
    assessment_id: str
    status: str
    submitted_at: str
    degraded: bool
    scores: dict[str, Any]  # Per-type breakdown
    jobs_queued: list[str]  # Job types queued


class SubmissionService:
    """Handles assessment submission and rule-based scoring."""

    # Rule-based scoring constants
    THEORETICAL_MAX_SCORE = 100.0
    PROFILE_MAX_SCORE = 100.0

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def submit_assessment(
        self,
        *,
        assessment_id: str,
        user_id: str,
        idempotency_key: str | None = None,
        responses_payload: list[dict[str, Any]] | None = None,
    ) -> SubmissionResult:
        """
        Submit an assessment for scoring.

        AC1: Enforces completion, locks responses, computes theoretical/profile scores.
        AC2: Scores written to Postgres scores table with per-question breakdown.
        AC3: Job records created (gpt, rag, fusion) with status queued.
        AC4: Degraded flag set if required data is missing.
        AC (Story 2.3): Idempotency key prevents duplicate submissions.
        """
        # Story 2.3: Check idempotency key
        if idempotency_key:
            existing = await self._check_idempotency_key(idempotency_key)
            if existing:
                raise DuplicateSubmissionError(
                    f"Duplicate submission detected for idempotency key: {idempotency_key}"
                )
        # Load assessment with all relationships
        assessment = await self._get_assessment_with_responses(assessment_id)

        # Validate ownership and state
        self._validate_submission(assessment, user_id)

        responses = assessment.responses
        if responses_payload:
            responses = await self._persist_responses(assessment, responses_payload)

        # Check for incomplete responses
        snapshots = assessment.question_snapshots
        missing_count = self._check_completion(snapshots, responses)

        # Set degraded flag if missing responses
        degraded = missing_count > 0

        # Compute rule-based scores for theoretical and profile questions
        scores = await self._compute_rule_scores(assessment, responses, degraded)

        # Create async jobs for GPT scoring (essays), RAG, and fusion
        jobs_queued = await self._create_async_jobs(assessment, snapshots)

        # Update assessment status
        now = datetime.now(UTC)
        update_values: dict = {
            "status": AssessmentStatus.SUBMITTED,
            "degraded": degraded,
            "completed_at": now,
        }
        # Story 2.3: Store idempotency key if provided
        if idempotency_key:
            update_values["idempotency_key"] = idempotency_key

        await self.session.execute(
            update(Assessment).where(Assessment.id == assessment_id).values(**update_values)
        )

        await self.session.commit()

        # Build score summary
        score_summary = self._build_score_summary(scores)

        # Log analytics event
        await logger.ainfo(
            "assessment_submitted",
            assessment_id=assessment_id,
            student_id=user_id,
            theoretical_score=score_summary.get("theoretical", {}).get("total"),
            profile_score=score_summary.get("profile", {}).get("total"),
            essay_count=score_summary.get("essay", {}).get("count", 0),
            degraded=degraded,
            jobs_queued=jobs_queued,
        )

        return SubmissionResult(
            assessment_id=assessment_id,
            status=AssessmentStatus.SUBMITTED.value,
            submitted_at=now.isoformat(),
            degraded=degraded,
            scores=score_summary,
            jobs_queued=jobs_queued,
        )

    async def _persist_responses(
        self,
        assessment: Assessment,
        responses_payload: list[dict[str, Any]],
    ) -> list[AssessmentResponse]:
        if not responses_payload:
            return list(assessment.responses)

        snapshot_map = {snapshot.id: snapshot for snapshot in assessment.question_snapshots}
        existing_map = {
            response.question_snapshot_id: response for response in assessment.responses
        }
        updated_responses = list(assessment.responses)

        for payload in responses_payload:
            snapshot_id = payload.get("question_id")
            snapshot = snapshot_map.get(snapshot_id or "")
            if snapshot is None:
                raise InvalidResponseError(f"Invalid question_id: {snapshot_id}")

            response_data = self._normalize_response_payload(snapshot, payload)

            if snapshot_id in existing_map:
                existing_map[snapshot_id].response_data = response_data
            else:
                response = AssessmentResponse(
                    assessment_id=assessment.id,
                    question_snapshot_id=snapshot_id,
                    response_data=response_data,
                )
                self.session.add(response)
                updated_responses.append(response)

        await self.session.flush()
        return updated_responses

    def _normalize_response_payload(
        self,
        snapshot: AssessmentQuestionSnapshot,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        question_type = snapshot.question_type
        metadata = payload.get("metadata")
        response: dict[str, Any] = {}

        if question_type == QuestionType.ESSAY:
            answer = self._clean_text(
                payload.get("answer_text") or payload.get("answer") or payload.get("value")
            )
            if answer:
                response["answer"] = answer
        elif question_type == QuestionType.THEORETICAL:
            selected = self._clean_text(
                payload.get("selected_option")
                or payload.get("selected_option_id")
                or payload.get("answer_text")
                or payload.get("value")
            )
            if selected:
                response["selected_option"] = selected
            if payload.get("selected_option_id"):
                response["selected_option_id"] = self._clean_text(payload["selected_option_id"])
        else:  # Profile question
            value = self._clean_text(
                payload.get("value") or payload.get("answer_text") or payload.get("answer")
            )
            if value:
                response["value"] = value

        if metadata is not None:
            response["metadata"] = metadata
        return response

    @staticmethod
    def _clean_text(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    async def _check_idempotency_key(self, idempotency_key: str) -> Assessment | None:
        """Check if an assessment with this idempotency key already exists."""
        stmt = select(Assessment).where(Assessment.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_assessment_with_responses(self, assessment_id: str) -> Assessment:
        """Load assessment with question snapshots and responses."""
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .options(
                selectinload(Assessment.question_snapshots),
                selectinload(Assessment.responses),
            )
        )
        assessment = await self.session.scalar(stmt)
        if assessment is None:
            raise AssessmentNotFoundError(f"Assessment '{assessment_id}' tidak ditemukan")
        return assessment

    def _validate_submission(self, assessment: Assessment, user_id: str) -> None:
        """Validate that assessment can be submitted."""
        # Check ownership
        if assessment.owner_id != user_id:
            raise AssessmentNotOwnedError("Anda tidak memiliki akses ke assessment ini")

        # Check if already submitted
        if assessment.status in (
            AssessmentStatus.SUBMITTED,
            AssessmentStatus.COMPLETED,
            AssessmentStatus.FAILED,
        ):
            raise AssessmentAlreadySubmittedError(
                f"Assessment sudah di-submit (status: {assessment.status.value})"
            )

        # Check expiration (handle both timezone-aware and naive datetimes)
        if assessment.expires_at:
            now = datetime.now(UTC)
            expires_at = assessment.expires_at
            # Convert naive datetime to aware if needed (SQLite stores naive datetimes)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if now > expires_at:
                raise AssessmentExpiredError("Assessment sudah expired")

    def _check_completion(
        self,
        snapshots: list[AssessmentQuestionSnapshot],
        responses: list[AssessmentResponse],
    ) -> int:
        """Check if all questions have responses. Returns count of missing responses."""
        snapshot_ids = {s.id for s in snapshots}
        response_snapshot_ids = {r.question_snapshot_id for r in responses}
        missing = snapshot_ids - response_snapshot_ids
        return len(missing)

    async def _compute_rule_scores(
        self,
        assessment: Assessment,
        responses: list[AssessmentResponse],
        degraded: bool,
    ) -> list[Score]:
        """Compute rule-based scores for theoretical and profile questions."""
        scores: list[Score] = []

        # Build response lookup
        response_map = {r.question_snapshot_id: r for r in responses}

        for snapshot in assessment.question_snapshots:
            # Skip essay questions - they need GPT scoring
            if snapshot.question_type == QuestionType.ESSAY:
                continue

            response = response_map.get(snapshot.id)

            if snapshot.question_type == QuestionType.THEORETICAL:
                score = self._score_theoretical(snapshot, response)
            elif snapshot.question_type == QuestionType.PROFILE:
                score = self._score_profile(snapshot, response)
            else:
                continue

            score_record = Score(
                assessment_id=assessment.id,
                question_snapshot_id=snapshot.id,
                question_type=snapshot.question_type,
                score=score["score"],
                max_score=score["max_score"],
                explanation=score["explanation"],
                scoring_method="rule",
                rules_applied=score.get("rules_applied"),
            )
            self.session.add(score_record)
            scores.append(score_record)

        return scores

    def _score_theoretical(
        self,
        snapshot: AssessmentQuestionSnapshot,
        response: AssessmentResponse | None,
    ) -> dict[str, Any]:
        """
        Score a theoretical (multiple choice) question.

        Rules:
        - Check if selected_option matches correct_answer in metadata
        - Full points for correct, zero for incorrect/missing
        """
        max_score = self.THEORETICAL_MAX_SCORE * (snapshot.weight or 1.0)
        correct_answer = snapshot.correct_answer or (snapshot.metadata_ or {}).get("correct_answer")

        if response is None:
            return {
                "score": 0.0,
                "max_score": max_score,
                "explanation": "Tidak ada jawaban",
                "rules_applied": {"rule": "no_response"},
            }

        response_data = response.response_data or {}
        selected_option = response_data.get("selected_option")

        if correct_answer is None:
            # No correct answer defined - give full score (degraded)
            return {
                "score": max_score,
                "max_score": max_score,
                "explanation": "Tidak ada jawaban benar yang didefinisikan",
                "rules_applied": {"rule": "no_correct_answer_defined", "degraded": True},
            }

        is_correct = str(selected_option).lower() == str(correct_answer).lower()

        return {
            "score": max_score if is_correct else 0.0,
            "max_score": max_score,
            "explanation": "Jawaban benar" if is_correct else "Jawaban salah",
            "rules_applied": {
                "rule": "exact_match",
                "correct_answer": correct_answer,
                "selected": selected_option,
                "is_correct": is_correct,
            },
        }

    def _score_profile(
        self,
        snapshot: AssessmentQuestionSnapshot,
        response: AssessmentResponse | None,
    ) -> dict[str, Any]:
        """
        Score a profile question.

        Rules:
        - Profile questions capture preferences/self-assessment
        - Score based on expected_values scoring map OR completeness
        - Supports compound questions with multiple fields
        """
        max_score = self.PROFILE_MAX_SCORE * (snapshot.weight or 1.0)
        if response is None:
            return {
                "score": 0.0,
                "max_score": max_score,
                "explanation": "Tidak ada jawaban",
                "rules_applied": {"rule": "no_response"},
            }

        response_data = response.response_data or {}
        expected_values = snapshot.expected_values or {}

        # Check for compound question type (Q7 with months + projects)
        if isinstance(expected_values, dict) and expected_values.get("type") == "compound":
            return self._score_compound_profile(snapshot, response_data, expected_values, max_score)

        # Check for scoring map (standard profile question with A/B/C/D/E options)
        if isinstance(expected_values, dict) and "scoring" in expected_values:
            scoring_map = expected_values["scoring"]
            selected = response_data.get("selected_option") or response_data.get("value", "")

            if selected and selected in scoring_map:
                # Calculate score based on scoring map (e.g., {"A": 20, "B": 40, ...})
                raw_score = scoring_map[selected]
                # Normalize to max_score (scoring map values are 0-100, scale to max_score)
                score = (raw_score / 100.0) * max_score
                return {
                    "score": score,
                    "max_score": max_score,
                    "explanation": f"Skor profil: {raw_score}%",
                    "rules_applied": {
                        "rule": "scoring_map",
                        "selected": selected,
                        "raw_score": raw_score,
                    },
                }

        # Fallback: check if response has meaningful content
        has_value = bool(response_data.get("value") or response_data.get("selected_option"))

        if has_value and expected_values:
            value = (
                response_data.get("value") or response_data.get("selected_option") or ""
            ).lower()
            accepted = (
                expected_values.get("accepted_values")
                if isinstance(expected_values, dict)
                else expected_values
            )
            match = False
            if isinstance(accepted, list):
                match = value in [str(v).lower() for v in accepted]
            elif isinstance(accepted, str):
                match = value == accepted.lower()
            else:
                match = True  # unknown structure, fallback to completeness

            if match:
                return {
                    "score": max_score,
                    "max_score": max_score,
                    "explanation": "Nilai sesuai kriteria",
                    "rules_applied": {
                        "rule": "expected_values_match",
                        "accepted": accepted,
                        "value": value,
                        "match": match,
                    },
                }
            return {
                "score": max_score,
                "max_score": max_score,
                "explanation": "Profil terisi, tetapi tidak sesuai kriteria",
                "rules_applied": {
                    "rule": "expected_values_mismatch",
                    "accepted": accepted,
                    "value": value,
                    "match": match,
                },
            }

        if has_value:
            return {
                "score": max_score,
                "max_score": max_score,
                "explanation": "Profil terisi lengkap",
                "rules_applied": {"rule": "completeness_check", "has_value": True},
            }

        return {
            "score": 0.0,
            "max_score": max_score,
            "explanation": "Profil tidak lengkap",
            "rules_applied": {"rule": "completeness_check", "has_value": False},
        }

    def _score_compound_profile(
        self,
        snapshot: AssessmentQuestionSnapshot,
        response_data: dict,
        expected_values: dict,
        max_score: float,
    ) -> dict[str, Any]:
        """Score a compound profile question with multiple fields.

        Supports two formats:
        1. Simple text: "X bulan dan Y project" (parsed via regex)
        2. Object: {"months": "6-12", "projects": "3-5"} (legacy dropdown format)
        """
        import re

        scoring = expected_values.get("scoring", {})
        weights = expected_values.get("weight", {})
        format_type = expected_values.get("format", "object")

        # Handle simple text format: "X bulan dan Y project"
        if format_type == "text":
            answer_text = response_data.get("answer_text", "")
            pattern = expected_values.get("pattern", r"(\d+) bulan dan (\d+) project")
            match = re.match(pattern, str(answer_text))

            if not match:
                return {
                    "score": 0,
                    "max_score": max_score,
                    "explanation": "Format jawaban tidak valid",
                    "rules_applied": {"rule": "compound_text_parse_failed"},
                }

            months = int(match.group(1))
            projects = int(match.group(2))

            # Score using ranges
            months_score = self._score_by_ranges(
                months, scoring.get("months", {}).get("ranges", [])
            )
            projects_score = self._score_by_ranges(
                projects, scoring.get("projects", {}).get("ranges", [])
            )

            months_weight = weights.get("months", 0.5)
            projects_weight = weights.get("projects", 0.5)

            total_score = (months_score * months_weight) + (projects_score * projects_weight)
            score = (total_score / 100.0) * max_score

            return {
                "score": score,
                "max_score": max_score,
                "explanation": f"Pengalaman: {months} bulan, {projects} project",
                "rules_applied": {
                    "rule": "compound_text_scoring",
                    "parsed": {"months": months, "projects": projects},
                    "scores": {"months": months_score, "projects": projects_score},
                    "weights": {"months": months_weight, "projects": projects_weight},
                    "total_raw": total_score,
                },
            }

        # Legacy object format: {"months": "6-12", "projects": "3-5"}
        total_score = 0.0
        details = {}

        for field, field_scoring in scoring.items():
            field_value = response_data.get(field, "")
            field_weight = weights.get(field, 1.0 / len(scoring))

            if field_value and field_value in field_scoring:
                raw = field_scoring[field_value]
                weighted = raw * field_weight
                total_score += weighted
                details[field] = {"value": field_value, "raw": raw, "weighted": weighted}
            else:
                details[field] = {"value": field_value, "raw": 0, "weighted": 0}

        # Normalize to max_score
        score = (total_score / 100.0) * max_score

        return {
            "score": score,
            "max_score": max_score,
            "explanation": f"Skor compound: {total_score:.0f}%",
            "rules_applied": {
                "rule": "compound_scoring",
                "details": details,
                "total_raw": total_score,
            },
        }

    def _score_by_ranges(self, value: int, ranges: list[dict]) -> float:
        """Score a numeric value based on defined ranges."""
        for r in ranges:
            if r.get("min", 0) <= value <= r.get("max", 999):
                return r.get("score", 0)
        return 0

    async def _create_async_jobs(
        self,
        assessment: Assessment,
        snapshots: list[AssessmentQuestionSnapshot],
    ) -> list[str]:
        """Create async job records for GPT scoring, RAG, and fusion."""
        jobs_queued: list[str] = []

        # Check if there are essay questions that need GPT scoring
        essay_snapshots = [s for s in snapshots if s.question_type == QuestionType.ESSAY]

        if essay_snapshots:
            # Create GPT scoring job
            gpt_job = AsyncJob(
                assessment_id=assessment.id,
                job_type=JobType.GPT,
                status=JobStatus.QUEUED,
                payload={
                    "essay_snapshot_ids": [s.id for s in essay_snapshots],
                    "count": len(essay_snapshots),
                },
            )
            self.session.add(gpt_job)
            jobs_queued.append(JobType.GPT.value)

        # Create RAG job for recommendations
        rag_job = AsyncJob(
            assessment_id=assessment.id,
            job_type=JobType.RAG,
            status=JobStatus.QUEUED,
            payload={"role_slug": assessment.role_slug},
        )
        self.session.add(rag_job)
        jobs_queued.append(JobType.RAG.value)

        # Create fusion job (combines all scores for final recommendation)
        fusion_job = AsyncJob(
            assessment_id=assessment.id,
            job_type=JobType.FUSION,
            status=JobStatus.QUEUED,
            payload={
                "depends_on": [JobType.GPT.value, JobType.RAG.value]
                if essay_snapshots
                else [JobType.RAG.value]
            },
        )
        self.session.add(fusion_job)
        jobs_queued.append(JobType.FUSION.value)

        return jobs_queued

    def _build_score_summary(self, scores: list[Score]) -> dict[str, Any]:
        """Build score summary grouped by question type."""
        summary: dict[str, Any] = {
            "theoretical": {"total": 0.0, "max": 0.0, "count": 0, "breakdown": []},
            "profile": {"total": 0.0, "max": 0.0, "count": 0, "breakdown": []},
            "essay": {"count": 0, "status": "pending_gpt"},  # Essays scored async
        }

        for score in scores:
            qtype = score.question_type.value
            if qtype in summary:
                summary[qtype]["total"] += score.score
                summary[qtype]["max"] += score.max_score
                summary[qtype]["count"] += 1
                summary[qtype]["breakdown"].append({
                    "question_id": score.question_snapshot_id,
                    "score": score.score,
                    "max_score": score.max_score,
                    "explanation": score.explanation,
                })

        # Calculate percentages
        for qtype in ["theoretical", "profile"]:
            if summary[qtype]["max"] > 0:
                summary[qtype]["percentage"] = round(
                    (summary[qtype]["total"] / summary[qtype]["max"]) * 100, 2
                )
            else:
                summary[qtype]["percentage"] = 0.0

        return summary
