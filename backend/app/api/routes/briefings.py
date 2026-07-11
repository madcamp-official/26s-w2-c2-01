from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.watchlist import list_watchlist
from app.db.session import get_db
from app.models.briefing import DailyBriefing, MarketOverview
from app.models.user import User
from app.schemas.briefing import TodayBriefingResponse
from app.services.briefing_pipeline import generate_daily_briefing

router = APIRouter(prefix="/briefings", tags=["briefings"])


@router.get("/today", response_model=TodayBriefingResponse)
def today_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    관심 종목별 오늘자 브리핑을 반환한다. daily_briefings 캐시에 없는 종목은
    이 요청 안에서 온디맨드로 생성해 채운다 (기획서.md 7-1절 "on-demand 보완").
    LLM API가 아직 정해지지 않아 지금은 스텁 파이프라인이 생성한다
    (app/services/llm/factory.py).
    """
    today = date.today()
    watchlist = list_watchlist(db, current_user.id)
    tickers = [w.ticker for w in watchlist]

    briefings: list[DailyBriefing] = []
    if tickers:
        stmt = select(DailyBriefing).where(
            DailyBriefing.ticker.in_(tickers), DailyBriefing.briefing_date == today
        )
        briefings = list(db.scalars(stmt).all())

    found_tickers = {b.ticker for b in briefings}
    missing_tickers = [t for t in tickers if t not in found_tickers]

    still_missing: list[str] = []
    for ticker in missing_tickers:
        try:
            briefings.append(generate_daily_briefing(db, ticker, briefing_date=today))
        except ValueError:
            still_missing.append(ticker)

    market_overview = db.scalar(select(MarketOverview).where(MarketOverview.briefing_date == today))

    return TodayBriefingResponse(
        market_overview=market_overview,
        stocks=briefings,
        missing_tickers=still_missing,
    )
