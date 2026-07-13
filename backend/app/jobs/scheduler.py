"""
정기 갱신 사이클: 뉴스 재수집 → 브리핑 재생성을 묶어서 실행한다.

app/main.py의 APScheduler가 REFRESH_HOURS_KST(장시작·장중·장마감·휴장 중 1회,
하루 4번)마다 run_refresh_cycle()을 자동 호출한다. 뉴스가 갱신된 뒤에 브리핑을 갱신해야
새 뉴스가 반영되므로 반드시 이 순서로 실행한다.

수동 실행: python -m app.jobs.scheduler
"""

import sys
from datetime import date

from app.batch.collect_news import FinnhubNotConfigured
from app.batch.collect_news import run as collect_news_run
from app.db.session import SessionLocal
from app.jobs import generate_briefings, generate_sector_briefings
from app.services.market_overview_pipeline import generate_market_overview

# Windows 콘솔(cp949) 인코딩 대비 — collect_news.py와 동일한 이유.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def run_refresh_cycle() -> None:
    print("=== 정기 갱신 시작: 뉴스 재수집 ===")
    try:
        collect_news_run()
    except FinnhubNotConfigured:
        print("FINNHUB_API_KEY가 없어 뉴스 재수집을 건너뜁니다. 기존 뉴스로만 브리핑을 갱신합니다.")
    except Exception as e:  # noqa: BLE001 - 뉴스 수집이 실패해도 브리핑 갱신은 계속 시도
        print(f"뉴스 재수집 중 오류: {e}")

    print("=== 정기 갱신: 전체 시황 재생성 ===")
    db = SessionLocal()
    try:
        overview = generate_market_overview(db, briefing_date=date.today())
        print(f"전체 시황 갱신 완료 (model={overview.model}, generated_at={overview.generated_at})")
    except Exception as e:  # noqa: BLE001 - 실패해도 종목 브리핑 갱신은 계속 진행
        print(f"전체 시황 갱신 실패: {e}")
    finally:
        db.close()

    print("=== 정기 갱신: 종목 브리핑 재생성 ===")
    generate_briefings.run()
    print("=== 정기 갱신: 섹터 브리핑 재생성 ===")
    generate_sector_briefings.run()
    print("=== 정기 갱신 완료 ===")


if __name__ == "__main__":
    run_refresh_cycle()
