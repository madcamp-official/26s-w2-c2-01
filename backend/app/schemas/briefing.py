from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DailyBriefingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    briefing_date: date
    sentiment: Literal["positive", "neutral", "negative"] | None
    summary: str | None
    positive_factors: list
    negative_factors: list
    watch_issues: list
    reasons: list
    today_actions: list
    model: str | None
    generated_at: datetime


class MarketOverviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    briefing_date: date
    summary: str | None
    indices: dict
    sector_moves: dict
    generated_at: datetime


class TodayBriefingResponse(BaseModel):
    market_overview: MarketOverviewRead | None
    stocks: list[DailyBriefingRead]
    missing_tickers: list[str]
