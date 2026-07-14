"""Finnhub company-news의 종목 관련성을 가볍게 점수화한다.

외부 모델 호출 없이 제목·요약·related·출처만 사용한다. 필터를 끄면 수집기가
이 모듈을 건너뛰므로 배포 후에도 환경변수 하나로 기존 동작으로 돌아갈 수 있다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.finnhub_client import FinnhubArticle

TRUSTED_SOURCES = {
    "associated press",
    "bloomberg",
    "cnbc",
    "reuters",
    "the wall street journal",
    "wall street journal",
}

GENERIC_HEADLINE_PATTERNS = (
    "market movers",
    "premarket movers",
    "pre-market session",
    "stocks trade up",
    "stocks trade down",
    "shares are soaring",
    "shares skyrocket",
    "stocks surge",
    "stocks to watch",
)

CORPORATE_SUFFIXES = re.compile(
    r"\s+(?:INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LIMITED|LTD|PLC|COMMON STOCK)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ScoredArticle:
    article: FinnhubArticle
    score: int


def _company_aliases(ticker: str, company_names: list[str | None]) -> list[str]:
    aliases = {ticker.strip().upper()}
    for value in company_names:
        if not value:
            continue
        name = re.sub(r"\s+", " ", value.strip()).upper()
        if name:
            aliases.add(name)
            stripped = CORPORATE_SUFFIXES.sub("", name).strip()
            if len(stripped) >= 3:
                aliases.add(stripped)
    return sorted(aliases, key=len, reverse=True)


def _mentions(text: str | None, aliases: list[str]) -> bool:
    if not text:
        return False
    upper = text.upper()
    return any(
        re.search(rf"(?:^|[^A-Z0-9]){re.escape(alias)}(?:$|[^A-Z0-9])", upper)
        for alias in aliases
    )


def _related_tickers(value: str | None) -> set[str]:
    return {item.strip().upper() for item in (value or "").split(",") if item.strip()}


def score_article_relevance(
    article: FinnhubArticle,
    *,
    ticker: str,
    company_names: list[str | None],
) -> int:
    """직접 언급을 가장 높게, Finnhub 태그와 출처는 보조 신호로 계산한다."""
    aliases = _company_aliases(ticker, company_names)
    title_mentions = _mentions(article.headline, aliases)
    summary_mentions = _mentions(article.summary, aliases)

    score = 0
    if title_mentions:
        score += 6
    if summary_mentions:
        score += 3
    if ticker.upper() in _related_tickers(article.related):
        score += 2
    if (article.source or "").strip().lower() in TRUSTED_SOURCES:
        score += 1
    if any(pattern in (article.headline or "").lower() for pattern in GENERIC_HEADLINE_PATTERNS):
        score -= 3
    return score


def select_relevant_articles(
    articles: list[FinnhubArticle],
    *,
    ticker: str,
    company_names: list[str | None],
    limit: int,
    min_score: int,
    min_articles: int,
) -> list[FinnhubArticle]:
    """고득점 기사를 우선 선택하고 부족하면 상위 후보로 최소 수량만 보충한다."""
    scored = [
        ScoredArticle(
            article=article,
            score=score_article_relevance(article, ticker=ticker, company_names=company_names),
        )
        for article in articles
    ]
    scored.sort(
        key=lambda item: (item.score, item.article.published_at is not None, item.article.published_at),
        reverse=True,
    )

    selected = [item for item in scored if item.score >= min_score]
    if len(selected) < min_articles:
        selected_ids = {id(item.article) for item in selected}
        fallback = [
            item for item in scored
            if id(item.article) not in selected_ids
        ]
        needed = max(0, min(min_articles, limit) - len(selected))
        selected.extend(fallback[:needed])
    return [item.article for item in selected[:limit]]
