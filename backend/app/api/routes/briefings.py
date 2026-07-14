from datetime import timedelta
from math import ceil
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.batch.collect_news import FinnhubNotConfigured, collect_for_ticker
from app.batch.collect_news import run as collect_news_run
from app.crud.sector_watchlist import list_sector_watchlist
from app.crud.watchlist import list_watchlist
from app.db.session import SessionLocal, get_db
from app.models.briefing import DailyBriefing, MarketOverview, SectorBriefing
from app.models.user import User
from app.schemas.briefing import (
    BriefingSessionRead,
    DailyBriefingRead,
    MarketOverviewRefreshJobRead,
    MarketOverviewRead,
    SectorBriefingRead,
    TodayBriefingResponse,
)
from app.services.briefing_pipeline import generate_daily_briefing
from app.services.market_overview_pipeline import generate_market_overview
from app.services.market_sessions import (
    SESSION_DEFINITIONS,
    current_briefing_date,
    current_session,
    now_kst,
    scheduled_at,
    session_rank,
)
from app.services.sector_briefing_pipeline import generate_sector_briefing

router = APIRouter(prefix="/briefings", tags=["briefings"])

_overview_refresh_jobs: dict[str, dict[str, str | None]] = {}
_overview_refresh_jobs_lock = Lock()
MANUAL_REFRESH_COOLDOWN = timedelta(minutes=0)


def _claim_manual_refresh(db: Session, user_id: int) -> None:
    """한 사용자의 모든 수동 새로고침에 공통 30분 쿨다운을 원자적으로 적용한다."""
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")

    server_now = db.scalar(select(func.now())).replace(tzinfo=None)
    if user.last_manual_refresh_at is not None:
        remaining = MANUAL_REFRESH_COOLDOWN - (server_now - user.last_manual_refresh_at)
        if remaining.total_seconds() > 0:
            seconds = max(1, ceil(remaining.total_seconds()))
            minutes = max(1, ceil(seconds / 60))
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"새로고침은 30분에 한 번만 가능합니다. 약 {minutes}분 후 다시 시도해주세요.",
                headers={"Retry-After": str(seconds)},
            )

    user.last_manual_refresh_at = server_now
    db.commit()


def _run_market_overview_refresh(job_id: str) -> None:
    """HTTP 응답과 분리된 스레드에서 전체 시황을 생성해 Cloudflare 524를 피한다."""
    db = SessionLocal()
    try:
        generate_market_overview(db, force=True, briefing_session="additional")
    except Exception as exc:  # noqa: BLE001 - 작업 상태로 전달하고 API 프로세스는 유지
        db.rollback()
        print(f"전체 시황 백그라운드 새로고침 실패: {exc}")
        with _overview_refresh_jobs_lock:
            _overview_refresh_jobs[job_id] = {
                "job_id": job_id,
                "status": "failed",
                "error": str(exc),
            }
    else:
        with _overview_refresh_jobs_lock:
            _overview_refresh_jobs[job_id] = {
                "job_id": job_id,
                "status": "completed",
                "error": None,
            }
    finally:
        db.close()


