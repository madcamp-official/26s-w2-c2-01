from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class DailyBriefing(Base):
    __tablename__ = "daily_briefings"
    __table_args__ = (
        CheckConstraint("sentiment IN ('positive','neutral','negative')", name="ck_daily_briefings_sentiment"),
        UniqueConstraint("ticker", "briefing_date", name="uq_daily_briefings_ticker_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), nullable=False, index=True
    )
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_factors: Mapped[list] = mapped_column(JSONB, default=list)
    negative_factors: Mapped[list] = mapped_column(JSONB, default=list)
    watch_issues: Mapped[list] = mapped_column(JSONB, default=list)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)
    today_actions: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MarketOverview(Base):
    __tablename__ = "market_overviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    briefing_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    indices: Mapped[dict] = mapped_column(JSONB, default=dict)
    sector_moves: Mapped[dict] = mapped_column(JSONB, default=dict)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())
