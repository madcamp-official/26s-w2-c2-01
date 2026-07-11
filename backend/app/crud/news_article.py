from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle


def url_exists(db: Session, url: str) -> bool:
    return db.scalar(select(NewsArticle.id).where(NewsArticle.url == url)) is not None


def create_news_article(
    db: Session,
    *,
    ticker: str,
    title: str,
    url: str,
    source: str | None,
    summary: str | None,
    published_at,
) -> NewsArticle:
    article = NewsArticle(
        ticker=ticker,
        title=title,
        url=url,
        source=source,
        summary=summary,
        published_at=published_at,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def list_recent_news_for_ticker(db: Session, ticker: str, limit: int = 10) -> list[NewsArticle]:
    stmt = (
        select(NewsArticle)
        .where(NewsArticle.ticker == ticker)
        .order_by(NewsArticle.published_at.desc().nulls_last(), NewsArticle.fetched_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def distinct_watchlist_tickers(db: Session) -> list[str]:
    from app.models.watchlist import Watchlist

    stmt = select(Watchlist.ticker).distinct().order_by(Watchlist.ticker)
    return list(db.scalars(stmt).all())
