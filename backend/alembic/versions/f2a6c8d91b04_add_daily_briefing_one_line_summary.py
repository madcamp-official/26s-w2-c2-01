"""add one-line summary to daily briefings

Revision ID: f2a6c8d91b04
Revises: e8b4a1f02c61
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a6c8d91b04"
down_revision: Union[str, None] = "e8b4a1f02c61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("daily_briefings", sa.Column("one_line_summary", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE daily_briefings
        SET one_line_summary = LEFT(regexp_replace(summary, E'[\\r\\n]+', ' ', 'g'), 80)
        WHERE summary IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("daily_briefings", "one_line_summary")
