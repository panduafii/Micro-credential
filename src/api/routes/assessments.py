from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_db_session, require_roles
from src.api.schemas.assessments import (
    AssessmentQuestion,
    AssessmentStartRequest,
    AssessmentStartResponse,
    AssessmentStatusResponse,
    AssessmentSubmitResponse,
    EssayScoreStatus,
    JobProgress,
    ScoreBreakdownItem,
    ScoreTypeDetail,
    StageProgress,
    SubmissionScores,
    WebhookRegisterRequest,
    WebhookRegisterResponse,
)
from src.api.schemas.tracks import TrackItem
from src.domain import User
from src.domain.services.assessments import (
    AssessmentService,
    MissingQuestionTemplateError,
    RoleNotFoundError,
)
from src.domain.services.status import (
    AssessmentNotFoundError as StatusNotFoundError,
)
from src.domain.services.status import (
    AssessmentNotOwnedError as StatusNotOwnedError,
)
from src.domain.services.status import (
    StatusService,
)
from src.domain.services.submission import (
    AssessmentAlreadySubmittedError,
    AssessmentExpiredError,
    AssessmentNotFoundError,
    AssessmentNotOwnedError,
    DuplicateSubmissionError,
    SubmissionService,
)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    payload: AssessmentStartRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(["student"])),
) -> AssessmentStartResponse:
    service = AssessmentService(session)
    try:
        result = await service.start_or_resume(user=user, role_slug=payload.role_slug)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MissingQuestionTemplateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AssessmentStartResponse(
        assessment_id=result["assessment_id"],
        status=result["status"],
        expires_at=result.get("expires_at"),
        role=TrackItem(**result["role"]),
        questions=[AssessmentQuestion(**question) for question in result["questions"]],
    )


@router.post("/{assessment_id}/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    assessment_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(["student"])),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> AssessmentSubmitResponse:
    """
    Submit an assessment for scoring (Story 2.1).

    - Locks all responses
    - Computes rule-based scores for theoretical/profile questions
    - Queues async jobs for GPT essay scoring, RAG, and fusion
    - Supports idempotency key to prevent duplicate submissions
    """
    service = SubmissionService(session)
    try:
        result = await service.submit_assessment(
            assessment_id=assessment_id,
            user_id=user.user_id,
            idempotency_key=idempotency_key,
        )
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AssessmentNotOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AssessmentAlreadySubmittedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AssessmentExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except DuplicateSubmissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    # Convert result to response schema
    return AssessmentSubmitResponse(
        assessment_id=result.assessment_id,
        status=result.status,
        submitted_at=result.submitted_at,
        degraded=result.degraded,
        scores=SubmissionScores(
            theoretical=ScoreTypeDetail(
                total=result.scores["theoretical"]["total"],
                max=result.scores["theoretical"]["max"],
                count=result.scores["theoretical"]["count"],
                percentage=result.scores["theoretical"].get("percentage", 0.0),
                breakdown=[
                    ScoreBreakdownItem(**item)
                    for item in result.scores["theoretical"].get("breakdown", [])
                ],
            ),
            profile=ScoreTypeDetail(
                total=result.scores["profile"]["total"],
                max=result.scores["profile"]["max"],
                count=result.scores["profile"]["count"],
                percentage=result.scores["profile"].get("percentage", 0.0),
                breakdown=[
                    ScoreBreakdownItem(**item)
                    for item in result.scores["profile"].get("breakdown", [])
                ],
            ),
            essay=EssayScoreStatus(
                count=result.scores["essay"]["count"],
                status=result.scores["essay"]["status"],
            ),
        ),
        jobs_queued=result.jobs_queued,
    )


# Story 2.3: Status Polling
@router.get("/{assessment_id}/status", response_model=AssessmentStatusResponse)
async def get_assessment_status(
    assessment_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(["student"])),
) -> AssessmentStatusResponse:
    """
    Get current status and progress of an assessment (Story 2.3).

    Returns:
    - Overall progress percentage
    - Stage-by-stage progress (rule_score, gpt, rag, fusion)
    - Individual job statuses
    - Webhook URL if registered
    """
    service = StatusService(session)
    try:
        result = await service.get_assessment_status(
            assessment_id=assessment_id, user_id=user.user_id
        )
    except StatusNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StatusNotOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return AssessmentStatusResponse(
        assessment_id=result.assessment_id,
        status=result.status,
        submitted_at=result.submitted_at,
        completed_at=result.completed_at,
        degraded=result.degraded,
        overall_progress=result.overall_progress,
        stages=[
            StageProgress(name=s.name, status=s.status, percentage=s.percentage)
            for s in result.stages
        ],
        jobs=[
            JobProgress(
                job_type=j.job_type,
                status=j.status,
                attempts=j.attempts,
                max_attempts=j.max_attempts,
                started_at=j.started_at,
                completed_at=j.completed_at,
                error=j.error,
            )
            for j in result.jobs
        ],
        webhook_url=result.webhook_url,
    )


# Story 2.3: Webhook Registration
@router.post("/{assessment_id}/webhook", response_model=WebhookRegisterResponse)
async def register_webhook(
    assessment_id: str,
    payload: WebhookRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(["student"])),
) -> WebhookRegisterResponse:
    """
    Register a webhook URL for assessment completion callbacks (Story 2.3).

    The webhook will be called with a POST request when:
    - All async jobs complete successfully
    - Processing fails after max retries
    """
    service = StatusService(session)
    try:
        result = await service.register_webhook(
            assessment_id=assessment_id,
            user_id=user.user_id,
            webhook_url=str(payload.webhook_url),
        )
    except StatusNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StatusNotOwnedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return WebhookRegisterResponse(
        assessment_id=result["assessment_id"],
        webhook_url=result["webhook_url"],
        registered_at=result["registered_at"],
    )
