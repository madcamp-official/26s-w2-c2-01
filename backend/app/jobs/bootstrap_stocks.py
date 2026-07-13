"""Startup bootstrap for reference stock data.

Docker Compose already imports the US stock universe before uvicorn starts.
This module covers the local-dev path where the app is started directly with
uvicorn and would otherwise keep only the small seed universe.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.seed.import_us_stocks import run as import_us_stocks_run
from app.seed.seed_data import run as seed_data_run

logger = logging.getLogger(__name__)


def _stock_count() -> int:
    db = SessionLocal()
    try:
        return int(db.scalar(select(func.count()).select_from(Stock)) or 0)
    finally:
        db.close()


def run_startup_stock_import_if_needed() -> None:
    if not settings.AUTO_IMPORT_US_STOCKS:
        logger.info("US stock import bootstrap skipped: disabled by config")
        return

    try:
        seed_data_run()
        count = _stock_count()
    except Exception:
        logger.exception("US stock import bootstrap skipped: database is not ready")
        return

    if count >= settings.AUTO_IMPORT_US_STOCKS_THRESHOLD:
        logger.info(
            "US stock import bootstrap skipped: %s stocks already present (threshold=%s)",
            count,
            settings.AUTO_IMPORT_US_STOCKS_THRESHOLD,
        )
        return

    logger.info(
        "US stock import bootstrap started: only %s stocks present (threshold=%s)",
        count,
        settings.AUTO_IMPORT_US_STOCKS_THRESHOLD,
    )
    try:
        import_us_stocks_run()
    except Exception:
        logger.exception("US stock import bootstrap failed")
