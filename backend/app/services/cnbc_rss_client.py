"""Small CNBC RSS client used only by the market-overview pipeline."""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

CNBC_RSS_FEEDS = (
    ("top", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html"),
)

USER_AGENT = "TrendChaser/1.0 (+https://trend-chaser.madcamp-kaist.org)"
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")
_TOP_MARKET_TERMS = (
    "market",
    "stock",
    "fed",
    "inflation",
    "econom",
    "interest rate",
    "treasury",
    "bond",
    "oil",
    "gold",
    "trade",
    "tariff",
    "earnings",
    "invest",
    "bank",
    "dollar",
    "currency",
    "shipping",
    "hormuz",
    "artificial intelligence",
    " ai ",
    "chip",
    "jobs",
    "unemployment",
    "consumer prices",
    "gdp",
)


def _plain_text(value: str | None) -> str:
    if not value:
        return ""
    return _WHITESPACE.sub(" ", html.unescape(_HTML_TAG.sub(" ", value))).strip()


def _published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_cnbc_rss(
    content: str,
    *,
    category: str,
    now: datetime,
    lookback_hours: int,
    limit: int,
) -> list[dict]:
    """Parse one feed into the same lightweight shape used by Finnhub news."""
    root = ElementTree.fromstring(content)
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=lookback_hours)
    articles: list[dict] = []

    for item in root.findall("./channel/item"):
        headline = _plain_text(item.findtext("title"))
        summary = _plain_text(item.findtext("description"))
        url = (item.findtext("link") or "").strip()
        published_at = _published_at(item.findtext("pubDate"))
        if not headline or not url or published_at is None or published_at < cutoff:
            continue
        searchable = f" {headline} {summary} ".lower()
        if category == "top" and not any(term in searchable for term in _TOP_MARKET_TERMS):
            continue
        articles.append(
            {
                "headline": headline,
                "summary": summary,
                "source": "CNBC",
                "url": url,
                "datetime": int(published_at.timestamp()),
                "category": category,
            }
        )

    articles.sort(key=lambda article: article["datetime"], reverse=True)
    return articles[:limit]


def fetch_cnbc_market_news(
    *,
    lookback_hours: int = 24,
    per_feed_limit: int = 5,
    total_limit: int = 20,
    timeout: float = 10.0,
    now: datetime | None = None,
) -> list[dict]:
    """Fetch CNBC market feeds, deduplicate them, and return newest first."""
    now = now or datetime.now(timezone.utc)
    collected: list[dict] = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=timeout) as client:
        for category, url in CNBC_RSS_FEEDS:
            try:
                response = client.get(url)
                response.raise_for_status()
                collected.extend(
                    parse_cnbc_rss(
                        response.text,
                        category=category,
                        now=now,
                        lookback_hours=lookback_hours,
                        # Parse extra candidates because the first entries in
                        # different CNBC feeds frequently point to the same URL.
                        limit=per_feed_limit * 3,
                    )
                )
            except (httpx.HTTPError, ElementTree.ParseError) as exc:
                logger.warning("CNBC RSS fetch failed for %s: %s", category, exc)

    unique: list[dict] = []
    seen_urls: set[str] = set()
    category_counts: dict[str, int] = {}
    for article in sorted(collected, key=lambda row: row["datetime"], reverse=True):
        url = article["url"]
        if url in seen_urls:
            continue
        category = article["category"]
        if category_counts.get(category, 0) >= per_feed_limit:
            continue
        seen_urls.add(url)
        unique.append(article)
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(unique) >= total_limit:
            break
    return unique
