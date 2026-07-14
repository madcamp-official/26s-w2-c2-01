"""무료 일봉 데이터로 거래가 활발한 종목 20개를 고르는 캐시."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

import yfinance as yf

from app.services.polygon_client import (
    PolygonError,
    PolygonNotConfigured,
    fetch_grouped_daily,
    recent_calendar_days,
)
from app.services.volatility_cache import CACHE_DIR, read_json, write_json

logger = logging.getLogger(__name__)

POPULAR_STOCKS_FILE = CACHE_DIR / "popular_stocks.json"
POPULAR_CACHE_TTL = timedelta(hours=1)


def _cached_tickers(*, allow_stale: bool = False) -> list[str]:
    payload = read_json(POPULAR_STOCKS_FILE)
    if not payload:
        return []

    generated_at = payload.get("generated_at")
    tickers = payload.get("tickers")
    if not isinstance(generated_at, str) or not isinstance(tickers, list):
        return []

    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(generated_at)
    except ValueError:
        return []
    if not allow_stale and age > POPULAR_CACHE_TTL:
        return []
    return [str(t).strip().upper() for t in tickers if str(t).strip()]


def get_popular_tickers(
    limit: int = 20,
    *,
    polygon_fetch: Callable[..., list[dict]] = fetch_grouped_daily,
    screen: Callable[..., dict] = yf.screen,
) -> list[str]:
    """거래대금 상위 종목을 반환한다. 공급자 장애 시 Yahoo와 마지막 캐시 순으로 대체한다."""
    limit = max(1, min(limit, 50))
    provider_count = 50
    cached = _cached_tickers()
    if len(cached) >= limit:
        return cached[:limit]

    try:
        for trade_date in recent_calendar_days(7):
            rows = polygon_fetch(trade_date)
            if not rows:
                continue
            ranked = sorted(
                rows,
                key=lambda row: float(row.get("c") or 0) * float(row.get("v") or 0),
                reverse=True,
            )
            tickers = list(dict.fromkeys(
                str(row.get("T", "")).strip().upper()
                for row in ranked
                if str(row.get("T", "")).strip()
            ))[:provider_count]
            if tickers:
                write_json(
                    POPULAR_STOCKS_FILE,
                    {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "source": "polygon_grouped_daily",
                        "criterion": "close_times_volume_desc",
                        "trade_date": trade_date.isoformat(),
                        "tickers": tickers,
                    },
                )
                return tickers[:limit]
    except (PolygonNotConfigured, PolygonError, OSError, TypeError, ValueError) as exc:
        logger.info("Polygon 인기 종목 조회를 사용할 수 없어 Yahoo로 대체합니다: %s", exc)

    try:
        result = screen("most_actives", count=provider_count)
        quotes = result.get("quotes", []) if isinstance(result, dict) else []
        tickers: list[str] = []
        for quote in quotes:
            ticker = str(quote.get("symbol", "")).strip().upper()
            quote_type = str(quote.get("quoteType", "")).upper()
            if ticker and quote_type in ("EQUITY", "") and ticker not in tickers:
                tickers.append(ticker)
        if tickers:
            write_json(
                POPULAR_STOCKS_FILE,
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "yahoo_finance_most_actives",
                    "criterion": "dayvolume_desc",
                    "tickers": tickers,
                },
            )
            return tickers[:limit]
    except Exception as exc:  # Yahoo 장애가 종목 검색 전체를 막으면 안 된다.
        logger.warning("인기 종목 조회 실패, 마지막 캐시를 사용합니다: %s", exc)

    return _cached_tickers(allow_stale=True)[:limit]
