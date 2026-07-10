"""
오늘자 브리핑이 아직 없는 관심종목 전체에 대해 브리핑을 생성 (DB스키마.md 3-4절 쿼리 참고).

지금은 사람이 수동으로 실행하는 스크립트지만, 이 함수(run)가 나중에
APScheduler 크론 잡이 매일 07:00 KST에 호출할 대상이 된다.
LLM API가 아직 정해지지 않아 실제로는 스텁 브리핑이 생성된다
(app/services/llm/factory.py 참고).

사용법: python -m app.jobs.generate_briefings
"""

from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.briefing import DailyBriefing
from app.models.watchlist import Watchlist
from app.services.briefing_pipeline import generate_daily_briefing


def run() -> None:
    db = SessionLocal()
    try:
        today = date.today()
        already_done = select(DailyBriefing.ticker).where(DailyBriefing.briefing_date == today)
        pending_tickers = sorted(
            {
                t
                for t in db.scalars(
                    select(Watchlist.ticker).distinct().where(~Watchlist.ticker.in_(already_done))
                ).all()
            }
        )

        if not pending_tickers:
            print("오늘자 브리핑이 필요한 관심종목이 없습니다.")
            return

        for ticker in pending_tickers:
            try:
                briefing = generate_daily_briefing(db, ticker, briefing_date=today)
                print(f"[{ticker}] 브리핑 생성 완료 (model={briefing.model})")
            except Exception as e:  # noqa: BLE001 - 종목 단위로 계속 진행
                print(f"[{ticker}] 브리핑 생성 실패: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
