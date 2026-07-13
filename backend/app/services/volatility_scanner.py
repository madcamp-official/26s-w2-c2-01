"""Two-step, score-based US equity volatility scanner."""

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
    bollinger_std_multiplier: float = 2.0
    daily_period: str = "3mo"
    minute_period: str = "7d"
    daily_chunk_size: int = 50
    minute_chunk_size: int = 25
    candidate_limit: int = 500
    market_cap_lookup_limit: int = 100
    request_pause_seconds: float = 1.5
    request_timeout_seconds: float = 20.0
    blue_chip_market_cap_usd: int = 2_000_000_000
    blue_chip_min_dollar_volume: int = 20_000_000
    all_stock_min_dollar_volume: int = 1_000_000
    top_n: int = 5
    minimum_historical_premarket_sessions: int = 3
    exchange_timezone: str = "America/New_York"

    # MVP heuristic weights. These are ranking weights, not a prediction model.
    gap_weight: float = 0.35
    premarket_volume_weight: float = 0.30
    news_weight: float = 0.15
    intraday_range_weight: float = 0.10
    liquidity_weight: float = 0.10

    # Winsorisation caps used to keep an outlier from dominating the score.
    gap_cap_pct: float = 15.0
    premarket_relative_volume_cap: float = 10.0
    intraday_range_cap_pct: float = 25.0
    liquidity_score_cap_usd: int = 500_000_000
    fallback_premarket_dollar_cap_usd: int = 50_000_000

    def __post_init__(self) -> None:
        if self.lookback_days < 2:
            raise ValueError("lookback_days must be at least 2")
        positive = (
            self.daily_chunk_size,
            self.minute_chunk_size,
            self.candidate_limit,
            self.market_cap_lookup_limit,
            self.top_n,
        )
        if any(value < 1 for value in positive):
            raise ValueError("chunk sizes, limits and top_n must be positive")
        if self.request_pause_seconds < 0:
            raise ValueError("request_pause_seconds cannot be negative")
        weight_sum = (
            self.gap_weight
            + self.premarket_volume_weight
            + self.news_weight
            + self.intraday_range_weight
            + self.liquidity_weight
        )
        if not math.isclose(weight_sum, 1.0):
            raise ValueError("volatility score weights must add up to 1.0")


DownloadFn = Callable[..., pd.DataFrame]
TickerFactory = Callable[[str], Any]


