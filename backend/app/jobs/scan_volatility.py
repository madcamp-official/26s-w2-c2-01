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
from app.services.volatility_cache import (
    DAILY_CANDIDATES_FILE,
    cache_daily_candidates,
    cache_today_results,
    read_json,
)
from app.services.volatility_scanner import ScannerConfig, VolatilityScanner


def load_universe() -> list[str]:
    db = SessionLocal()
    try:
        return list(db.scalars(select(Stock.ticker).order_by(Stock.ticker)).all())
    finally:
        db.close()


def run_daily(scanner: VolatilityScanner, universe: list[str] | None = None) -> dict:
    tickers = universe if universe is not None else load_universe()
    candidates = scanner.scan_daily(tickers)
    payload = cache_daily_candidates(candidates)
    print(f"Step 1 complete: {len(tickers)} scanned, {len(candidates)} candidates")
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
    payload = cache_today_results(scanner.build_tabs(final))
    print(f"Step 2 complete: {len(cached['candidates'])} candidates, {len(final)} passed")
    print(json.dumps({"all": payload["all"]["tickers"], "blue_chip": payload["blue_chip"]["tickers"]}))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the US equity volatility scanner")
    parser.add_argument("phase", choices=("daily", "premarket", "full"))
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--pause", type=float, default=1.5)
    parser.add_argument("--blue-chip-market-cap", type=int, default=2_000_000_000)
    args = parser.parse_args()

    scanner = VolatilityScanner(
        ScannerConfig(
            daily_chunk_size=args.chunk_size,
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
