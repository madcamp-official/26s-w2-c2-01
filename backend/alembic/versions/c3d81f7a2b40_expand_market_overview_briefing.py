"""expand market overview briefing fields

Revision ID: c3d81f7a2b40
Revises: 9a4f2c1d7e30
Create Date: 2026-07-14
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "c3d81f7a2b40"
down_revision: Union[str, None] = "9a4f2c1d7e30"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    empty_list = sa.text("'[]'::jsonb")
    op.add_column("market_overviews", sa.Column("sentiment", sa.String(length=10), nullable=True))
    op.add_column(
        "market_overviews",
        sa.Column("positive_factors", postgresql.JSONB(astext_type=sa.Text()), server_default=empty_list, nullable=False),
    )
    op.add_column(
        "market_overviews",
        sa.Column("negative_factors", postgresql.JSONB(astext_type=sa.Text()), server_default=empty_list, nullable=False),
    )
    op.add_column(
        "market_overviews",
        sa.Column("watch_issues", postgresql.JSONB(astext_type=sa.Text()), server_default=empty_list, nullable=False),
    )
    op.add_column(
        "market_overviews",
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), server_default=empty_list, nullable=False),
    )
    op.add_column(
        "market_overviews",
        sa.Column("today_actions", postgresql.JSONB(astext_type=sa.Text()), server_default=empty_list, nullable=False),
    )
    op.create_check_constraint(
        "ck_market_overviews_sentiment",
        "market_overviews",
        "sentiment IN ('positive','neutral','negative')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_market_overviews_sentiment", "market_overviews", type_="check")
    op.drop_column("market_overviews", "today_actions")
    op.drop_column("market_overviews", "reasons")
    op.drop_column("market_overviews", "watch_issues")
    op.drop_column("market_overviews", "negative_factors")
    op.drop_column("market_overviews", "positive_factors")
    op.drop_column("market_overviews", "sentiment")
