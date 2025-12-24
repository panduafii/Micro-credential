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
