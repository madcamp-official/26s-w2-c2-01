"""
관심종목 뉴스 수집 배치.

관심종목(watchlists)에 등록된 티커를 대상으로 Finnhub company-news를 조회해
title/url/source/summary/published_at만 news_articles에 저장한다 (원문 전체는
가져오지 않음 — 토큰비용_정확도_리포트.md의 "제목+스니펫" 방침).
같은 url은 중복 저장하지 않는다 (news_articles.url UNIQUE + 사전 조회로 이중 방지).

FINNHUB_API_KEY가 비어 있으면 안내만 출력하고 정상 종료한다(스텁 동작).

사용법: python -m app.batch.collect_news [--days 3] [--limit 8]
"""

import argparse
import sys
import time
from datetime import date, timedelta

# Windows 콘솔 기본 코드페이지(cp949)는 em-dash(—) 등 일부 유니코드 문자를 인코딩하지 못해
# print()에서 UnicodeEncodeError로 죽는다. UTF-8로 강제 전환(안 되면 대체 문자로 치환).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.core.finnhub_client import FinnhubError, FinnhubNotConfigured, fetch_company_news
from app.crud.news_article import create_news_article, distinct_watchlist_tickers, url_exists
from app.crud.stock import list_stocks
from app.db.session import SessionLocal

REQUEST_INTERVAL_SEC = 1.1  # Finnhub 무료 티어(분당 호출 제한) 여유를 두기 위한 간격


def target_tickers(db) -> list[str]:
    tickers = distinct_watchlist_tickers(db)
    if tickers:
        return tickers
    # 관심종목이 아직 없으면(초기 데모) 시드된 전체 종목을 대상으로 한다.
    return [s.ticker for s in list_stocks(db)]


def collect_for_ticker(db, ticker: str, since: date, until: date, limit: int) -> tuple[int, int]:
    """(신규 저장 건수, 중복 스킵 건수) 반환."""
    articles = fetch_company_news(ticker, since, until)[:limit]
    inserted = 0
    skipped = 0
    for a in articles:
        if url_exists(db, a.url):
            skipped += 1
            continue
        create_news_article(
            db,
            ticker=ticker,
            title=a.headline,
            url=a.url,
            source=a.source,
            summary=a.summary,
            published_at=a.published_at,
        )
        inserted += 1
    return inserted, skipped


def run(days: int = 3, limit: int = 8) -> None:
    db = SessionLocal()
    try:
        tickers = target_tickers(db)
        if not tickers:
            print("대상 종목이 없습니다 (관심종목도, 시드된 종목도 없음).")
            return

        until = date.today()
        since = until - timedelta(days=days)

        total_inserted = 0
        total_skipped = 0
        total_failed = 0

        for i, ticker in enumerate(tickers):
            try:
                inserted, skipped = collect_for_ticker(db, ticker, since, until, limit)
                total_inserted += inserted
                total_skipped += skipped
                print(f"[{ticker}] 신규 {inserted}건 · 중복 {skipped}건")
            except FinnhubError as exc:
                total_failed += 1
                print(f"[{ticker}] 수집 실패: {exc}")

            if i < len(tickers) - 1:
                time.sleep(REQUEST_INTERVAL_SEC)

        print(
            f"뉴스 수집 완료 — 종목 {len(tickers)}개, 신규 {total_inserted}건, "
            f"중복 스킵 {total_skipped}건, 실패 {total_failed}건"
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="관심종목 뉴스 수집 배치")
    parser.add_argument("--days", type=int, default=3, help="최근 며칠치 뉴스를 조회할지 (기본 3일)")
    parser.add_argument("--limit", type=int, default=8, help="종목당 최대 저장 건수 (기본 8건)")
    args = parser.parse_args()

    try:
        run(days=args.days, limit=args.limit)
    except FinnhubNotConfigured:
        print(
            "FINNHUB_API_KEY가 설정되지 않아 뉴스 수집을 건너뜁니다.\n"
            "https://finnhub.io 에서 무료 API 키를 발급받아 backend/.env 의 "
            "FINNHUB_API_KEY 에 넣어주세요."
        )
        sys.exit(0)
