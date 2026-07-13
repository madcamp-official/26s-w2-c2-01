from __future__ import annotations

from datetime import datetime, timedelta
from unittest import TestCase

import pandas as pd

from app.services.volatility_scanner import ScannerConfig, VolatilityScanner


def daily_frame(close: float = 20.0) -> pd.DataFrame:
    index = pd.date_range("2026-05-01", periods=21, freq="B")
    return pd.DataFrame(
        {
            "Open": [10.0] * 21,
            "High": [11.0] * 20 + [20.0],
            "Low": [9.0] * 20 + [8.0],
            "Close": [10.0] * 20 + [close],
            "Volume": [1_000_000.0] * 20 + [3_100_000.0],
        },
        index=index,
    )


def premarket_frame(price: float = 22.0, include_history: bool = True) -> pd.DataFrame:
    rows = []
    start = datetime(2026, 6, 1, 8, 28)
    session_offsets = (-4, -3, -2, 0) if include_history else (0,)
    for offset in session_offsets:
        for minute in range(2):
            rows.append((start + timedelta(days=offset, minutes=minute), price, 100_000))
    index = pd.DatetimeIndex([row[0] for row in rows], tz="America/New_York")
    return pd.DataFrame(
        {
            "Open": [row[1] for row in rows], "High": [row[1] for row in rows],
            "Low": [row[1] for row in rows], "Close": [row[1] for row in rows],
            "Volume": [row[2] for row in rows],
        },
        index=index,
    )


class VolatilityScannerTest(TestCase):
    def make_scanner(self, download) -> VolatilityScanner:
        return VolatilityScanner(
            ScannerConfig(
                all_stock_min_dollar_volume=1_000_000,
                blue_chip_min_dollar_volume=2_000_000,
                request_pause_seconds=0,
            ),
            download=download,
            ticker_factory=lambda _: None,
        )

    def test_score_based_ranking_and_tabs(self) -> None:
        def download(**kwargs):
            return daily_frame() if kwargs["interval"] == "1d" else premarket_frame()

        scanner = self.make_scanner(download)
        daily = scanner.scan_daily(["test"])
        self.assertEqual(["TEST"], list(daily))
        self.assertGreater(daily["TEST"]["volume_spike_ratio"], 3)
        self.assertEqual("up", daily["TEST"]["bollinger_direction"])

        final = scanner.scan_premarket(
            daily,
            market_caps={"TEST": 3_000_000_000},
            news_catalysts={"TEST": 2},
        )
        item = final["TEST"]
        self.assertEqual("up", item["premarket_direction"])
        self.assertAlmostEqual(10.0, item["premarket_gap_abs_pct"])
        self.assertEqual("same_time_premarket_20d", item["premarket_volume_method"])
        self.assertTrue(item["news_catalyst_confirmed"])
        self.assertGreater(item["volatility_attention_score"], 0)
        self.assertTrue(all(0 <= score <= 100 for score in item["score_components"].values()))

        tabs = scanner.build_tabs(final)
        self.assertEqual(["TEST"], tabs["all"]["tickers"])
        self.assertEqual(["TEST"], tabs["blue_chip"]["tickers"])

    def test_negative_gap_is_kept_with_direction(self) -> None:
        scanner = self.make_scanner(lambda **kwargs: daily_frame() if kwargs["interval"] == "1d" else premarket_frame(18.0))
        daily = scanner.scan_daily(["DOWN"])
        final = scanner.scan_premarket(daily, market_caps={"DOWN": 3_000_000_000})
        self.assertEqual("down", final["DOWN"]["premarket_direction"])
        self.assertAlmostEqual(-10.0, final["DOWN"]["premarket_gap_pct"])
        self.assertAlmostEqual(10.0, final["DOWN"]["premarket_gap_abs_pct"])

    def test_missing_history_uses_explicit_fallback_not_daily_ratio(self) -> None:
        scanner = self.make_scanner(lambda **kwargs: daily_frame() if kwargs["interval"] == "1d" else premarket_frame(include_history=False))
        daily = scanner.scan_daily(["TEST"])
        final = scanner.scan_premarket(daily, market_caps={"TEST": 1})
        item = final["TEST"]
        self.assertIsNone(item["premarket_relative_volume"])
        self.assertEqual("absolute_premarket_dollar_volume_fallback", item["premarket_volume_method"])

    def test_outliers_are_capped_at_100(self) -> None:
        scanner = self.make_scanner(lambda **kwargs: daily_frame() if kwargs["interval"] == "1d" else premarket_frame(200.0))
        daily = scanner.scan_daily(["TEST"])
        item = scanner.scan_premarket(daily, market_caps={"TEST": 1})["TEST"]
        self.assertEqual(100.0, item["score_components"]["premarket_gap"])
        self.assertLessEqual(item["volatility_attention_score"], 100)

    def test_download_failure_does_not_stop_other_chunks(self) -> None:
        calls = 0

        def download(**_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("simulated timeout")
            return daily_frame()

        scanner = VolatilityScanner(
            ScannerConfig(daily_chunk_size=1, request_pause_seconds=0, all_stock_min_dollar_volume=1),
            download=download,
        )
        self.assertEqual(["PASS"], list(scanner.scan_daily(["FAIL", "PASS"])))

    def test_nan_rows_are_skipped_without_exception(self) -> None:
        frame = daily_frame()
        frame.loc[frame.index[-1], "Close"] = float("nan")
        scanner = self.make_scanner(lambda **_: frame)
        self.assertEqual({}, scanner.scan_daily(["TEST"]))
