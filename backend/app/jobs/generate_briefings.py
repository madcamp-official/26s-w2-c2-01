"""
관심종목 전체의 브리핑을 최신 상태로 유지한다.

generate_daily_briefing이 내부적으로 신선도(REFRESH_INTERVAL_HOURS, 기본 9시간)를
판단하므로, 이미 최신인 종목은 LLM을 다시 부르지 않고 캐시를 그대로 반환한다.
그래서 여기서는 "오늘자 브리핑이 아직 없는 종목"만 고르지 않고 관심종목 전체를
매번 대상으로 삼아도 안전하다 — 실제로 갱신이 필요한 것만 갱신된다.

APScheduler(app/jobs/scheduler.py)가 REFRESH_HOURS_KST(하루 4번, 장 스케줄 기준)
주기로 이 run()을 자동 호출한다.

사용법: python -m app.jobs.generate_briefings
"""

from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.watchlist import Watchlist
from app.services.briefing_pipeline import generate_daily_briefing


def run() -> None:
    db = SessionLocal()
    try:
        today = date.today()
        tickers = sorted({t for t in db.scalars(select(Watchlist.ticker).distinct()).all()})

        if not tickers:
            print("관심종목이 없습니다.")
            return

        for ticker in tickers:
            try:
                briefing = generate_daily_briefing(db, ticker, briefing_date=today)
                print(f"[{ticker}] 최신 상태 (model={briefing.model}, generated_at={briefing.generated_at})")
            except Exception as e:  # noqa: BLE001 - 종목 단위로 계속 진행
                print(f"[{ticker}] 브리핑 갱신 실패: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
