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
    sentiment: Literal["positive", "neutral", "negative"] | None
    summary: str | None
    positive_factors: list
    negative_factors: list
    watch_issues: list
    reasons: list
    today_actions: list
    indices: dict
    sector_moves: dict
    model: str | None
    generated_at: datetime


class MarketOverviewRefreshJobRead(BaseModel):
    job_id: str
    status: Literal["running", "completed", "failed"]
    error: str | None = None


class SectorBriefingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sector_id: int
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


class TodayBriefingResponse(BaseModel):
    market_overview: MarketOverviewRead | None
    stocks: list[DailyBriefingRead]
    missing_tickers: list[str]
    sector_briefings: list[SectorBriefingRead] = []
    missing_sectors: list[int] = []
