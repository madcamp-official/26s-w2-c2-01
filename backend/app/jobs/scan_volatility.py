"""CLI entry point for the two volatility scan phases.

Examples (from backend/):
    python -m app.jobs.scan_volatility daily
    python -m app.jobs.scan_volatility premarket
    python -m app.jobs.scan_volatility full
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.news_article import NewsArticle
from app.services.polygon_client import PolygonNotConfigured, fetch_daily_history_bulk
from app.services.volatility_cache import (
    DAILY_CANDIDATES_FILE,
    TODAY_RESULTS_FILE,
    cache_daily_candidates,
    cache_today_results,
    read_json,
)
from app.services.volatility_scanner import ScannerConfig, VolatilityScanner


# OTC(OOTC) 종목은 stocks 테이블의 73%(13,479/18,436)를 차지하지만 야후 파이낸스에
# 데이터가 거의 없어("possibly delisted") 스캔 시간만 잡아먹고 결과에도 안 잡힌다.
# 실제 거래 가능한 주요 거래소만 대상으로 삼는다.
SCANNABLE_EXCHANGES = ["NASDAQ", "NYSE", "NYSE American", "CBOE BZX"]


def load_universe(limit: int | None = None) -> list[str]:
    """DB에서 스캔 가능한 미국 상장 보통주 전체를 불러온다.

    ``limit``은 진단용 수동 실행에서만 사용한다. 기본 스캔은 제한 없이
    전체 종목을 사용해야 ``all`` 탭이 인기 종목 일부로 축소되지 않는다.
    """
    db = SessionLocal()
    try:
        stmt = (
            select(Stock.ticker)
            .where(Stock.exchange.in_(SCANNABLE_EXCHANGES))
            .order_by(Stock.ticker)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(db.scalars(stmt).all())
    finally:
        db.close()


def cache_matches_universe(payload: dict | None, universe_size: int) -> bool:
    """Return whether the final cache was built from the current DB universe."""
    return bool(payload and payload.get("universe_size") == universe_size)


def run_bootstrap_if_needed(scanner: VolatilityScanner) -> None:
    """Build the initial cache once after a fresh DB/import, without blocking API startup."""
    universe = load_universe()
    if not universe:
        print("Volatility bootstrap skipped: stock universe is empty", flush=True)
        return

    cached = read_json(TODAY_RESULTS_FILE)
    if cache_matches_universe(cached, len(universe)):
        print(
            f"Volatility bootstrap skipped: cache already covers {len(universe)} tickers",
            flush=True,
        )
        return

    print(f"Volatility bootstrap started for {len(universe)} tickers", flush=True)
    run_daily(scanner, universe=universe)
    run_premarket(scanner)


def run_daily(scanner: VolatilityScanner, universe: list[str] | None = None) -> dict:
    """Step 1(사전 필터링). POLYGON_API_KEY가 설정돼 있으면 Grouped Daily로 전체
    유니버스를 한 번에(호출 ~21회, 무료 티어 분당 5회 제한 준수) 받아온다 — yfinance처럼
    종목당 요청이 필요 없어 대량 유니버스에서도 Cloudflare 차단 위험이 없다.
    미설정이면 기존 yfinance 청크 다운로드로 폴백한다."""
    tickers = universe if universe is not None else load_universe()
    if len(tickers) <= 50:
        candidates = scanner.scan_daily(tickers)
        print(f"Step 1 complete (yfinance, popular universe): {len(tickers)} scanned, {len(candidates)} candidates")
        return cache_daily_candidates(candidates, universe_size=len(tickers))
    try:
        frames = fetch_daily_history_bulk(lookback_days=scanner.config.lookback_days + 1)
        ticker_set = set(tickers)
        frames = {t: f for t, f in frames.items() if t in ticker_set}
        candidates = scanner.scan_daily_from_frames(frames)
        print(f"Step 1 complete (Polygon Grouped Daily): {len(frames)}/{len(tickers)} tickers matched, {len(candidates)} candidates")
    except PolygonNotConfigured:
        print("POLYGON_API_KEY 미설정 — yfinance 청크 다운로드로 폴백합니다 (느리고 차단 위험 있음)")
        candidates = scanner.scan_daily(tickers)
        print(f"Step 1 complete (yfinance): {len(tickers)} scanned, {len(candidates)} candidates")
    payload = cache_daily_candidates(candidates, universe_size=len(tickers))
    return payload


def load_news_catalysts(tickers: list[str], lookback_hours: int = 72) -> dict[str, int]:
    """Count recently collected company-news items as a confirmed catalyst signal."""
    if not tickers:
        return {}
    since = datetime.now() - timedelta(hours=lookback_hours)
    db = SessionLocal()
    try:
        rows = db.execute(
            select(NewsArticle.ticker, func.count(NewsArticle.id))
            .where(NewsArticle.ticker.in_(tickers), NewsArticle.published_at >= since)
            .group_by(NewsArticle.ticker)
        ).all()
        return {ticker: int(count) for ticker, count in rows if ticker}
    finally:
        db.close()


def run_premarket(scanner: VolatilityScanner) -> dict:
    cached = read_json(DAILY_CANDIDATES_FILE)
    if not cached or not isinstance(cached.get("candidates"), dict):
        raise RuntimeError("No Step 1 cache. Run the 'daily' phase after market close first.")
    catalysts = load_news_catalysts(list(cached["candidates"]))
    final = scanner.scan_premarket(cached["candidates"], news_catalysts=catalysts)
    payload = cache_today_results(
        scanner.build_tabs(final),
        universe_size=cached.get("universe_size"),
        candidate_count=len(cached["candidates"]),
    )
    print(f"Step 2 complete: {len(cached['candidates'])} candidates, {len(final)} passed")
    print(json.dumps({"all": payload["all"]["tickers"], "blue_chip": payload["blue_chip"]["tickers"]}))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the US equity volatility scanner")
    parser.add_argument("phase", choices=("daily", "premarket", "full"))
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--max-workers", type=int, default=3, help="concurrent chunk downloads per batch (only affects yfinance calls: Step 2, or Step 1 fallback without POLYGON_API_KEY)")
    parser.add_argument("--pause", type=float, default=1.5)
    parser.add_argument("--blue-chip-market-cap", type=int, default=2_000_000_000)
    args = parser.parse_args()

    scanner = VolatilityScanner(
        ScannerConfig(
            daily_chunk_size=args.chunk_size,
            max_workers=args.max_workers,
            request_pause_seconds=args.pause,
            blue_chip_market_cap_usd=args.blue_chip_market_cap,
        )
    )
    if args.phase == "daily":
        run_daily(scanner)
    elif args.phase == "premarket":
        run_premarket(scanner)
    else:
        run_daily(scanner)
        run_premarket(scanner)


if __name__ == "__main__":
    main()
