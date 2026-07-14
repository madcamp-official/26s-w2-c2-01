"""add 30-40 character summaries to all briefing types

Revision ID: c4f82d6a1e93
Revises: b7e31a4c9d52
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f82d6a1e93"
down_revision: Union[str, None] = "b7e31a4c9d52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_daily_briefings_one_line_summary_length",
        "daily_briefings",
        type_="check",
    )
    op.execute(
        """
        UPDATE daily_briefings
        SET one_line_summary = NULL
        WHERE one_line_summary IS NOT NULL
          AND char_length(one_line_summary) NOT BETWEEN 30 AND 40
        """
    )
    op.create_check_constraint(
        "ck_daily_briefings_one_line_summary_length",
        "daily_briefings",
        "char_length(one_line_summary) BETWEEN 30 AND 40",
    )

    op.add_column("sector_briefings", sa.Column("one_line_summary", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_sector_briefings_one_line_summary_length",
        "sector_briefings",
        "char_length(one_line_summary) BETWEEN 30 AND 40",
    )

    op.add_column("market_overviews", sa.Column("one_line_summary", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_market_overviews_one_line_summary_length",
        "market_overviews",
        "char_length(one_line_summary) BETWEEN 30 AND 40",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_market_overviews_one_line_summary_length",
        "market_overviews",
        type_="check",
    )
    op.drop_column("market_overviews", "one_line_summary")
    op.drop_constraint(
        "ck_sector_briefings_one_line_summary_length",
        "sector_briefings",
        type_="check",
    )
    op.drop_column("sector_briefings", "one_line_summary")

    op.drop_constraint(
        "ck_daily_briefings_one_line_summary_length",
        "daily_briefings",
        type_="check",
    )
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