@router.get("/today", response_model=TodayBriefingResponse)
def today_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    관심 종목별 오늘자 브리핑 + 전체 시황을 조회만 한다.

    정기 세션 생성은 스케줄러가, 사용자가 요청한 추가 생성은 refresh API가
    담당한다. 화면 조회가 브리핑을 암묵적으로 생성하면 스케줄러 비활성 환경에서도
    현재 시간대 브리핑이 생기므로 이 엔드포인트에서는 생성하지 않는다.
    """
    today = current_briefing_date()
    active_session = current_session(today)
    watchlist = list_watchlist(db, current_user.id)
    tickers = [w.ticker for w in watchlist]

    briefings: list[DailyBriefing] = []
    if tickers:
        stmt = select(DailyBriefing).where(
            DailyBriefing.ticker.in_(tickers), DailyBriefing.briefing_date == today
        )
        briefings = list(db.scalars(stmt).all())

    found_tickers = {b.ticker for b in briefings if b.briefing_session == active_session}
    missing_tickers = [t for t in tickers if t not in found_tickers]

    still_missing = missing_tickers

    sector_watchlist = list_sector_watchlist(db, current_user.id)
    sector_ids = [sw.sector_id for sw in sector_watchlist]

    sector_briefings: list[SectorBriefing] = []
    if sector_ids:
        stmt = select(SectorBriefing).where(
            SectorBriefing.sector_id.in_(sector_ids), SectorBriefing.briefing_date == today
        )
        sector_briefings = list(db.scalars(stmt).all())

    found_sector_ids = {
        b.sector_id for b in sector_briefings if b.briefing_session == active_session
    }
    missing_sector_ids = [sid for sid in sector_ids if sid not in found_sector_ids]

    still_missing_sectors = missing_sector_ids

    market_overviews = list(db.scalars(
        select(MarketOverview).where(MarketOverview.briefing_date == today)
    ).all())

    current = now_kst()
    available_keys = {
        item.key for item in SESSION_DEFINITIONS if scheduled_at(today, item) <= current
    }
    available_keys.add("additional")
    # 마이그레이션된 기존 행이나 잘못된 서버 시각 때문에 미래 세션 내용이 노출되지 않게 한다.
    briefings = [item for item in briefings if item.briefing_session in available_keys]
    sector_briefings = [
        item for item in sector_briefings if item.briefing_session in available_keys
    ]
    market_overviews = [
        item for item in market_overviews if item.briefing_session in available_keys
    ]
    briefings.sort(key=lambda item: session_rank(item.briefing_session))
    sector_briefings.sort(key=lambda item: session_rank(item.briefing_session))
    market_overviews.sort(key=lambda item: session_rank(item.briefing_session))
    market_overview = market_overviews[-1] if market_overviews else None
    market_date = today - timedelta(days=1)
    session_labels = {
        "market_open": f"{market_date.day}일 장시작",
        "intraday": f"{market_date.day}일 장중",
        "market_close": f"{market_date.day}일 장마감",
        "after_hours": f"{market_date.day}~{today.day}일 시간외",
    }
    sessions = [
        BriefingSessionRead(
            key=item.key,
            label=session_labels[item.key],
            available=scheduled_at(today, item) <= current,
            scheduled_at=scheduled_at(today, item),
        )
        for item in SESSION_DEFINITIONS
    ]

    return TodayBriefingResponse(
        briefing_date=today,
        sessions=sessions,
        market_overview=market_overview,
        market_overviews=market_overviews,
        stocks=briefings,
        missing_tickers=still_missing,
        sector_briefings=sector_briefings,
        missing_sectors=still_missing_sectors,
    )


@router.post("/refresh", response_model=TodayBriefingResponse)
def refresh_briefing(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    사용자가 원할 때 직접 오늘자 브리핑을 새로고침한다.
    모든 수동 새로고침은 사용자별로 30분에 한 번만 허용한다.
    """
    _claim_manual_refresh(db, current_user.id)

    try:
        collect_news_run()
    except FinnhubNotConfigured:
        pass
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 강제 재생성은 계속 시도
        print(f"수동 새로고침 - 뉴스 재수집 중 오류: {e}")

    today = current_briefing_date()
    watchlist = list_watchlist(db, current_user.id)
    tickers = [w.ticker for w in watchlist]

    briefings: list[DailyBriefing] = []
    still_missing: list[str] = []
    for ticker in tickers:
        try:
            briefings.append(generate_daily_briefing(
                db, ticker, briefing_date=today, force=True, briefing_session="additional"
            ))
        except ValueError:
            still_missing.append(ticker)
        except RuntimeError as exc:  # noqa: BLE001 - LLM 생성 실패해도 나머지 종목은 계속 진행
            print(f"{ticker} 브리핑 생성 실패, 건너뜀: {exc}")
            still_missing.append(ticker)

    sector_ids = [sw.sector_id for sw in list_sector_watchlist(db, current_user.id)]
    sector_briefings: list[SectorBriefing] = []
    still_missing_sectors: list[int] = []
    for sector_id in sector_ids:
        try:
            sector_briefings.append(generate_sector_briefing(
                db, sector_id, briefing_date=today, force=True, briefing_session="additional"
            ))
        except ValueError:
            still_missing_sectors.append(sector_id)
        except RuntimeError as exc:  # noqa: BLE001 - LLM 생성 실패해도 나머지 섹터는 계속 진행
            print(f"섹터 {sector_id} 브리핑 생성 실패, 건너뜀: {exc}")
            still_missing_sectors.append(sector_id)

    try:
        market_overview = generate_market_overview(
            db, briefing_date=today, force=True, briefing_session="additional"
        )
    except Exception as e:  # noqa: BLE001 - 시황 생성 실패해도 종목 브리핑은 정상 반환
        print(f"수동 새로고침 - 전체 시황 생성 실패: {e}")
        market_overview = None

    return today_briefing(current_user=current_user, db=db)


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
    _claim_manual_refresh(db, current_user.id)

    # 뉴스 재수집 없이 바로 재생성하면 DB에 이미 있는(오래된) 뉴스만 보게 되어
    # "새로고침해도 최신 이슈가 안 잡히는" 문제가 생긴다 — 이 종목만 가볍게 먼저 수집한다.
    try:
        calendar_today = now_kst().date()
        collect_for_ticker(db, ticker, since=calendar_today - timedelta(days=3), until=calendar_today, limit=8)
    except FinnhubNotConfigured:
        pass
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 강제 재생성은 계속 시도
        print(f"종목 단건 새로고침 - 뉴스 재수집 중 오류: {e}")

    try:
        return generate_daily_briefing(db, ticker, force=True, briefing_session="additional")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="브리핑 생성에 실패했습니다. 잠시 후 다시 시도해주세요.",
        ) from exc


@router.post(
    "/refresh/overview",
    response_model=MarketOverviewRefreshJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def refresh_market_overview(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """전체 시황 생성을 백그라운드에서 시작하고 즉시 작업 ID를 반환한다."""
    _claim_manual_refresh(db, current_user.id)
    with _overview_refresh_jobs_lock:
        running = next(
            (job.copy() for job in _overview_refresh_jobs.values() if job["status"] == "running"),
            None,
        )
        if running:
            return running

        job_id = str(uuid4())
        job = {"job_id": job_id, "status": "running", "error": None}
        _overview_refresh_jobs[job_id] = job

    background_tasks.add_task(_run_market_overview_refresh, job_id)
    return job


@router.get("/refresh/overview/status/{job_id}", response_model=MarketOverviewRefreshJobRead)
def market_overview_refresh_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """프론트엔드가 전체 시황 생성 완료 여부를 짧은 요청으로 확인한다."""
    del current_user
    with _overview_refresh_jobs_lock:
        job = _overview_refresh_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="새로고침 작업을 찾을 수 없습니다.")
        return job.copy()


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
    _claim_manual_refresh(db, current_user.id)

    try:
        return generate_sector_briefing(db, sector_id, force=True, briefing_session="additional")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="브리핑 생성에 실패했습니다. 잠시 후 다시 시도해주세요.",
        ) from exc


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
