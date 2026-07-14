"""store four briefing snapshots per market day

Revision ID: e8b4a1f02c61
Revises: c3d81f7a2b40
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8b4a1f02c61"
down_revision: Union[str, None] = "c3d81f7a2b40"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    for table in ("daily_briefings", "sector_briefings", "market_overviews"):
        op.add_column(table, sa.Column("briefing_session", sa.String(length=20), server_default="after_hours", nullable=False))
    op.drop_constraint("uq_daily_briefings_ticker_date", "daily_briefings", type_="unique")
    op.create_unique_constraint("uq_daily_briefings_ticker_date_session", "daily_briefings", ["ticker", "briefing_date", "briefing_session"])
    op.drop_constraint("uq_sector_briefings_sector_date", "sector_briefings", type_="unique")
    op.create_unique_constraint("uq_sector_briefings_sector_date_session", "sector_briefings", ["sector_id", "briefing_date", "briefing_session"])
    op.drop_constraint("market_overviews_briefing_date_key", "market_overviews", type_="unique")
    op.create_unique_constraint("uq_market_overviews_date_session", "market_overviews", ["briefing_date", "briefing_session"])


def downgrade() -> None:
    op.drop_constraint("uq_market_overviews_date_session", "market_overviews", type_="unique")
    op.drop_constraint("uq_sector_briefings_sector_date_session", "sector_briefings", type_="unique")
    op.drop_constraint("uq_daily_briefings_ticker_date_session", "daily_briefings", type_="unique")
    op.create_unique_constraint("market_overviews_briefing_date_key", "market_overviews", ["briefing_date"])
    op.create_unique_constraint("uq_sector_briefings_sector_date", "sector_briefings", ["sector_id", "briefing_date"])
    op.create_unique_constraint("uq_daily_briefings_ticker_date", "daily_briefings", ["ticker", "briefing_date"])
    for table in ("market_overviews", "sector_briefings", "daily_briefings"):
        op.drop_column(table, "briefing_session")
