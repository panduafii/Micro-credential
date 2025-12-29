from __future__ import annotations

from pydantic import BaseModel, Field
from src.api.schemas.tracks import TrackItem


class AssessmentStartRequest(BaseModel):
    role_slug: str = Field(..., description="Role/track identifier to start or resume")


class AssessmentQuestion(BaseModel):
    id: str
    sequence: int
    question_type: str
    prompt: str
    metadata: dict | None = None
    response: dict | None = None


class AssessmentStartResponse(BaseModel):
    assessment_id: str
    status: str
    expires_at: str | None = Field(None, description="ISO timestamp when assessment expires")
    role: TrackItem
    questions: list[AssessmentQuestion]


# Story 2.1: Submission schemas
class ScoreBreakdownItem(BaseModel):
    question_id: str
    score: float
    max_score: float
    explanation: str | None = None


class ScoreTypeDetail(BaseModel):
    total: float = 0.0
    max: float = 0.0
    count: int = 0
    percentage: float = 0.0
    breakdown: list[ScoreBreakdownItem] = []


class EssayScoreStatus(BaseModel):
    count: int = 0
    status: str = "pending_gpt"


class SubmissionScores(BaseModel):
    theoretical: ScoreTypeDetail
    profile: ScoreTypeDetail
    essay: EssayScoreStatus


class AssessmentSubmitResponse(BaseModel):
    assessment_id: str
    status: str
    submitted_at: str
    degraded: bool = Field(
        False, description="True if submission had missing or incomplete data"
    )
    scores: SubmissionScores
    jobs_queued: list[str] = Field(
        default_factory=list, description="Async job types queued (gpt, rag, fusion)"
    )
