"""update profile questions for personalization

Revision ID: 202501082201
Revises: 202412300001
Create Date: 2026-01-08 22:01:00

Updates profile questions 2-4 to capture user preferences:
- Q2: Technology preferences (what user wants to learn)
- Q3: Content duration preference (short/medium/long)
- Q4: Payment preference (free/paid/any)
"""

# revision identifiers, used by Alembic.
revision = "202501082201"
down_revision = "202412300001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update profile questions with personalization fields."""
    # Note: Questions are defined in reference_data.py and loaded at runtime
    # This migration is a marker for documentation purposes
    # The actual question updates are in the code changes to reference_data.py
    pass


def downgrade() -> None:
    """Revert profile questions to original form."""
    pass
