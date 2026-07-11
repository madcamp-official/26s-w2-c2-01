"""
Finnhub에서 받아온 시세·뉴스를 price_snapshots / news_articles 테이블에 저장.
UNIQUE(ticker, trade_date), UNIQUE(url) 제약을 캐시 키처럼 활용해 중복 저장을 막는다.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle
from app.models.price_snapshot import PriceSnapshot
from app.services.finnhub_client import FinnhubClient, unix_to_datetime


def save_price_snapshot(db: Session, ticker: str, quote: dict, trade_date: date) -> PriceSnapshot:
    existing = db.scalar(
        select(PriceSnapshot).where(PriceSnapshot.ticker == ticker, PriceSnapshot.trade_date == trade_date)
    )
    if existing:
        existing.close = quote.get("c")
        existing.change_pct = quote.get("dp")
        snapshot = existing
    else:
        snapshot = PriceSnapshot(
            ticker=ticker,
            trade_date=trade_date,
            close=quote.get("c"),
            change_pct=quote.get("dp"),
            volume=None,  # 무료 quote 엔드포인트는 거래량 미제공
        )
        db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def save_news_articles(db: Session, ticker: str, articles: list[dict]) -> int:
    saved = 0
    for article in articles:
        url = article.get("url")
        if not url:
            continue
        if db.scalar(select(NewsArticle).where(NewsArticle.url == url)):
            continue  # 이미 수집된 기사
        db.add(
            NewsArticle(
                ticker=ticker,
                title=article.get("headline") or "(제목 없음)",
                url=url,
                source=article.get("source"),
                summary=article.get("summary"),
                sentiment=None,
                published_at=unix_to_datetime(article["datetime"]) if article.get("datetime") else None,
            )
        )
        saved += 1
    db.commit()
    return saved


def collect_for_ticker(db: Session, client: FinnhubClient, ticker: str, news_lookback_days: int = 2) -> dict:
    """
    한 종목의 종가 스냅샷 + 최근 뉴스를 수집해 저장. 결과 개수를 요약해 반환.
    실패해도 예외를 올리지 않고 error 필드에 담아, 여러 종목을 순회할 때
    하나가 실패해도 나머지는 계속 처리되게 한다.
    """
    result = {"ticker": ticker, "price_saved": False, "news_saved": 0, "error": None}
    try:
        quote = client.get_quote(ticker)
        save_price_snapshot(db, ticker, quote, date.today())
        result["price_saved"] = True
    except Exception as e:  # noqa: BLE001 - 배치 잡이라 종목 단위로 계속 진행
        result["error"] = f"price: {e}"

    try:
        articles = client.get_company_news(
            ticker, from_date=date.today() - timedelta(days=news_lookback_days), to_date=date.today()
        )
        result["news_saved"] = save_news_articles(db, ticker, articles)
    except Exception as e:  # noqa: BLE001
        prev = result["error"]
        result["error"] = f"{prev}; news: {e}" if prev else f"news: {e}"

    return result
