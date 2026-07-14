"""
관심종목 전체의 브리핑을 최신 상태로 유지한다.

기본 실행은 generate_daily_briefing의 캐시를 따르고, 아침 7시 정기 작업은
force=True로 호출해 그날 관심종목을 정확히 한 번 최신화한다.

APScheduler(app/main.py)가 WATCHLIST_REFRESH_HOUR_KST에 하루 1회 호출한다.

사용법: python -m app.jobs.generate_briefings
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.watchlist import Watchlist
from app.services.briefing_pipeline import generate_daily_briefing


def run(*, force: bool = False) -> None:
    db = SessionLocal()
    try:
        today = datetime.now(ZoneInfo("Asia/Seoul")).date()
        tickers = sorted({t for t in db.scalars(select(Watchlist.ticker).distinct()).all()})

        if not tickers:
            print("관심종목이 없습니다.")
            return

        for ticker in tickers:
            try:
                briefing = generate_daily_briefing(db, ticker, briefing_date=today, force=force)
                print(f"[{ticker}] 최신 상태 (model={briefing.model}, generated_at={briefing.generated_at})")
            except Exception as e:  # noqa: BLE001 - 종목 단위로 계속 진행
                print(f"[{ticker}] 브리핑 갱신 실패: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
