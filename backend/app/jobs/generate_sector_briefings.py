"""
관심 섹터 전체의 브리핑을 최신 상태로 유지한다. generate_briefings.py(종목별)와
완전히 같은 구조 — generate_sector_briefing이 내부적으로 신선도를 판단하므로
매번 관심 섹터 전체를 대상으로 삼아도 안전하다.

APScheduler(app/jobs/scheduler.py)가 REFRESH_HOURS_KST 주기로 이 run()을 자동 호출한다.

사용법: python -m app.jobs.generate_sector_briefings
"""

from datetime import date

from app.crud.sector_watchlist import distinct_followed_sector_ids
from app.db.session import SessionLocal
from app.services.sector_briefing_pipeline import generate_sector_briefing


def run() -> None:
    db = SessionLocal()
    try:
        today = date.today()
        sector_ids = sorted(distinct_followed_sector_ids(db))

        if not sector_ids:
            print("관심 섹터가 없습니다.")
            return

        for sector_id in sector_ids:
            try:
                briefing = generate_sector_briefing(db, sector_id, briefing_date=today)
                print(f"[섹터 {sector_id}] 최신 상태 (model={briefing.model}, generated_at={briefing.generated_at})")
            except Exception as e:  # noqa: BLE001 - 섹터 단위로 계속 진행
                print(f"[섹터 {sector_id}] 브리핑 갱신 실패: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
