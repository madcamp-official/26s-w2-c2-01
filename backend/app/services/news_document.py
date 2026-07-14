"""뉴스 기사를 LLM 입력 문서로 직렬화하는 공용 포맷."""

from datetime import timezone
from zoneinfo import ZoneInfo

from app.models.news_article import NewsArticle

KST = ZoneInfo("Asia/Seoul")


def format_published_at(article: NewsArticle) -> str:
    if article.published_at is None:
        return "게시 시각 미상"
    value = article.published_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def format_news_article(article: NewsArticle, *, include_ticker: bool = False) -> str:
    ticker = f"[{article.ticker}] " if include_ticker and article.ticker else ""
    return (
        f"- {ticker}{article.title} ({article.source or '출처 미상'})\n"
        f"  게시 시각: {format_published_at(article)}\n"
        f"  {article.summary or ''}\n"
        f"  URL: {article.url}"
    )
