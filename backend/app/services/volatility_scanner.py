"""Two-step US equity volatility scanner backed by yfinance.

Step 1 is intended to run after the US market closes.  It downloads daily bars
in throttled batches and applies the first three factors.  Step 2 is intended
to run during pre-market and downloads one-minute extended-hours bars only for
the candidates produced by Step 1.

The public methods return plain dictionaries so their output can be cached as
JSON or passed directly to the news/LLM pipeline.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from datetime import time as dt_time
from typing import Any, Callable, Iterable, Mapping

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScannerConfig:
    lookback_days: int = 20
    volume_multiplier: float = 3.0
    intraday_range_threshold_pct: float = 15.0
    bollinger_std_multiplier: float = 2.0
    premarket_gap_threshold_pct: float = 5.0
    daily_period: str = "3mo"
    minute_period: str = "1d"
    daily_chunk_size: int = 50
    request_pause_seconds: float = 1.5
    request_timeout_seconds: float = 20.0
    blue_chip_market_cap_usd: int = 10_000_000_000
    top_n: int = 5
    exchange_timezone: str = "America/New_York"

    def __post_init__(self) -> None:
        if self.lookback_days < 2:
            raise ValueError("lookback_days must be at least 2")
        if self.daily_chunk_size < 1 or self.top_n < 1:
            raise ValueError("daily_chunk_size and top_n must be positive")
        if self.request_pause_seconds < 0:
            raise ValueError("request_pause_seconds cannot be negative")


DownloadFn = Callable[..., pd.DataFrame]
TickerFactory = Callable[[str], Any]


class VolatilityScanner:
    """Apply the four volatility factors without failing the whole universe."""

    REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")

    def __init__(
        self,
        config: ScannerConfig | None = None,
        *,
        download: DownloadFn | None = None,
        ticker_factory: TickerFactory | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or ScannerConfig()
        self._download = download or yf.download
        self._ticker_factory = ticker_factory or yf.Ticker
        self._sleep = sleep

    @staticmethod
    def _normalise_tickers(universe: Iterable[str]) -> list[str]:
        return sorted({ticker.strip().upper() for ticker in universe if ticker and ticker.strip()})

    @staticmethod
    def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
        for start in range(0, len(values), size):
            yield values[start : start + size]

    @staticmethod
    def _finite_number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    @classmethod
    def _ticker_frame(cls, downloaded: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Handle both yfinance single-symbol and MultiIndex response shapes."""
        if downloaded is None or downloaded.empty:
            return pd.DataFrame()

        frame: pd.DataFrame
        try:
            if isinstance(downloaded.columns, pd.MultiIndex):
                level_zero = set(downloaded.columns.get_level_values(0))
                level_one = set(downloaded.columns.get_level_values(1))
                if ticker in level_zero:
                    frame = downloaded[ticker].copy()
                elif ticker in level_one:
                    frame = downloaded.xs(ticker, axis=1, level=1).copy()
                else:
                    return pd.DataFrame()
            else:
                frame = downloaded.copy()
        except (KeyError, TypeError, ValueError):
            return pd.DataFrame()

        frame.columns = [str(column).title() for column in frame.columns]
        if not set(cls.REQUIRED_COLUMNS).issubset(frame.columns):
            return pd.DataFrame()
        return frame.loc[:, list(cls.REQUIRED_COLUMNS)]

    def _daily_metrics(self, ticker: str, frame: pd.DataFrame) -> dict[str, Any] | None:
        if frame.empty or not set(self.REQUIRED_COLUMNS).issubset(frame.columns):
            return None
        numeric = frame.copy()
        for column in self.REQUIRED_COLUMNS:
            numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
        numeric = numeric.dropna(subset=list(self.REQUIRED_COLUMNS)).sort_index()

        lookback = self.config.lookback_days
        # One extra row is needed because the signal day's volume is excluded
        # from its baseline, preventing a spike from inflating its own average.
        if len(numeric) < lookback + 1:
            return None

        signal = numeric.iloc[-1]
        prior_volume = numeric["Volume"].iloc[-(lookback + 1) : -1]
        band_closes = numeric["Close"].iloc[-lookback:]

        open_price = self._finite_number(signal["Open"])
        high = self._finite_number(signal["High"])
        low = self._finite_number(signal["Low"])
        close = self._finite_number(signal["Close"])
        volume = self._finite_number(signal["Volume"])
        average_volume = self._finite_number(prior_volume.mean())
        moving_average = self._finite_number(band_closes.mean())
        standard_deviation = self._finite_number(band_closes.std())
        if None in (open_price, high, low, close, volume, average_volume, moving_average, standard_deviation):
            return None
        if open_price <= 0 or close <= 0 or average_volume <= 0:
            return None

        intraday_range_pct = ((high - low) / open_price) * 100
        upper_band = moving_average + standard_deviation * self.config.bollinger_std_multiplier
        volume_ratio = volume / average_volume

        volume_pass = volume > average_volume * self.config.volume_multiplier
        range_pass = intraday_range_pct > self.config.intraday_range_threshold_pct
        bollinger_pass = close > upper_band
        if not (volume_pass and range_pass and bollinger_pass):
            return None

        index_value = numeric.index[-1]
        signal_date = pd.Timestamp(index_value).date().isoformat()
        return {
            "ticker": ticker,
            "signal_date": signal_date,
            "previous_open": round(open_price, 6),
            "previous_high": round(high, 6),
            "previous_low": round(low, 6),
            "previous_close": round(close, 6),
            "previous_volume": int(volume),
            "average_volume_20d": round(average_volume, 2),
            "volume_ratio": round(volume_ratio, 4),
            "intraday_range_pct": round(intraday_range_pct, 4),
            "bollinger_middle_20d": round(moving_average, 6),
            "bollinger_upper_20d": round(upper_band, 6),
            "factors": {"volume_spike": True, "intraday_range": True, "bollinger_breakout": True},
        }

    def scan_daily(self, universe: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Run factors 1-3 over an entire universe in throttled batches."""
        tickers = self._normalise_tickers(universe)
        candidates: dict[str, dict[str, Any]] = {}
        chunks = list(self._chunks(tickers, self.config.daily_chunk_size))

        for chunk_index, chunk in enumerate(chunks):
            try:
                downloaded = self._download(
                    tickers=chunk,
                    period=self.config.daily_period,
                    interval="1d",
                    group_by="ticker",
                    auto_adjust=False,
                    actions=False,
                    threads=False,
                    progress=False,
                    timeout=self.config.request_timeout_seconds,
                )
            except Exception as exc:  # yfinance exposes several transport exception types
                logger.warning("Daily download failed for %s: %s", ",".join(chunk), exc)
                downloaded = pd.DataFrame()

            for ticker in chunk:
                try:
                    metrics = self._daily_metrics(ticker, self._ticker_frame(downloaded, ticker))
                    if metrics is not None:
                        candidates[ticker] = metrics
                except Exception as exc:
                    logger.warning("Skipping malformed daily data for %s: %s", ticker, exc)

            if chunk_index < len(chunks) - 1 and self.config.request_pause_seconds:
                self._sleep(self.config.request_pause_seconds)

        return candidates

    def _premarket_price(self, frame: pd.DataFrame) -> tuple[float, str] | None:
        numeric = frame.copy()
        numeric["Close"] = pd.to_numeric(numeric["Close"], errors="coerce")
        numeric = numeric.dropna(subset=["Close"]).sort_index()
        if numeric.empty or not isinstance(numeric.index, pd.DatetimeIndex):
            return None

        index = numeric.index
        try:
            if index.tz is None:
                index = index.tz_localize(self.config.exchange_timezone)
            else:
                index = index.tz_convert(self.config.exchange_timezone)
        except (TypeError, ValueError):
            return None
        numeric.index = index

        latest_session = index[-1].date()
        session_rows = numeric[index.date == latest_session]
        premarket = session_rows.between_time(dt_time(4, 0), dt_time(9, 29, 59), inclusive="both")
        if premarket.empty:
            return None
        price = self._finite_number(premarket["Close"].iloc[-1])
        if price is None or price <= 0:
            return None
        observed_at = premarket.index[-1].isoformat()
        return price, observed_at

    def _market_cap(self, ticker: str) -> int | None:
        try:
            quote = self._ticker_factory(ticker)
            fast_info = quote.fast_info
            value = getattr(fast_info, "market_cap", None)
            if value is None:
                for key in ("marketCap", "market_cap"):
                    try:
                        value = fast_info[key]
                        break
                    except (KeyError, TypeError):
                        continue
            number = self._finite_number(value)
            return int(number) if number is not None and number > 0 else None
        except Exception as exc:
            logger.warning("Market-cap lookup failed for %s: %s", ticker, exc)
            return None

    def scan_premarket(
        self,
        daily_candidates: Mapping[str, Mapping[str, Any]],
        *,
        market_caps: Mapping[str, int | float | None] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Run factor 4 only on Step 1 candidates and enrich passing symbols."""
        tickers = self._normalise_tickers(daily_candidates.keys())
        if not tickers:
            return {}
        try:
            downloaded = self._download(
                tickers=tickers,
                period=self.config.minute_period,
                interval="1m",
                prepost=True,
                group_by="ticker",
                auto_adjust=False,
                actions=False,
                threads=False,
                progress=False,
                timeout=self.config.request_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("Pre-market download failed: %s", exc)
            return {}

        results: dict[str, dict[str, Any]] = {}
        for ticker in tickers:
            try:
                daily = dict(daily_candidates[ticker])
                previous_close = self._finite_number(daily.get("previous_close"))
                price_point = self._premarket_price(self._ticker_frame(downloaded, ticker))
                if previous_close is None or previous_close <= 0 or price_point is None:
                    continue
                premarket_price, observed_at = price_point
                gap_pct = ((premarket_price - previous_close) / previous_close) * 100
                if gap_pct <= self.config.premarket_gap_threshold_pct:
                    continue

                supplied_cap = market_caps.get(ticker) if market_caps is not None else None
                cap_number = self._finite_number(supplied_cap)
                market_cap = int(cap_number) if cap_number is not None and cap_number > 0 else self._market_cap(ticker)

                # A transparent composite used only for ranking symbols that
                # have already passed all four strict thresholds.
                score = (
                    float(daily["volume_ratio"]) / self.config.volume_multiplier
                    + float(daily["intraday_range_pct"]) / self.config.intraday_range_threshold_pct
                    + previous_close / float(daily["bollinger_upper_20d"])
                    + gap_pct / self.config.premarket_gap_threshold_pct
                )
                factors = dict(daily.get("factors", {}))
                factors["premarket_gap"] = True
                results[ticker] = {
                    **daily,
                    "premarket_price": round(premarket_price, 6),
                    "premarket_observed_at": observed_at,
                    "premarket_gap_pct": round(gap_pct, 4),
                    "market_cap_usd": market_cap,
                    "volatility_score": round(score, 6),
                    "factors": factors,
                }
            except Exception as exc:
                logger.warning("Skipping malformed pre-market data for %s: %s", ticker, exc)
        return results

    def build_tabs(self, results: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        """Return the top-N all-stock and blue-chip tabs as JSON-ready dicts."""
        ranked = sorted(
            (dict(item) for item in results.values()),
            key=lambda item: (float(item.get("volatility_score", 0)), item.get("ticker", "")),
            reverse=True,
        )
        all_items = ranked[: self.config.top_n]
        blue_chip_items = [
            item
            for item in ranked
            if isinstance(item.get("market_cap_usd"), (int, float))
            and item["market_cap_usd"] >= self.config.blue_chip_market_cap_usd
        ][: self.config.top_n]

        def tab(items: list[dict[str, Any]]) -> dict[str, Any]:
            return {
                "tickers": [item["ticker"] for item in items],
                "metrics": {item["ticker"]: item for item in items},
            }

        return {
            "criteria": {
                "top_n": self.config.top_n,
                "blue_chip_market_cap_usd": self.config.blue_chip_market_cap_usd,
                "volume_multiplier": self.config.volume_multiplier,
                "intraday_range_threshold_pct": self.config.intraday_range_threshold_pct,
                "bollinger_std_multiplier": self.config.bollinger_std_multiplier,
                "premarket_gap_threshold_pct": self.config.premarket_gap_threshold_pct,
            },
            "all": tab(all_items),
            "blue_chip": tab(blue_chip_items),
        }

    def run(
        self,
        universe: Iterable[str],
        *,
        market_caps: Mapping[str, int | float | None] | None = None,
    ) -> dict[str, Any]:
        """Convenience method for manual runs; production schedules should split the two steps."""
        daily = self.scan_daily(universe)
        final = self.scan_premarket(daily, market_caps=market_caps)
        return self.build_tabs(final)
