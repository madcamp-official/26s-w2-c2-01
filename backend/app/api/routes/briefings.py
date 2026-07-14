from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.batch.collect_news import FinnhubNotConfigured, collect_for_ticker
from app.batch.collect_news import run as collect_news_run
from app.crud.sector_watchlist import list_sector_watchlist
from app.crud.watchlist import list_watchlist
from app.db.session import get_db
from app.models.briefing import DailyBriefing, MarketOverview, SectorBriefing
from app.models.user import User
from app.schemas.briefing import (
    DailyBriefingRead,
    MarketOverviewRead,
    SectorBriefingRead,
    TodayBriefingResponse,
)
from app.services.briefing_pipeline import generate_daily_briefing
from app.services.freshness import is_same_calendar_day
from app.services.market_overview_pipeline import generate_market_overview
from app.services.sector_briefing_pipeline import generate_sector_briefing

router = APIRouter(prefix="/briefings", tags=["briefings"])


@router.get("/today", response_model=TodayBriefingResponse)
def today_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    관심 종목별 오늘자 브리핑 + 전체 시황을 반환한다. 캐시에 없거나
    REFRESH_INTERVAL_HOURS보다 오래됐으면 이 요청 안에서 온디맨드로 생성해
    채운다 (기획서.md 7-1절 "on-demand 보완").
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

    sector_watchlist = list_sector_watchlist(db, current_user.id)
    sector_ids = [sw.sector_id for sw in sector_watchlist]

    sector_briefings: list[SectorBriefing] = []
    if sector_ids:
        stmt = select(SectorBriefing).where(
            SectorBriefing.sector_id.in_(sector_ids), SectorBriefing.briefing_date == today
        )
        sector_briefings = list(db.scalars(stmt).all())

    found_sector_ids = {b.sector_id for b in sector_briefings}
    missing_sector_ids = [sid for sid in sector_ids if sid not in found_sector_ids]

    still_missing_sectors: list[int] = []
    for sector_id in missing_sector_ids:
        try:
            sector_briefings.append(generate_sector_briefing(db, sector_id, briefing_date=today))
        except ValueError:
            still_missing_sectors.append(sector_id)

    try:
        market_overview = generate_market_overview(db, briefing_date=today)
    except Exception as e:  # noqa: BLE001 - 시황 생성 실패해도 종목 브리핑은 정상 반환
        print(f"전체 시황 생성 실패: {e}")
        market_overview = None

    return TodayBriefingResponse(
        market_overview=market_overview,
        stocks=briefings,
        missing_tickers=still_missing,
        sector_briefings=sector_briefings,
        missing_sectors=still_missing_sectors,
    )


