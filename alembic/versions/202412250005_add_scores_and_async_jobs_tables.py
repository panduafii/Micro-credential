"""Add scores and async_jobs tables

Revision ID: 202412250005
Revises: 202412250004
Create Date: 2025-12-30

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "202412250005"
down_revision = "202412250004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add degraded column to assessments
    op.add_column(
        "assessments",
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Add new assessment statuses (submitted, failed)
    # For PostgreSQL, we need to alter the enum type
    op.execute("ALTER TYPE assessmentstatus ADD VALUE IF NOT EXISTS 'submitted'")
    op.execute("ALTER TYPE assessmentstatus ADD VALUE IF NOT EXISTS 'failed'")

    # Create jobtype enum
    op.execute("CREATE TYPE jobtype AS ENUM ('gpt', 'rag', 'fusion')")

    # Create jobstatus enum
    op.execute("CREATE TYPE jobstatus AS ENUM ('queued', 'in_progress', 'completed', 'failed')")

    # Create scores table
    op.create_table(
        "scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(36),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "question_snapshot_id",
            sa.String(36),
            sa.ForeignKey("assessment_question_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_type",
            sa.Enum("theoretical", "essay", "profile", name="questiontype", create_type=False),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("scoring_method", sa.String(32), nullable=False),
        sa.Column("rules_applied", sa.JSON(), nullable=True),
        sa.Column("model_info", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("assessment_id", "question_snapshot_id", name="uq_score_per_question"),
    )

    # Create async_jobs table
    op.create_table(
        "async_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(36),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "job_type",
            sa.Enum("gpt", "rag", "fusion", name="jobtype", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "in_progress",
                "completed",
                "failed",
                name="jobstatus",
                create_type=False,
            ),
            nullable=False,
            index=True,
            server_default="queued",
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("error_payload", sa.JSON(), nullable=True),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("async_jobs")
    op.drop_table("scores")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS jobtype")

    # Remove degraded column
    op.drop_column("assessments", "degraded")

    # Note: Cannot easily remove enum values in PostgreSQL
