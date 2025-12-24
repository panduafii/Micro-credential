from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class QuestionType(str, enum.Enum):
    THEORETICAL = "theoretical"
    ESSAY = "essay"
    PROFILE = "profile"


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    @classmethod
    def active_statuses(cls) -> tuple["AssessmentStatus", ...]:
        return (cls.DRAFT, cls.IN_PROGRESS)


class RoleCatalog(Base):
    __tablename__ = "role_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    question_templates: Mapped[list["QuestionTemplate"]] = relationship(
        back_populates="role",
        cascade="all,delete",
    )


class QuestionTemplate(Base):
    __tablename__ = "question_templates"
    __table_args__ = (UniqueConstraint("role_slug", "sequence", name="uq_question_sequence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_slug: Mapped[str] = mapped_column(ForeignKey("role_catalog.slug", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSON)

    role: Mapped[RoleCatalog] = relationship(back_populates="question_templates")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role_slug: Mapped[str] = mapped_column(ForeignKey("role_catalog.slug", ondelete="RESTRICT"), nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(Enum(AssessmentStatus), default=AssessmentStatus.DRAFT, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    role: Mapped[RoleCatalog] = relationship()
    question_snapshots: Mapped[list["AssessmentQuestionSnapshot"]] = relationship(
        back_populates="assessment",
        cascade="all,delete-orphan",
        order_by="AssessmentQuestionSnapshot.sequence",
    )
    responses: Mapped[list["AssessmentResponse"]] = relationship(back_populates="assessment", cascade="all,delete-orphan")


class AssessmentQuestionSnapshot(Base):
    __tablename__ = "assessment_question_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_templates.id", ondelete="SET NULL"),
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSON)

    assessment: Mapped[Assessment] = relationship(back_populates="question_snapshots")
    template: Mapped[QuestionTemplate | None] = relationship()
    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="question_snapshot",
        cascade="all,delete-orphan",
    )


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_question_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    response_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assessment: Mapped[Assessment] = relationship(back_populates="responses")
    question_snapshot: Mapped[AssessmentQuestionSnapshot] = relationship(back_populates="responses")
