from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_db_session, require_roles
from src.api.schemas.assessments import (
    AssessmentQuestion,
    AssessmentStartRequest,
    AssessmentStartResponse,
)
from src.api.schemas.tracks import TrackItem
from src.domain import User
from src.domain.services.assessments import (
    AssessmentService,
    MissingQuestionTemplateError,
    RoleNotFoundError,
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
        role=TrackItem(**result["role"]),
        questions=[AssessmentQuestion(**question) for question in result["questions"]],
    )
