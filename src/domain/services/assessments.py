from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain import User
from src.infrastructure.db.models import (
    Assessment,
    AssessmentQuestionSnapshot,
    AssessmentResponse,
    AssessmentStatus,
    QuestionTemplate,
    RoleCatalog,
)

if TYPE_CHECKING:
    from sqlalchemy import Select


class RoleNotFoundError(Exception):
    """Raised when requested role slug does not exist."""


class MissingQuestionTemplateError(Exception):
    """Raised when a role is not configured with question templates."""


@dataclass(slots=True)
class AssessmentQuestionPayload:
    id: str
    sequence: int
    question_type: str
    prompt: str
    metadata: dict | None
    response: dict | None


class AssessmentService:
    """Domain logic for assessment lifecycle operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_or_resume(self, *, user: User, role_slug: str) -> dict[str, Any]:
        role = await self._get_role(role_slug)
        if role is None:
            raise RoleNotFoundError(f"Role '{role_slug}' tidak ditemukan")

        assessment = await self._find_active_assessment(user_id=user.user_id, role_slug=role_slug)
        if assessment is None:
            assessment = await self._create_assessment(user_id=user.user_id, role_slug=role_slug)

        questions = await self._build_questions_payload(assessment.id)
        return {
            "assessment_id": assessment.id,
            "status": assessment.status.value,
            "role": {
                "slug": role.slug,
                "name": role.name,
                "description": role.description,
                "question_count": len(questions),
            },
            "questions": [asdict(question) for question in questions],
        }

    async def _get_role(self, role_slug: str) -> RoleCatalog | None:
        stmt: Select[tuple[RoleCatalog]] = select(RoleCatalog).where(RoleCatalog.slug == role_slug)
        return await self.session.scalar(stmt)

    async def _find_active_assessment(self, *, user_id: str, role_slug: str) -> Assessment | None:
        stmt: Select[tuple[Assessment]] = (
            select(Assessment)
            .where(
                Assessment.owner_id == user_id,
                Assessment.role_slug == role_slug,
                Assessment.status.in_(AssessmentStatus.active_statuses()),
            )
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def _create_assessment(self, *, user_id: str, role_slug: str) -> Assessment:
        templates = await self._get_question_templates(role_slug)
        if not templates:
            raise MissingQuestionTemplateError(
                f"Role '{role_slug}' belum memiliki question templates"
            )

        assessment = Assessment(
            owner_id=user_id,
            role_slug=role_slug,
            status=AssessmentStatus.DRAFT,
        )
        self.session.add(assessment)
        await self.session.flush()

        for template in templates:
            snapshot = AssessmentQuestionSnapshot(
                assessment_id=assessment.id,
                question_template_id=template.id,
                sequence=template.sequence,
                question_type=template.question_type,
                prompt=template.prompt,
                metadata=template.metadata_ or {},
            )
            self.session.add(snapshot)

        await self.session.commit()
        await self.session.refresh(assessment)
        return assessment

    async def _get_question_templates(self, role_slug: str) -> list[QuestionTemplate]:
        stmt: Select[tuple[QuestionTemplate]] = (
            select(QuestionTemplate)
            .where(QuestionTemplate.role_slug == role_slug)
            .order_by(QuestionTemplate.sequence)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def _build_questions_payload(self, assessment_id: str) -> list[AssessmentQuestionPayload]:
        stmt = (
            select(AssessmentQuestionSnapshot, AssessmentResponse)
            .join(
                AssessmentResponse,
                AssessmentResponse.question_snapshot_id == AssessmentQuestionSnapshot.id,
                isouter=True,
            )
            .where(AssessmentQuestionSnapshot.assessment_id == assessment_id)
            .order_by(AssessmentQuestionSnapshot.sequence)
        )
        rows = (await self.session.execute(stmt)).all()

        payloads: list[AssessmentQuestionPayload] = []
        seen_ids: set[str] = set()
        for snapshot, response in rows:
            if snapshot.id in seen_ids:
                continue
            seen_ids.add(snapshot.id)
            payloads.append(
                AssessmentQuestionPayload(
                    id=snapshot.id,
                    sequence=snapshot.sequence,
                    question_type=snapshot.question_type.value,
                    prompt=snapshot.prompt,
                    metadata=snapshot.metadata_ or {},
                    response=response.response_data if response else None,
                )
            )
        return payloads