@router.post("/refresh", response_model=TodayBriefingResponse)
def refresh_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    사용자가 원할 때 직접 오늘자 브리핑을 새로고침한다 — REFRESH_INTERVAL_HOURS
    신선도와 무관하게 강제로 재생성한다. 정기 스케줄과 별개로 LLM 호출이
    추가로 늘어나는 셈이라, 원래는 유저당 하루 1회로 제한했다(User.last_manual_refresh_at).
    Gemma2(Ollama) 테스트 기간 동안 임시로 제한을 꺼둔 상태 — 나중에 아래 if문을 복구할 것.
    """
    # if is_same_calendar_day(db, current_user.last_manual_refresh_at):
    #     raise HTTPException(
    #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    #         detail="오늘은 이미 새로고침을 사용했습니다. 내일 다시 시도해주세요.",
    #     )

    try:
        collect_news_run()
    except FinnhubNotConfigured:
        pass
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 강제 재생성은 계속 시도
        print(f"수동 새로고침 - 뉴스 재수집 중 오류: {e}")

    today = date.today()
    watchlist = list_watchlist(db, current_user.id)
    tickers = [w.ticker for w in watchlist]

    briefings: list[DailyBriefing] = []
    still_missing: list[str] = []
    for ticker in tickers:
        try:
            briefings.append(generate_daily_briefing(db, ticker, briefing_date=today, force=True))
        except ValueError:
            still_missing.append(ticker)

    sector_ids = [sw.sector_id for sw in list_sector_watchlist(db, current_user.id)]
    sector_briefings: list[SectorBriefing] = []
    still_missing_sectors: list[int] = []
    for sector_id in sector_ids:
        try:
            sector_briefings.append(generate_sector_briefing(db, sector_id, briefing_date=today, force=True))
        except ValueError:
            still_missing_sectors.append(sector_id)

    try:
        market_overview = generate_market_overview(db, briefing_date=today, force=True)
    except Exception as e:  # noqa: BLE001 - 시황 생성 실패해도 종목 브리핑은 정상 반환
        print(f"수동 새로고침 - 전체 시황 생성 실패: {e}")
        market_overview = None

    current_user.last_manual_refresh_at = db.scalar(select(func.now())).replace(tzinfo=None)
    db.commit()

    return TodayBriefingResponse(
        market_overview=market_overview,
        stocks=briefings,
        missing_tickers=still_missing,
        sector_briefings=sector_briefings,
        missing_sectors=still_missing_sectors,
    )


@router.post("/refresh/stocks/{ticker}", response_model=DailyBriefingRead)
def refresh_stock_briefing(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 사용자의 관심 종목 하나만 오늘자로 강제 재생성한다."""
    ticker = ticker.upper()
    followed_tickers = {item.ticker for item in list_watchlist(db, current_user.id)}
    if ticker not in followed_tickers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심 종목에서 찾을 수 없습니다.")

    # 뉴스 재수집 없이 바로 재생성하면 DB에 이미 있는(오래된) 뉴스만 보게 되어
    # "새로고침해도 최신 이슈가 안 잡히는" 문제가 생긴다 — 이 종목만 가볍게 먼저 수집한다.
    try:
        collect_for_ticker(db, ticker, since=date.today() - timedelta(days=3), until=date.today(), limit=8)
    except FinnhubNotConfigured:
        pass
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 강제 재생성은 계속 시도
        print(f"종목 단건 새로고침 - 뉴스 재수집 중 오류: {e}")

    try:
        return generate_daily_briefing(db, ticker, briefing_date=date.today(), force=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/refresh/overview", response_model=MarketOverviewRead)
def refresh_market_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """전체 종목·섹터 브리핑은 건드리지 않고 오늘의 전체 시황만 강제 재생성한다."""
    try:
        return generate_market_overview(db, briefing_date=date.today(), force=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/refresh/sectors/{sector_id}", response_model=SectorBriefingRead)
def refresh_single_sector_briefing(
    sector_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 사용자의 관심 섹터 하나만 오늘자로 강제 재생성한다."""
    followed_sector_ids = {item.sector_id for item in list_sector_watchlist(db, current_user.id)}
    if sector_id not in followed_sector_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심 섹터에서 찾을 수 없습니다.")

    try:
        return generate_sector_briefing(db, sector_id, briefing_date=date.today(), force=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/history", response_model=list[DailyBriefingRead])
def briefing_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """관심종목 전체의 과거 브리핑을 날짜 역순으로 반환한다 (Claude 재호출 없이 DB 조회만)."""
    watchlist = list_watchlist(db, current_user.id)
    tickers = [w.ticker for w in watchlist]
    if not tickers:
        return []

    stmt = (
        select(DailyBriefing)
        .where(DailyBriefing.ticker.in_(tickers))
        .order_by(DailyBriefing.briefing_date.desc(), DailyBriefing.ticker)
    )
    return list(db.scalars(stmt).all())


@router.get("/history/overview", response_model=list[MarketOverviewRead])
def market_overview_history(db: Session = Depends(get_db)):
    """전체 시황(종목 무관)의 과거 이력을 날짜 역순으로 반환한다. 종목별과 달리 유저 무관 전역 데이터."""
    stmt = select(MarketOverview).order_by(MarketOverview.briefing_date.desc())
    return list(db.scalars(stmt).all())


@router.get("/history/sectors", response_model=list[SectorBriefingRead])
def sector_briefing_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """관심 섹터 전체의 과거 브리핑을 날짜 역순으로 반환한다 (Claude 재호출 없이 DB 조회만)."""
    sector_ids = [sw.sector_id for sw in list_sector_watchlist(db, current_user.id)]
    if not sector_ids:
        return []

    stmt = (
        select(SectorBriefing)
        .where(SectorBriefing.sector_id.in_(sector_ids))
        .order_by(SectorBriefing.briefing_date.desc(), SectorBriefing.sector_id)
    )
    return list(db.scalars(stmt).all())
