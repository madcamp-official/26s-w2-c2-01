"""add sector tables and manual refresh timestamp

Revision ID: 9a4f2c1d7e30
Revises: 6c700992b858
Create Date: 2026-07-13
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9a4f2c1d7e30"
down_revision: Union[str, None] = "6c700992b858"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_manual_refresh_at", sa.DateTime(), nullable=True))

    op.create_table(
        "sector_briefings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.Column("briefing_date", sa.Date(), nullable=False),
        sa.Column("sentiment", sa.String(length=10), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("positive_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("negative_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("watch_issues", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("today_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=True),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "sentiment IN ('positive','neutral','negative')",
            name="ck_sector_briefings_sentiment",
        ),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sector_id", "briefing_date", name="uq_sector_briefings_sector_date"),
    )
    op.create_index(
        op.f("ix_sector_briefings_sector_id"),
        "sector_briefings",
        ["sector_id"],
        unique=False,
    )

    op.create_table(
        "sector_watchlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sector_id", name="uq_sector_watchlists_user_sector"),
    )
    op.create_index(
        op.f("ix_sector_watchlists_sector_id"),
        "sector_watchlists",
        ["sector_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sector_watchlists_user_id"),
        "sector_watchlists",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sector_watchlists_user_id"), table_name="sector_watchlists")
    op.drop_index(op.f("ix_sector_watchlists_sector_id"), table_name="sector_watchlists")
    op.drop_table("sector_watchlists")
    op.drop_index(op.f("ix_sector_briefings_sector_id"), table_name="sector_briefings")
    op.drop_table("sector_briefings")
    op.drop_column("users", "last_manual_refresh_at")
