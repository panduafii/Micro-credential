"""Add options column to question_templates for multiple choice

Revision ID: 202601080001
Revises: 202412300002
Create Date: 2026-01-08 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "202601080001"
down_revision: Union[str, None] = "202412300002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add options column to question_templates table."""
    # Add options column for multiple choice questions
    # Format: [{"id": "A", "text": "Option text"}, {"id": "B", "text": "Option text"}, ...]
    op.add_column(
        "question_templates",
        sa.Column("options", sa.JSON(), nullable=True),
    )

    # Also add options to assessment_question_snapshots for consistency
    op.add_column(
        "assessment_question_snapshots",
        sa.Column("options", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Remove options column from question_templates table."""
    op.drop_column("assessment_question_snapshots", "options")
    op.drop_column("question_templates", "options")
