"""
활성 관심종목(watchlists에 등록된 종목)의 시세·뉴스를 Finnhub에서 수집해 저장.

지금은 사람이 수동으로 실행하는 스크립트지만, 이 함수(run)가 나중에
APScheduler 크론 잡이 매일 07:00 KST에 호출할 대상이 된다.

사용법: python -m app.jobs.collect_market_data
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.watchlist import Watchlist
from app.services.finnhub_client import FinnhubClient
from app.services.market_data import collect_for_ticker


def run() -> None:
    db = SessionLocal()
    try:
        tickers = sorted({t for t in db.scalars(select(Watchlist.ticker).distinct()).all()})
        if not tickers:
            print("관심 등록된 종목이 없습니다. watchlists 테이블이 비어있는지 확인하세요.")
            return

        with FinnhubClient() as client:
            for ticker in tickers:
                result = collect_for_ticker(db, client, ticker)
                status = "OK" if not result["error"] else f"FAIL ({result['error']})"
                print(f"[{ticker}] price_saved={result['price_saved']} news_saved={result['news_saved']} {status}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
