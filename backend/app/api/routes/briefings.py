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

router = APIRouter(prefix="/briefings", tags=["briefings"])


@router.get("/today", response_model=TodayBriefingResponse)
def today_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    관심 종목별 오늘자 캐시된 브리핑을 반환한다.
    뉴스 수집·Claude 파이프라인은 아직 미구현이라, 캐시가 없는 종목은
    missing_tickers 로 알려주고 프론트가 안내 문구를 보여줄 수 있게 한다.
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

    market_overview = db.scalar(select(MarketOverview).where(MarketOverview.briefing_date == today))

    return TodayBriefingResponse(
        market_overview=market_overview,
        stocks=briefings,
        missing_tickers=missing_tickers,
    )
