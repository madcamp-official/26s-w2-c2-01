"""
Finnhub company-news API 얇은 클라이언트.
문서: https://finnhub.io/docs/api/company-news

FINNHUB_API_KEY가 비어 있으면 FinnhubNotConfigured를 던진다 — 호출부에서
"키 없으면 스텁으로 동작" 정책에 맞춰 처리한다.
"""

from datetime import date, datetime, timezone

import httpx

from app.core.config import settings

BASE_URL = "https://finnhub.io/api/v1"


class FinnhubNotConfigured(RuntimeError):
    pass


class FinnhubError(RuntimeError):
    pass


class FinnhubArticle:
    def __init__(
        self,
        headline: str,
        url: str,
        source: str | None,
        summary: str | None,
        ts: int | None,
        related: str | None = None,
        category: str | None = None,
    ):
        self.headline = headline
        self.url = url
        self.source = source
        self.summary = summary
        self.related = related
        self.category = category
        self.published_at = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


def fetch_company_news(ticker: str, since: date, until: date, timeout: float = 10.0) -> list[FinnhubArticle]:
    """지정한 종목의 [since, until] 구간 뉴스를 최신순으로 반환한다."""
    if not settings.FINNHUB_API_KEY:
        raise FinnhubNotConfigured("FINNHUB_API_KEY가 설정되지 않았습니다.")

    params = {
        "symbol": ticker,
        "from": since.isoformat(),
        "to": until.isoformat(),
        "token": settings.FINNHUB_API_KEY,
    }
    try:
        resp = httpx.get(f"{BASE_URL}/company-news", params=params, timeout=timeout)
    except httpx.HTTPError as exc:
        raise FinnhubError(f"Finnhub 요청 실패: {exc}") from exc

    if resp.status_code == 429:
        raise FinnhubError("Finnhub API 호출 한도를 초과했습니다 (429).")
    if resp.status_code != 200:
        raise FinnhubError(f"Finnhub API 오류: {resp.status_code} {resp.text[:200]}")

    data = resp.json()
    if not isinstance(data, list):
        raise FinnhubError(f"예상치 못한 응답 형식: {data!r:.200}")

    articles = [
        FinnhubArticle(
            headline=item.get("headline") or "",
            url=item.get("url") or "",
            source=item.get("source"),
            summary=item.get("summary"),
            ts=item.get("datetime"),
            related=item.get("related"),
            category=item.get("category"),
        )
        for item in data
        if item.get("headline") and item.get("url")
    ]
    # 최신순 정렬 (published_at 내림차순, None은 뒤로)
    articles.sort(key=lambda a: a.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return articles