class VolatilityScanner:
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

    @staticmethod
    def _direction(value: float) -> str:
        if value > 0:
            return "up"
        if value < 0:
            return "down"
        return "flat"

    @staticmethod
    def _linear_score(value: float, cap: float) -> float:
        if cap <= 0:
            return 0.0
        return round(max(0.0, min(abs(value), cap)) / cap * 100, 4)

    @staticmethod
    def _log_score(value: float, floor: float, cap: float) -> float:
        if value <= floor or cap <= floor:
            return 0.0
        clipped = min(value, cap)
        return round(math.log(clipped / floor) / math.log(cap / floor) * 100, 4)

    @classmethod
    def _ticker_frame(cls, downloaded: pd.DataFrame, ticker: str) -> pd.DataFrame:
        if downloaded is None or downloaded.empty:
            return pd.DataFrame()
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
        if len(numeric) < lookback + 1:
            return None

        signal = numeric.iloc[-1]
        prior = numeric.iloc[-(lookback + 1) : -1]
        band_closes = numeric["Close"].iloc[-lookback:]
        values = [
            signal["Open"], signal["High"], signal["Low"], signal["Close"], signal["Volume"],
            prior["Volume"].mean(), band_closes.mean(), band_closes.std(),
            (prior["Close"] * prior["Volume"]).mean(),
        ]
        converted = [self._finite_number(value) for value in values]
        if any(value is None for value in converted):
            return None
        open_price, high, low, close, volume, average_volume, middle, std, average_dollar_volume = converted
        if open_price <= 0 or close <= 0 or average_volume <= 0 or average_dollar_volume <= 0:
            return None

        spread_pct = ((high - low) / open_price) * 100
        volume_ratio = volume / average_volume
        upper_band = middle + self.config.bollinger_std_multiplier * std
        lower_band = middle - self.config.bollinger_std_multiplier * std
        if close > upper_band:
            band_distance_pct = ((close - upper_band) / middle) * 100 if middle else 0.0
        elif close < lower_band:
            band_distance_pct = ((close - lower_band) / middle) * 100 if middle else 0.0
        else:
            band_distance_pct = 0.0

        # Only used to reduce a very large universe before expensive minute data.
        daily_attention_score = (
            self._linear_score(volume_ratio, 5.0) * 0.4
            + self._linear_score(spread_pct, self.config.intraday_range_cap_pct) * 0.3
            + self._linear_score(band_distance_pct, 10.0) * 0.2
            + self._log_score(
                average_dollar_volume,
                self.config.all_stock_min_dollar_volume,
                self.config.liquidity_score_cap_usd,
            ) * 0.1
        )
        return {
            "ticker": ticker,
            "signal_date": pd.Timestamp(numeric.index[-1]).date().isoformat(),
            "previous_open": round(open_price, 6),
            "previous_high": round(high, 6),
            "previous_low": round(low, 6),
            "previous_close": round(close, 6),
            "previous_volume": int(volume),
            "average_volume_20d": round(average_volume, 2),
            "volume_spike_ratio": round(volume_ratio, 4),
            "high_low_spread_pct": round(spread_pct, 4),
            "average_dollar_volume_20d": round(average_dollar_volume, 2),
            "bollinger_middle_20d": round(middle, 6),
            "bollinger_std_20d": round(std, 6),
            "bollinger_upper_20d": round(upper_band, 6),
            "bollinger_lower_20d": round(lower_band, 6),
            "bollinger_distance_pct": round(band_distance_pct, 4),
            "bollinger_distance_abs_pct": round(abs(band_distance_pct), 4),
            "bollinger_direction": self._direction(band_distance_pct),
            "daily_attention_score": round(daily_attention_score, 4),
        }

    def scan_daily(self, universe: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Calculate daily metrics and retain a bounded liquid candidate pool."""
        tickers = self._normalise_tickers(universe)
        metrics_by_ticker: dict[str, dict[str, Any]] = {}
        chunks = list(self._chunks(tickers, self.config.daily_chunk_size))
        for chunk_index, chunk in enumerate(chunks):
            try:
                downloaded = self._download(
                    tickers=chunk, period=self.config.daily_period, interval="1d",
                    group_by="ticker", auto_adjust=False, actions=False, threads=False,
                    progress=False, timeout=self.config.request_timeout_seconds,
                )
            except Exception as exc:
                logger.warning("Daily download failed for %s: %s", ",".join(chunk), exc)
                downloaded = pd.DataFrame()
            for ticker in chunk:
                try:
                    metrics = self._daily_metrics(ticker, self._ticker_frame(downloaded, ticker))
                    if metrics and metrics["average_dollar_volume_20d"] >= self.config.all_stock_min_dollar_volume:
                        metrics_by_ticker[ticker] = metrics
                except Exception as exc:
                    logger.warning("Skipping malformed daily data for %s: %s", ticker, exc)
            if chunk_index < len(chunks) - 1 and self.config.request_pause_seconds:
                self._sleep(self.config.request_pause_seconds)

        ranked = sorted(
            metrics_by_ticker.values(),
            key=lambda item: (item["daily_attention_score"], item["ticker"]),
            reverse=True,
        )[: self.config.candidate_limit]
        return {item["ticker"]: item for item in ranked}

    def _premarket_snapshot(self, frame: pd.DataFrame) -> dict[str, Any] | None:
        numeric = frame.copy()
        numeric["Close"] = pd.to_numeric(numeric["Close"], errors="coerce")
        numeric["Volume"] = pd.to_numeric(numeric["Volume"], errors="coerce").fillna(0)
        numeric = numeric.dropna(subset=["Close"]).sort_index()
        if numeric.empty or not isinstance(numeric.index, pd.DatetimeIndex):
            return None
        try:
            index = numeric.index.tz_localize(self.config.exchange_timezone) if numeric.index.tz is None else numeric.index.tz_convert(self.config.exchange_timezone)
        except (TypeError, ValueError):
            return None
        numeric.index = index
        latest_session = index[-1].date()
        current = numeric[index.date == latest_session].between_time(dt_time(4, 0), dt_time(9, 29, 59))
        if current.empty:
            return None
        observed_at = current.index[-1]
        current_volume = float(current["Volume"].sum())
        previous_totals: list[float] = []
        for session_date in sorted(set(index.date), reverse=True):
            if session_date >= latest_session:
                continue
            session = numeric[index.date == session_date].between_time(dt_time(4, 0), observed_at.time())
            if not session.empty:
                previous_totals.append(float(session["Volume"].sum()))
            if len(previous_totals) >= self.config.lookback_days:
                break
        historical_average = sum(previous_totals) / len(previous_totals) if previous_totals else None
        relative_volume = (
            current_volume / historical_average
            if historical_average and historical_average > 0 and len(previous_totals) >= self.config.minimum_historical_premarket_sessions
            else None
        )
        return {
            "price": float(current["Close"].iloc[-1]),
            "observed_at": observed_at.isoformat(),
            "volume": int(current_volume),
            "historical_average_volume": round(historical_average, 2) if historical_average else None,
            "historical_sessions": len(previous_totals),
            "relative_volume": round(relative_volume, 4) if relative_volume is not None else None,
        }

    def _market_cap(self, ticker: str) -> int | None:
        try:
            fast_info = self._ticker_factory(ticker).fast_info
            value = getattr(fast_info, "market_cap", None)
            if value is None:
                for key in ("marketCap", "market_cap"):
                    try:
                        value = fast_info[key]
                        break
                    except (KeyError, TypeError):
                        continue
            number = self._finite_number(value)
            return int(number) if number and number > 0 else None
        except Exception as exc:
            logger.warning("Market-cap lookup failed for %s: %s", ticker, exc)
            return None

    def _score(self, daily: Mapping[str, Any], snapshot: Mapping[str, Any], gap_pct: float, news_count: int) -> tuple[float, dict[str, float], str]:
        gap_score = self._linear_score(gap_pct, self.config.gap_cap_pct)
        relative_volume = snapshot.get("relative_volume")
        if relative_volume is not None:
            volume_score = self._linear_score(float(relative_volume), self.config.premarket_relative_volume_cap)
            volume_method = "same_time_premarket_20d"
        else:
            # Explicit fallback: absolute pre-market dollar volume, never daily-volume ratio.
            premarket_dollar_volume = float(snapshot["volume"]) * float(snapshot["price"])
            volume_score = self._log_score(premarket_dollar_volume, 100_000, self.config.fallback_premarket_dollar_cap_usd)
            volume_method = "absolute_premarket_dollar_volume_fallback"
        components = {
            "premarket_gap": gap_score,
            "premarket_volume": volume_score,
            "news_catalyst": 100.0 if news_count > 0 else 0.0,
            "high_low_spread": self._linear_score(float(daily["high_low_spread_pct"]), self.config.intraday_range_cap_pct),
            "dollar_liquidity": self._log_score(
                float(daily["average_dollar_volume_20d"]),
                self.config.all_stock_min_dollar_volume,
                self.config.liquidity_score_cap_usd,
            ),
        }
        score = (
            components["premarket_gap"] * self.config.gap_weight
            + components["premarket_volume"] * self.config.premarket_volume_weight
            + components["news_catalyst"] * self.config.news_weight
            + components["high_low_spread"] * self.config.intraday_range_weight
            + components["dollar_liquidity"] * self.config.liquidity_weight
        )
        return round(score, 4), components, volume_method

    def scan_premarket(
        self,
        daily_candidates: Mapping[str, Mapping[str, Any]],
        *,
        market_caps: Mapping[str, int | float | None] | None = None,
        news_catalysts: Mapping[str, int | bool] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Calculate both up/down pre-market moves and a capped 0-100 attention score."""
        tickers = self._normalise_tickers(daily_candidates.keys())
        results: dict[str, dict[str, Any]] = {}
        for chunk_index, chunk in enumerate(self._chunks(tickers, self.config.minute_chunk_size)):
            try:
                downloaded = self._download(
                    tickers=chunk, period=self.config.minute_period, interval="1m", prepost=True,
                    group_by="ticker", auto_adjust=False, actions=False, threads=False,
                    progress=False, timeout=self.config.request_timeout_seconds,
                )
            except Exception as exc:
                logger.warning("Pre-market download failed for %s: %s", ",".join(chunk), exc)
                downloaded = pd.DataFrame()
            for ticker in chunk:
                try:
                    daily = dict(daily_candidates[ticker])
                    previous_close = self._finite_number(daily.get("previous_close"))
                    snapshot = self._premarket_snapshot(self._ticker_frame(downloaded, ticker))
                    if not previous_close or previous_close <= 0 or not snapshot or snapshot["price"] <= 0:
                        continue
                    gap_pct = ((snapshot["price"] - previous_close) / previous_close) * 100
                    raw_news = news_catalysts.get(ticker, 0) if news_catalysts else 0
                    news_count = int(raw_news) if not isinstance(raw_news, bool) else int(raw_news)
                    score, components, volume_method = self._score(daily, snapshot, gap_pct, news_count)
                    results[ticker] = {
                        **daily,
                        "premarket_price": round(snapshot["price"], 6),
                        "premarket_observed_at": snapshot["observed_at"],
                        "premarket_gap_pct": round(gap_pct, 4),
                        "premarket_gap_abs_pct": round(abs(gap_pct), 4),
                        "premarket_direction": self._direction(gap_pct),
                        "premarket_volume": snapshot["volume"],
                        "premarket_average_volume_same_time": snapshot["historical_average_volume"],
                        "premarket_historical_sessions": snapshot["historical_sessions"],
                        "premarket_relative_volume": snapshot["relative_volume"],
                        "premarket_volume_method": volume_method,
                        "news_catalyst_confirmed": news_count > 0,
                        "news_catalyst_count": news_count,
                        "score_components": components,
                        "volatility_attention_score": score,
                        "market_cap_usd": None,
                    }
                except Exception as exc:
                    logger.warning("Skipping malformed pre-market data for %s: %s", ticker, exc)
            if chunk_index < math.ceil(len(tickers) / self.config.minute_chunk_size) - 1 and self.config.request_pause_seconds:
                self._sleep(self.config.request_pause_seconds)

        ranked = sorted(results.values(), key=lambda item: (item["volatility_attention_score"], item["ticker"]), reverse=True)
        for item in ranked[: self.config.market_cap_lookup_limit]:
            ticker = item["ticker"]
            supplied = market_caps.get(ticker) if market_caps else None
            cap = self._finite_number(supplied)
            item["market_cap_usd"] = int(cap) if cap and cap > 0 else self._market_cap(ticker)
        return {item["ticker"]: item for item in ranked}

    def build_tabs(self, results: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        ranked = sorted(
            (dict(item) for item in results.values()),
            key=lambda item: (float(item.get("volatility_attention_score", 0)), item.get("ticker", "")),
            reverse=True,
        )
        all_items = [item for item in ranked if item.get("average_dollar_volume_20d", 0) >= self.config.all_stock_min_dollar_volume][: self.config.top_n]
        blue_items = [
            item for item in ranked
            if isinstance(item.get("market_cap_usd"), (int, float))
            and item["market_cap_usd"] >= self.config.blue_chip_market_cap_usd
            and item.get("average_dollar_volume_20d", 0) >= self.config.blue_chip_min_dollar_volume
        ][: self.config.top_n]

        def tab(items: list[dict[str, Any]]) -> dict[str, Any]:
            return {"tickers": [item["ticker"] for item in items], "metrics": {item["ticker"]: item for item in items}}

        return {
            "score_name": "변동성 주목 점수",
            "score_disclaimer": "초기 랭킹 휴리스틱이며 미래 수익률 또는 변동 확률이 아닙니다.",
            "criteria": {
                "top_n": self.config.top_n,
                "blue_chip_market_cap_usd": self.config.blue_chip_market_cap_usd,
                "blue_chip_min_dollar_volume": self.config.blue_chip_min_dollar_volume,
                "all_stock_min_dollar_volume": self.config.all_stock_min_dollar_volume,
                "weights": {
                    "premarket_gap_abs": self.config.gap_weight,
                    "premarket_relative_volume": self.config.premarket_volume_weight,
                    "confirmed_news_catalyst": self.config.news_weight,
                    "previous_intraday_range": self.config.intraday_range_weight,
                    "dollar_liquidity": self.config.liquidity_weight,
                },
            },
            "all": tab(all_items),
            "blue_chip": tab(blue_items),
        }

    def run(
        self,
        universe: Iterable[str],
        *,
        market_caps: Mapping[str, int | float | None] | None = None,
        news_catalysts: Mapping[str, int | bool] | None = None,
    ) -> dict[str, Any]:
        daily = self.scan_daily(universe)
        final = self.scan_premarket(daily, market_caps=market_caps, news_catalysts=news_catalysts)
        return self.build_tabs(final)
