"""
정기 갱신 사이클. 전체 시황·관심 섹터·관심종목을 같은 시장 주기로 갱신한다.

app/main.py의 APScheduler가 REFRESH_HOURS_KST(장시작·장중·장마감·휴장 중 1회,
하루 4번)마다 run_refresh_cycle()을 자동 호출한다.

수동 실행: python -m app.jobs.scheduler
"""

import sys
from app.batch.collect_news import FinnhubNotConfigured
from app.batch.collect_news import run as collect_news_run
from app.db.session import SessionLocal
from app.jobs import generate_briefings, generate_sector_briefings
from app.services.market_overview_pipeline import generate_market_overview
from app.services.market_sessions import current_briefing_date, current_session

# Windows 콘솔(cp949) 인코딩 대비 — collect_news.py와 동일한 이유.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _collect_news(label: str) -> None:
    print(f"=== {label}: 뉴스 재수집 ===")
    try:
        collect_news_run()
    except FinnhubNotConfigured:
        print("FINNHUB_API_KEY가 없어 뉴스 재수집을 건너뜁니다. 기존 뉴스로만 브리핑을 갱신합니다.")
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 브리핑 갱신은 계속 시도
        print(f"뉴스 재수집 중 오류: {e}")


def run_refresh_cycle() -> None:
    _collect_news("정기 갱신")
    briefing_date = current_briefing_date()
    briefing_session = current_session(briefing_date)

    print("=== 정기 갱신: 전체 시황 재생성 ===")
    db = SessionLocal()
    try:
        overview = generate_market_overview(
            db, briefing_date=briefing_date, briefing_session=briefing_session
        )
        print(f"전체 시황 갱신 완료 (model={overview.model}, generated_at={overview.generated_at})")
    except Exception as e:  # noqa: BLE001 - 실패해도 종목 브리핑 갱신은 계속 진행
        print(f"전체 시황 갱신 실패: {e}")
    finally:
        db.close()

    print("=== 정기 갱신: 섹터 브리핑 재생성 ===")
    generate_sector_briefings.run()
    print("=== 정기 갱신: 관심종목 브리핑 재생성 ===")
    generate_briefings.run()
    print("=== 정기 갱신 완료 ===")


if __name__ == "__main__":
    run_refresh_cycle()
