"""enforce 30-character one-line summaries

Revision ID: b7e31a4c9d52
Revises: f2a6c8d91b04
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b7e31a4c9d52"
down_revision: Union[str, None] = "f2a6c8d91b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The previous migration temporarily backfilled this field by cutting the
    # detailed summary. Discard those overlong placeholders so the pipeline
    # regenerates a real short summary instead of displaying clipped text.
    op.execute(
        """
        UPDATE daily_briefings
        SET one_line_summary = NULL
        WHERE char_length(one_line_summary) > 30
        """
    )
    op.create_check_constraint(
        "ck_daily_briefings_one_line_summary_length",
        "daily_briefings",
        "char_length(one_line_summary) <= 30",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_daily_briefings_one_line_summary_length",
        "daily_briefings",
        type_="check",
    )
