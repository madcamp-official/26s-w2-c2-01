"""
Polygon.io Grouped Daily(전체 시장 일봉 스냅샷) 클라이언트.

무료 티어에서도 미국 전체 종목의 하루치 OHLCV를 단 1번의 호출로 받을 수 있다
(실측: 2026-07-10 기준 12,398개 종목). 단, 무료 티어는 분당 5회 제한이 있어서
날짜별로 여러 번 호출해 20일 히스토리를 쌓으려면 호출 사이에 텀을 둬야 한다.

변동성 스캐너 Step 1(사전 필터링)의 yfinance 청크 다운로드를 대체하는 용도 —
yfinance는 종목당 요청이 필요해 대량 유니버스에서 Cloudflare 차단에 취약했지만,
Grouped Daily는 "하루 전체 시장"을 한 번에 주는 공식 쿼터 기반 API라 그 문제가 없다.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import date, timedelta
from typing import Callable

import httpx
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.polygon.io"
_REQUIRED_FIELDS = {"T", "o", "h", "l", "c", "v"}


class PolygonNotConfigured(RuntimeError):
    pass


class PolygonError(RuntimeError):
    pass


def fetch_grouped_daily(trade_date: date, timeout: float = 20.0) -> list[dict]:
    """지정한 거래일의 미국 전체 종목 일봉을 반환한다.
    주말/휴장일이면 빈 리스트(호출부에서 건너뛰면 됨)."""
    if not settings.POLYGON_API_KEY:
        raise PolygonNotConfigured("POLYGON_API_KEY가 설정되지 않았습니다.")

    url = f"{BASE_URL}/v2/aggs/grouped/locale/us/market/stocks/{trade_date.isoformat()}"
    try:
        resp = httpx.get(
            url, params={"apiKey": settings.POLYGON_API_KEY, "adjusted": "true"}, timeout=timeout
        )
    except httpx.HTTPError as exc:
        raise PolygonError(f"Polygon 요청 실패: {exc}") from exc

    if resp.status_code == 429:
        raise PolygonError("Polygon API 호출 한도 초과 (429) — 무료 티어는 분당 5회 제한")
    if resp.status_code != 200:
        raise PolygonError(f"Polygon API 오류: {resp.status_code} {resp.text[:200]}")

    data = resp.json()
    if data.get("status") not in ("OK", "DELAYED"):
        raise PolygonError(f"예상치 못한 응답: {data!r:.200}")
    return data.get("results") or []


def recent_calendar_days(count: int, *, before: date | None = None) -> list[date]:
    """오늘(또는 before)부터 거슬러 올라가며 평일만 count개 반환한다 (주말 제외, 공휴일은
    fetch_grouped_daily가 빈 결과를 주므로 호출부에서 자연스럽게 건너뛰게 된다)."""
    anchor = before or date.today()
    days: list[date] = []
    cursor = anchor - timedelta(days=1)  # 오늘은 아직 장이 안 끝났을 수 있으니 어제부터
    while len(days) < count:
        if cursor.weekday() < 5:  # 0=월 ... 4=금
            days.append(cursor)
        cursor -= timedelta(days=1)
    return days


def fetch_daily_history_bulk(
    lookback_days: int = 21,
    *,
    max_calendar_lookback: int = 40,
    pause_seconds: float = 13.0,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, pd.DataFrame]:
    """최근 lookback_days 거래일치 Grouped Daily를 모아 종목별 시계열로 재구성한다.

    무료 티어 분당 5회 제한에 맞춰 호출 사이 pause_seconds(기본 13초, 60/5=12초보다
    여유를 둠)를 둔다. 공휴일 등으로 빈 응답이 오면 그냥 건너뛰고 더 과거 날짜로
    채운다 — 그래서 후보 날짜를 lookback_days보다 넉넉히(max_calendar_lookback) 준비한다.

    반환된 프레임은 VolatilityScanner._daily_metrics/evaluate_daily_frame이 기대하는
    Open/High/Low/Close/Volume 컬럼 그대로라 yfinance 경로와 동일한 팩터 계산을 탄다.
    """
    candidate_days = recent_calendar_days(max_calendar_lookback)
    rows_by_ticker: dict[str, list[dict]] = defaultdict(list)
    collected = 0

    for day in candidate_days:
        if collected >= lookback_days:
            break
        try:
            results = fetch_grouped_daily(day)
        except PolygonError as exc:
            logger.warning("Grouped Daily 조회 실패(%s): %s", day, exc)
            continue

        if not results:
            continue  # 주말은 이미 걸렀으니 여긴 공휴일 등 무데이터

        for row in results:
            ticker = row.get("T")
            if not ticker or not _REQUIRED_FIELDS.issubset(row):
                continue
            rows_by_ticker[ticker].append(
                {"date": day, "Open": row["o"], "High": row["h"], "Low": row["l"], "Close": row["c"], "Volume": row["v"]}
            )
        collected += 1
        logger.info("Grouped Daily %s 수집 완료 (%d/%d 거래일)", day, collected, lookback_days)
        if collected < lookback_days and pause_seconds:
            sleep(pause_seconds)

    return {
        ticker: pd.DataFrame(rows).set_index("date").sort_index()
        for ticker, rows in rows_by_ticker.items()
    }
