from __future__ import annotations

from datetime import datetime
from unittest import TestCase

import pandas as pd

from app.services.volatility_scanner import ScannerConfig, VolatilityScanner


def passing_daily_frame() -> pd.DataFrame:
    index = pd.date_range("2026-05-01", periods=21, freq="B")
    return pd.DataFrame(
        {
            "Open": [10.0] * 21,
            "High": [11.0] * 20 + [20.0],
            "Low": [9.0] * 20 + [8.0],
            "Close": [10.0] * 20 + [20.0],
            "Volume": [100.0] * 20 + [301.0],
        },
        index=index,
    )


def premarket_frame(price: float = 22.0) -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [datetime(2026, 6, 1, 8, 28), datetime(2026, 6, 1, 8, 29)],
        tz="America/New_York",
    )
    return pd.DataFrame(
        {
            "Open": [price, price],
            "High": [price, price],
            "Low": [price, price],
            "Close": [price, price],
            "Volume": [100, 100],
        },
        index=index,
    )


class VolatilityScannerTest(TestCase):
    def test_all_four_factors_and_tabs(self) -> None:
        def download(**kwargs):
            return passing_daily_frame() if kwargs["interval"] == "1d" else premarket_frame()

        scanner = VolatilityScanner(download=download, ticker_factory=lambda _: None)
        daily = scanner.scan_daily(["test"])
        self.assertEqual(["TEST"], list(daily))
        self.assertGreater(daily["TEST"]["volume_ratio"], 3)
        self.assertGreater(daily["TEST"]["intraday_range_pct"], 15)

        final = scanner.scan_premarket(daily, market_caps={"TEST": 20_000_000_000})
        self.assertAlmostEqual(10.0, final["TEST"]["premarket_gap_pct"])
        self.assertTrue(final["TEST"]["factors"]["premarket_gap"])

        tabs = scanner.build_tabs(final)
        self.assertEqual(["TEST"], tabs["all"]["tickers"])
        self.assertEqual(["TEST"], tabs["blue_chip"]["tickers"])

    def test_gap_threshold_is_strict(self) -> None:
        scanner = VolatilityScanner(download=lambda **_: passing_daily_frame())
        daily = scanner.scan_daily(["TEST"])
        scanner._download = lambda **_: premarket_frame(price=21.0)  # exactly +5%
        self.assertEqual({}, scanner.scan_premarket(daily, market_caps={"TEST": 1}))

    def test_download_failure_does_not_stop_other_chunks(self) -> None:
        calls = 0
        sleeps: list[float] = []

        def download(**_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("simulated timeout")
            return passing_daily_frame()

        scanner = VolatilityScanner(
            ScannerConfig(daily_chunk_size=1, request_pause_seconds=0.01),
            download=download,
            sleep=sleeps.append,
        )
        result = scanner.scan_daily(["FAIL", "PASS"])
        self.assertEqual(["PASS"], list(result))
        self.assertEqual([0.01], sleeps)

    def test_nan_rows_are_skipped_without_exception(self) -> None:
        frame = passing_daily_frame()
        frame.loc[frame.index[-1], "Close"] = float("nan")
        scanner = VolatilityScanner(download=lambda **_: frame)
        self.assertEqual({}, scanner.scan_daily(["TEST"]))
