from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class DailyBriefing(Base):
    __tablename__ = "daily_briefings"
    __table_args__ = (
        CheckConstraint("sentiment IN ('positive','neutral','negative')", name="ck_daily_briefings_sentiment"),
        CheckConstraint(
            "char_length(one_line_summary) BETWEEN 30 AND 40",
            name="ck_daily_briefings_one_line_summary_length",
        ),
        UniqueConstraint("ticker", "briefing_date", "briefing_session", name="uq_daily_briefings_ticker_date_session"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), nullable=False, index=True
    )
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False)
    briefing_session: Mapped[str] = mapped_column(String(20), nullable=False, default="additional")
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    one_line_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_factors: Mapped[list] = mapped_column(JSONB, default=list)
    negative_factors: Mapped[list] = mapped_column(JSONB, default=list)
    watch_issues: Mapped[list] = mapped_column(JSONB, default=list)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)
    today_actions: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    #: onupdate — 정기 갱신(하루 4번) 때마다 같은 행을 UPDATE하므로, 그때마다 이 값도 갱신되어야
    #: briefing_pipeline.py의 신선도 판단(REFRESH_INTERVAL_HOURS)이 정확해진다.
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class SectorBriefing(Base):
    """
    섹터별 일일 브리핑 — daily_briefings와 동일한 패턴이지만 ticker 대신 sector_id로
    묶인다. 섹터에 속한 종목들의 news_articles를 모아 같은 2단계 LLM 파이프라인으로
    생성한다 (app/services/sector_briefing_pipeline.py).
    """

    __tablename__ = "sector_briefings"
    __table_args__ = (
        CheckConstraint("sentiment IN ('positive','neutral','negative')", name="ck_sector_briefings_sentiment"),
        CheckConstraint(
            "char_length(one_line_summary) BETWEEN 30 AND 40",
            name="ck_sector_briefings_one_line_summary_length",
        ),
        UniqueConstraint("sector_id", "briefing_date", "briefing_session", name="uq_sector_briefings_sector_date_session"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sector_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False)
    briefing_session: Mapped[str] = mapped_column(String(20), nullable=False, default="additional")
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    one_line_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_factors: Mapped[list] = mapped_column(JSONB, default=list)
    negative_factors: Mapped[list] = mapped_column(JSONB, default=list)
    watch_issues: Mapped[list] = mapped_column(JSONB, default=list)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)
    today_actions: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class MarketOverview(Base):
    __tablename__ = "market_overviews"
    __table_args__ = (
        CheckConstraint("sentiment IN ('positive','neutral','negative')", name="ck_market_overviews_sentiment"),
        CheckConstraint(
            "char_length(one_line_summary) BETWEEN 30 AND 40",
            name="ck_market_overviews_one_line_summary_length",
        ),
        UniqueConstraint("briefing_date", "briefing_session", name="uq_market_overviews_date_session"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False)
    briefing_session: Mapped[str] = mapped_column(String(20), nullable=False, default="additional")
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    one_line_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_factors: Mapped[list] = mapped_column(JSONB, default=list)
    negative_factors: Mapped[list] = mapped_column(JSONB, default=list)
    watch_issues: Mapped[list] = mapped_column(JSONB, default=list)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)
    today_actions: Mapped[list] = mapped_column(JSONB, default=list)
    indices: Mapped[dict] = mapped_column(JSONB, default=dict)
    sector_moves: Mapped[dict] = mapped_column(JSONB, default=dict)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
